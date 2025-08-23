src/core/consistency.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..db.models import Belief
from ..llm.provider import LLM
from datetime import datetime

def _mk_fact(b: Belief) -> str:
    return f"{b.subject}::{b.predicate}::{b.object} (conf={b.confidence:.2f})"

async def reflect_beliefs(db: Session):
    blfs = db.execute(select(Belief).order_by(Belief.updated_at.desc()).limit(200)).scalars().all()
    facts = [_mk_fact(b) for b in blfs]
    out = await LLM().detect_contradictions(facts)

    for u in out.get("updates", []):
        subj, pred, obj = u["subject"], u["predicate"], u["object"]
        conf = float(u.get("confidence", 0.6))
        ex = db.execute(select(Belief).where(Belief.subject == subj, Belief.predicate == pred)).scalar_one_or_none()
        if ex:
            ex.object, ex.confidence, ex.updated_at = obj, conf, datetime.utcnow()
        else:
            db.add(Belief(subject=subj, predicate=pred, object=obj, confidence=conf, source_id="reflect"))