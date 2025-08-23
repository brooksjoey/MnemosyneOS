tests/test_index_corruption.py
from sqlalchemy import text
from src.db.session import SessionLocal
from src.core.healing import check_index, rebuild_index

def test_partial_index_corruption():
    with SessionLocal() as db:
        db.execute(text("DROP INDEX IF EXISTS idx_memories_embedding_hnsw"))
        ok = check_index(db)
        assert ok is False
        rebuild_index(db)
        assert check_index(db) is True