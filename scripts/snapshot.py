scripts/snapshot.py
import sys, subprocess, datetime, pathlib, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from src.utils.settings import settings

SNAPDIR = pathlib.Path(settings.backup_dir)
SNAPDIR.mkdir(parents=True, exist_ok=True)

def load_key() -> bytes:
    with open(settings.backup_key_file, "rb") as f:
        master = f.read().strip()
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"mnemo-snapshot")
    return hkdf.derive(master)

def dump_db() -> pathlib.Path:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    raw = SNAPDIR / f"dump-{ts}.sql"
    subprocess.check_call(["pg_dump", settings.database_url, "-f", str(raw)])
    return raw

def encrypt_file(path: pathlib.Path) -> pathlib.Path:
    key = load_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, path.read_bytes(), None)
    out = path.with_suffix(path.suffix + ".enc")
    out.write_bytes(nonce + ct)
    path.unlink(missing_ok=True)
    return out

def decrypt_file(path: pathlib.Path) -> pathlib.Path:
    key = load_key()
    aes = AESGCM(key)
    data = path.read_bytes()
    nonce, ct = data[:12], data[12:]
    pt = aes.decrypt(nonce, ct, None)
    out = path.with_suffix("")
    out.write_bytes(pt)
    return out

def restore_db(sqlfile: pathlib.Path):
    subprocess.check_call(["psql", settings.database_url, "-f", str(sqlfile)])

def main():
    if len(sys.argv) < 2:
        print("usage: snapshot.py backup|restore [arg]", file=sys.stderr); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "backup":
        dump = dump_db()
        enc = encrypt_file(dump)
        print(str(enc))
    elif cmd == "restore":
        path = pathlib.Path(sys.argv[2])
        sql = decrypt_file(path)
        restore_db(sql)
        sql.unlink(missing_ok=True)
        print("restored")
    else:
        print("unknown command", file=sys.stderr); sys.exit(1)

if __name__ == "__main__":
    main()