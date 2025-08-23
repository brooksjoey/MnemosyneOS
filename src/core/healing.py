src/core/healing.py
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.vector_index import ensure_indexes
from .journal import verify_checksums
from ..utils.snapshots import restore_latest_if_needed

log = logging.getLogger(__name__)

def check_index(db: Session) -> bool:
    """Return True if expected indexes exist; avoid dimension‑dependent probes."""
    try:
        res = db.execute(
            text("SELECT to_regclass('public.idx_memories_embedding_hnsw') IS NOT NULL")
        ).scalar()
        fts = db.execute(
            text("SELECT to_regclass('public.idx_memories_tsv') IS NOT NULL")
        ).scalar()
        return bool(res) and bool(fts)
    except Exception as e:
        log.error("Index check failure", error=str(e))
        return False

def rebuild_index(db: Session):
    ensure_indexes(db.connection())

def self_heal_on_boot(db: Session):
    ok = verify_checksums(db)
    if not ok:
        log.error("Journal checksum verification failed; attempting snapshot restore")
        restore_latest_if_needed(db)
    if not check_index(db):
        log.warning("Rebuilding vector/FTS indexes")
        rebuild_index(db)