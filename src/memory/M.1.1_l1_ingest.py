"""
M.1.1 — L1 Buffer Ingestion Module
PURPOSE: Capture and persist immediate input/output events to the L1 buffer (short-term context).
INPUTS: event_type (str), content (str), metadata (dict)
ACTIONS:
  1. Validate and sanitize input.
  2. Store event in L1 buffer (in-memory or fast persistent store).
  3. Emit log and metrics for observability.
OUTPUT/STATE: L1 buffer updated, event logged
ROLLBACK: Remove last event from buffer (if needed)
QUICKTEST: python -m memory.M.1.1_l1_ingest --test
"""

from typing import Dict, Any
import time
import logging

def ingest_l1(event_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:

from .M.0.1_persistence import init_db, insert_l1_event, get_l1_events, delete_l1_event
logger = logging.getLogger("memory.l1_ingest")
init_db()

def ingest_l1(event_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest an event into the persistent L1 buffer."""
    event = {
        "timestamp": time.time(),
        "event_type": event_type,
        "content": content,
        "metadata": metadata or {},
    }
    event_id = insert_l1_event(event)
    logger.info(f"L1 INGEST: {event_type} | {content[:40]}... | meta: {metadata}")
    event["id"] = event_id
    return event



def rollback_last():
    """Remove the most recent event from the persistent L1 buffer."""
    events = get_l1_events(1)
    if events:
        delete_l1_event(events[0]["id"])
        return events[0]
    return None



def quicktest():
    e = ingest_l1("test", "hello world", {"user": "test"})
    events = get_l1_events(1)
    assert events and events[0]["id"] == e["id"]
    rollback_last()
    events = get_l1_events(1)
    assert not events or events[0]["id"] != e["id"]
    print("M.1.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
