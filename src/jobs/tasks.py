src/jobs/tasks.py
from .celery_app import app
from ..db.session import SessionLocal
from ..core.reflect import run_reflection
from ..core.compress import compress_clusters
from ..db.models import Memory
from sqlalchemy import select

def _db():
    return SessionLocal()

@app.task(name="tasks.reflect", max_retries=5, autoretry_for=(Exception,), retry_backoff=2)
def reflect():
    from anyio import run
    with _db() as db:
        run(lambda: run_reflection(db))

@app.task(name="tasks.compress", max_retries=5, autoretry_for=(Exception,), retry_backoff=2)
def compress():
    from anyio import run
    with _db() as db:
        rows = db.execute(select(Memory.id).limit(1000)).all()
        ids = [str(r[0]) for r in rows]
        clusters = [ids[i:i+5] for i in range(0, len(ids), 5)]
        run(lambda: compress_clusters(db, clusters))

@app.task(name="tasks.rebuild")
def rebuild():
    from ..core.healing import rebuild_index
    with _db() as db:
        rebuild_index(db)