tests/test_concurrent_writers.py
import threading
from src.db.session import SessionLocal
from src.db.models import Memory

def worker(n):
    with SessionLocal() as db:
        db.add(Memory(source_id=f"s{n}", content="c", content_hash=f"h{n}", metadata={}, embedding=[0]*1536))

def test_concurrent_writers():
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    with SessionLocal() as db:
        assert db.query(Memory).count() >= 10