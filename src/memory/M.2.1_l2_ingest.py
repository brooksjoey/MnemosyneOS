"""
M.2.1 — L2 Episodic Ingestion Module
PURPOSE: Persist events from L1 buffer into L2 episodic memory (event timeline).
INPUTS: events (List[Dict])
ACTIONS:
  1. Validate and timestamp each event.
  2. Store events in L2 (in-memory or persistent store).
  3. Log operation and emit metrics.
OUTPUT/STATE: L2 episodic memory updated
ROLLBACK: Remove last batch of events from L2
QUICKTEST: python -m memory.M.2.1_l2_ingest --test
"""

from typing import List, Dict, Any
import time
import logging

def ingest_l2(events: List[Dict[str, Any]]) -> int:

from .M.0.1_persistence import init_db, insert_l2_event, get_l2_events, delete_l2_event
logger = logging.getLogger("memory.l2_ingest")
init_db()

def ingest_l2(events: List[Dict[str, Any]]) -> int:
    """Persist a batch of events to persistent L2 episodic memory."""
    now = time.time()
    count = 0
    for e in events:
        e["l2_timestamp"] = now
        insert_l2_event(e)
        count += 1
    logger.info(f"[M.2.1] Ingested {count} events to L2.")
    return count


def rollback_last_batch(n: int):
    """Remove the last n events from persistent L2."""
    events = get_l2_events(n)
    for e in events:
        delete_l2_event(e["id"])


def quicktest():
    events = [
        {"event_type": "test", "content": "a", "metadata": {}},
        {"event_type": "test", "content": "b", "metadata": {}}
    ]
    n = ingest_l2(events)
    assert n == 2
    got = get_l2_events(2)
    assert len(got) == 2
    rollback_last_batch(2)
    got = get_l2_events(2)
    assert not got
    print("M.2.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
