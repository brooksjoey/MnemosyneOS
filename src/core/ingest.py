src/core/ingest.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db.models import Memory
from ..utils.redaction import redact
from ..utils.hashing import stable_hash_text
from ..llm.provider import Embeddings
from ..utils.metrics import ingest_counter

async def remember(db: Session, source_id: str, content: str, metadata: dict) -> Memory:
    red = redact(content)
    chash = stable_hash_text(red + (metadata and str(sorted(metadata.items())) or ""))
    existing = db.execute(
        select(Memory).where(Memory.source_id == source_id, Memory.content_hash == chash)
    ).scalar_one_or_none()
    if existing:
        return existing
    emb = await Embeddings().embed([red])
    m = Memory(source_id=source_id, content=red, content_hash=chash, metadata=metadata or {}, embedding=emb[0])
    db.add(m)
    ingest_counter.inc()
    return m