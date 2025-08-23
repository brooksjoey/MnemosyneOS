tests/test_crash_commit.py
from src.db.session import SessionLocal
from src.db.models import Memory
import pytest

def test_crash_during_commit(monkeypatch):
    with SessionLocal() as db:
        db.add(Memory(source_id="x", content="y", content_hash="h", metadata={}, embedding=[0]*1536))
        def boom(*a, **k): raise RuntimeError("boom")
        monkeypatch.setattr(db, "commit", boom)
        with pytest.raises(RuntimeError):
            db.commit()
        db.rollback()
        assert db.query(Memory).count() == 0