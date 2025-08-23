src/api/routes_memory.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from .deps import auth_dep, size_limit_dep
from ..db.session import get_db
from .schemas import RememberIn, MemoryOut, RecallOut
from ..core.ingest import remember
from ..core.recall import recall
from ..llm.provider import Embeddings
from ..core.journal import append_event
from sqlalchemy import select
from ..db.models import JournalEntry

router = APIRouter(prefix="", tags=["memory"])

@router.post("/remember", response_model=MemoryOut, dependencies=[Depends(auth_dep), Depends(size_limit_dep)])
async def post_remember(body: RememberIn, db: Session = Depends(get_db)):
    m = await remember(db, body.source_id, body.content, body.metadata)
    append_event(db, "remember", {"source_id": body.source_id, "metadata": body.metadata, "id": str(m.id)}, memory_id=m.id)
    return MemoryOut(id=str(m.id), content=m.content, metadata=m.metadata)

@router.get("/recall", response_model=list[RecallOut], dependencies=[Depends(auth_dep)])
async def get_recall(query: str = Query(...), k: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    results = await recall(db, query, embedder=Embeddings(), k=k)
    return [RecallOut(id=str(r["id"]), content=r["content"], metadata=r["metadata"], score=r["score"]) for r in results]

@router.get("/provenance/{memory_id}", dependencies=[Depends(auth_dep)])
def provenance(memory_id: str, db: Session = Depends(get_db)):
    q = select(JournalEntry).where(JournalEntry.memory_id == memory_id).order_by(JournalEntry.created_at)
    out = []
    for j in db.execute(q).scalars():
        out.append({"id": str(j.id), "event_type": j.event_type, "payload": j.payload, "checksum": j.checksum, "created_at": j.created_at.isoformat()})
    return out