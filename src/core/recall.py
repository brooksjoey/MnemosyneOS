src/core/recall.py
import time
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..llm.policy import hybrid_score
from ..utils.metrics import recall_latency_ms

def _semantic(db: Session, query_vec: list[float], k: int):
    sql = text("""
      SELECT id, content, metadata, (embedding <=> :q) AS dist
      FROM memories
      ORDER BY embedding <=> :q
      LIMIT :k
    """)
    rows = db.execute(sql, {"q": query_vec, "k": k}).mappings().all()
    out = []
    for r in rows:
        # cosine distance is [0, 2]; map to similarity [0,1]
        d = float(r["dist"])
        vscore = 1.0 - min(max(d / 2.0, 0.0), 1.0)
        out.append({"id": r["id"], "content": r["content"], "metadata": r["metadata"], "vscore": vscore})
    return out

def _keyword(db: Session, query: str, k: int):
    sql = text("""
      SELECT id, content, metadata, ts_rank_cd(tsv, plainto_tsquery('english', :q)) AS ts
      FROM memories
      WHERE tsv @@ plainto_tsquery('english', :q)
      ORDER BY ts DESC
      LIMIT :k
    """)
    rows = db.execute(sql, {"q": query, "k": k}).mappings().all()
    return [{"id": r["id"], "content": r["content"], "metadata": r["metadata"], "tscore": float(r["ts"])} for r in rows]

async def recall(db: Session, query: str, embedder, k: int = 5):
    t0 = time.perf_counter()
    qvec = (await embedder.embed([query]))[0]
    sem = _semantic(db, qvec, k * 3)
    kw = _keyword(db, query, k * 3)

    by_id: dict = {}
    for r in sem:
        by_id.setdefault(r["id"], {}).update(r)
    for r in kw:
        by_id.setdefault(r["id"], {}).update(r)

    rescored = []
    for mid, r in by_id.items():
        v = float(r.get("vscore", 0.0))
        t = float(r.get("tscore", 0.0))
        rescored.append({**r, "id": mid, "score": hybrid_score(v, t)})

    rescored.sort(key=lambda x: x["score"], reverse=True)
    out = rescored[:k]
    recall_latency_ms.observe((time.perf_counter() - t0) * 1000.0)
    return out