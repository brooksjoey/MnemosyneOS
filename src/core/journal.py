src/core/journal.py
from sqlalchemy.orm import Session
from ..db.models import JournalEntry
from ..utils.hashing import sha256_json

def append_event(db: Session, event_type: str, payload: dict, memory_id=None):
    checksum = sha256_json(payload)
    je = JournalEntry(event_type=event_type, payload=payload, checksum=checksum, memory_id=memory_id)
    db.add(je)
    return je

def verify_checksums(db: Session) -> bool:
    from sqlalchemy import select
    ok = True
    for (payload, checksum) in db.execute(select(JournalEntry.payload, JournalEntry.checksum)):
        if sha256_json(payload) != checksum:
            ok = False
            break
    return ok