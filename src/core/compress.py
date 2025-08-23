src/core/compress.py
from sqlalchemy.orm import Session
from ..db.models import Memory
from ..llm.provider import LLM
from ..utils.metrics import compress_counter

async def compress_clusters(db: Session, cluster_ids: list[list[str]]):
    llm = LLM()
    for cluster in cluster_ids:
        docs = []
        for mid in cluster:
            m = db.get(Memory, mid)
            if m:
                docs.append(m.content)
        if not docs:
            continue
        summary = await llm.summarize_cluster(docs)
        from .ingest import remember
        await remember(db, source_id="system:compress", content=summary,
                       metadata={"episode": True, "parents": cluster})
    compress_counter.inc()