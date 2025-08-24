import asyncio
import pathlib
from datetime import datetime
from typing import Optional
import aiofiles
import aiofiles.os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from ..utils.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

SNAPSHOT_DIR = pathlib.Path(settings.backup_dir)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

class SnapshotError(Exception):
    """Custom exception for snapshot-related errors."""
    pass

def _get_cipher_suite(*, key: bytes, iv: bytes) -> Cipher:
    """
    Creates an AES-GCM cipher suite for encryption/decryption.
    Uses the provided key and a passed IV for deterministic operations.
    """
    return Cipher(algorithms.AES(key), modes.GCM(iv))

def _derive_key(backup_key: bytes, salt: bytes, info: bytes) -> bytes:
    """Derives a secure encryption key from the master backup key using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key for AES
        salt=salt,
        info=info,
    )
    return hkdf.derive(backup_key)

async def _read_backup_key() -> bytes:
    """Asynchronously reads and validates the backup key file."""
    key_path = pathlib.Path(settings.backup_key_file)
    
    if not await aiofiles.os.path.exists(key_path):
        raise SnapshotError(f"Backup key file not found: {key_path}")
    
    try:
        async with aiofiles.open(key_path, 'rb') as key_file:
            key_data = await key_file.read()
            if len(key_data) < 32:  # Minimum key size check
                raise SnapshotError("Backup key is too short. Must be at least 32 bytes.")
            return key_data
    except IOError as e:
        raise SnapshotError(f"Failed to read backup key: {e}") from e

async def _run_async_command(command: list[str]) -> tuple[str, str]:
    """
    Robustly runs a shell command asynchronously and captures output.
    Raises SnapshotError on failure.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise SnapshotError(
                f"Command '{' '.join(command)}' failed with return code {process.returncode}.\n"
                f"Stderr: {stderr.decode().strip()}"
            )
            
        return stdout.decode().strip(), stderr.decode().strip()
        
    except (FileNotFoundError, PermissionError) as e:
        raise SnapshotError(f"Failed to execute command: {e}") from e

async def backup_now(kind: str = "full") -> str:
    """
    Creates an encrypted database snapshot.
    
    Args:
        kind: Type of backup ('full' or 'incremental' - currently only 'full' supported)
        
    Returns:
        Path to the created snapshot file.
        
    Raises:
        SnapshotError: If the backup process fails at any step.
    """
    if kind != "full":
        logger.warning("Only 'full' backup kind is currently supported. Using 'full'.")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"mnemo_snapshot_{timestamp}.enc"
    snapshot_path = SNAPSHOT_DIR / snapshot_filename
    
    # Temp files for intermediate steps
    temp_dump_path = SNAPSHOT_DIR / f"temp_dump_{timestamp}.sql"
    
    try:
        # 1. Read the backup key
        backup_key = await _read_backup_key()
        
        # 2. Create a deterministic salt and IV for this backup
        #    (Using timestamp as part of the info ensures uniqueness)
        timestamp_bytes = timestamp.encode()
        salt = b'mnemo_backup_salt'  # Can be made configurable
        info = f"backup_{timestamp}".encode()
        
        derived_key = _derive_key(backup_key, salt, info)
        iv = hashes.Hash(hashes.SHA256())
        iv.update(timestamp_bytes)
        iv = iv.finalize()[:12]  # 96-bit IV for GCM
        
        # 3. Dump the database using pg_dump
        logger.info("Starting database dump...")
        db_url = settings.database_url.replace('+psycopg', '')  # Get pure PostgreSQL URL
        dump_cmd = [
            'pg_dump', 
            '-d', db_url,
            '-F', 'c',  # Custom format
            '-f', str(temp_dump_path)
        ]
        
        await _run_async_command(dump_cmd)
        
        # 4. Encrypt the dump
        logger.info("Encrypting dump...")
        cipher = _get_cipher_suite(key=derived_key, iv=iv)
        encryptor = cipher.encryptor()
        
        async with aiofiles.open(temp_dump_path, 'rb') as infile, \
                 aiofiles.open(snapshot_path, 'wb') as outfile:
            
            # Write the IV first (needed for decryption)
            await outfile.write(iv)
            
            # Encrypt and write the data
            while chunk := await infile.read(4096):
                encrypted_chunk = encryptor.update(chunk)
                await outfile.write(encrypted_chunk)
            
            # Finalize encryption and write the tag
            encrypted_chunk = encryptor.finalize()
            await outfile.write(encrypted_chunk)
            await outfile.write(encryptor.tag)
        
        # 5. Clean up temporary file
        await aiofiles.os.remove(temp_dump_path)
        
        logger.info(f"Backup completed successfully: {snapshot_path}")
        return str(snapshot_path)
        
    except Exception as e:
        # Clean up on failure
        for temp_file in [temp_dump_path]:
            if await aiofiles.os.path.exists(temp_file):
                try:
                    await aiofiles.os.remove(temp_file)
                except IOError:
                    pass  # Don't mask the original error
                    
        if isinstance(e, SnapshotError):
            raise
        raise SnapshotError(f"Unexpected error during backup: {e}") from e

async def restore(snapshot_path: str, db_engine: AsyncEngine) -> None:
    """
    Restores the database from an encrypted snapshot.
    
    Args:
        snapshot_path: Path to the encrypted snapshot file
        db_engine: SQLAlchemy async engine for the target database
        
    Raises:
        SnapshotError: If the restore process fails
    """
    snapshot_path = pathlib.Path(snapshot_path)
    
    if not await aiofiles.os.path.exists(snapshot_path):
        raise SnapshotError(f"Snapshot file not found: {snapshot_path}")
    
    # Temp files for intermediate steps
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    temp_restore_path = SNAPSHOT_DIR / f"temp_restore_{timestamp}.sql"
    
    try:
        # 1. Read the backup key
        backup_key = await _read_backup_key()
        
        # 2. Decrypt the snapshot
        logger.info(f"Decrypting snapshot {snapshot_path}...")
        
        async with aiofiles.open(snapshot_path, 'rb') as infile:
            # Read the IV from the beginning of the file
            iv = await infile.read(12)
            # The last 16 bytes are the GCM tag
            file_size = (await aiofiles.os.stat(snapshot_path)).st_size
            await infile.seek(file_size - 16)
            tag = await infile.read(16)
            await infile.seek(12)  # Back to start of encrypted data
            
            # Derive the key using the same parameters
            salt = b'mnemo_backup_salt'
            # Extract timestamp from filename for info
            timestamp_str = snapshot_path.stem.split('_')[-1]
            info = f"backup_{timestamp_str}".encode()
            
            derived_key = _derive_key(backup_key, salt, info)
            
            cipher = _get_cipher_suite(key=derived_key, iv=iv)
            decryptor = cipher.decryptor()
            
            async with aiofiles.open(temp_restore_path, 'wb') as outfile:
                # Read and decrypt the rest of the file (excluding tag)
                remaining_size = file_size - 12 - 16
                bytes_read = 0
                
                while bytes_read < remaining_size:
                    chunk_size = min(4096, remaining_size - bytes_read)
                    encrypted_chunk = await infile.read(chunk_size)
                    
                    # Don't process the tag as encrypted data
                    if bytes_read + chunk_size > remaining_size:
                        encrypted_chunk = encrypted_chunk[:remaining_size - bytes_read]
                    
                    decrypted_chunk = decryptor.update(encrypted_chunk)
                    await outfile.write(decrypted_chunk)
                    bytes_read += len(encrypted_chunk)
                
                # Verify the tag
                decryptor.finalize_with_tag(tag)
        
        # 3. Restore the database
        logger.info("Restoring database...")
        
        # First, terminate all connections to the target database
        async with db_engine.connect() as conn:
            await conn.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = current_database() AND pid <> pg_backend_pid()"
            ))
            await conn.commit()
        
        # Restore using pg_restore
        db_url = settings.database_url.replace('+psycopg', '')
        restore_cmd = [
            'pg_restore',
            '-d', db_url,
            '-c',  # Clean (drop) existing objects
            '--if-exists',
            str(temp_restore_path)
        ]
        
        await _run_async_command(restore_cmd)
        
        # 4. Clean up
        await aiofiles.os.remove(temp_restore_path)
        
        logger.info("Database restore completed successfully")
        
    except Exception as e:
        # Clean up on failure
        if await aiofiles.os.path.exists(temp_restore_path):
            try:
                await aiofiles.os.remove(temp_restore_path)
            except IOError:
                pass
                
        if isinstance(e, SnapshotError):
            raise
        raise SnapshotError(f"Unexpected error during restore: {e}") from e

async def restore_latest_if_needed(db_engine: AsyncEngine) -> None:
    """
    Restores the latest snapshot if the database is empty.
    
    Args:
        db_engine: SQLAlchemy async engine to check and restore into
    """
    try:
        async with db_engine.connect() as conn:
            result = await conn.execute(text("SELECT COUNT(1) FROM memories"))
            memory_count = result.scalar()
            
            if memory_count == 0:
                # Find latest snapshot
                snapshots = []
                async for snapshot in aiofiles.os.scandir(SNAPSHOT_DIR):
                    if snapshot.name.endswith('.enc') and snapshot.is_file():
                        snapshots.append(snapshot.path)
                
                if snapshots:
                    latest_snapshot = max(snapshots, key=lambda x: aiofiles.os.path.getctime(x))
                    logger.info(f"Database empty, restoring from latest snapshot: {latest_snapshot}")
                    await restore(latest_snapshot, db_engine)
                else:
                    logger.info("Database empty, but no snapshots found for restore")
            else:
                logger.debug("Database contains data, skipping auto-restore")
                
    except Exception as e:
        logger.error(f"Failed to check/perform auto-restore: {e}")
        # Don't raise - this is a non-critical auto-heal function
