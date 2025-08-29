"""
M.1.2 — L1 Buffer Flush Module
PURPOSE: Move events from the L1 buffer to L2 episodic memory for longer retention.
INPUTS: None (operates on L1 buffer)
ACTIONS:
  1. Retrieve all events from L1 buffer.
  2. Persist events to L2 (calls M.2.1).
  3. Clear L1 buffer after successful flush.
  4. Log operation and emit metrics.
OUTPUT/STATE: L1 buffer emptied, L2 updated
ROLLBACK: Restore events to L1 from backup if flush fails
QUICKTEST: python -m memory.M.1.2_l1_flush --test
"""

from typing import List, Dict, Any
import logging
from .M.1.1_l1_ingest import L1_BUFFER

logger = logging.getLogger("memory.l1_flush")


# Import the real L2 ingestion function
from .M.2.1_l2_ingest import ingest_l2

def flush_l1_to_l2() -> int:
    """Flush all events from L1 buffer to L2."""
    if not L1_BUFFER:
        logger.info("[M.1.2] L1 buffer empty, nothing to flush.")
        return 0
    events = L1_BUFFER.copy()
    if ingest_l2(events):
        L1_BUFFER.clear()
        logger.info(f"[M.1.2] Flushed {len(events)} events from L1 to L2.")
        return len(events)
    else:
        logger.error("[M.1.2] Failed to flush L1 buffer to L2.")
        return 0

def quicktest():
    from .M.1.1_l1_ingest import ingest_l1
    ingest_l1("test", "event1", {})
    ingest_l1("test", "event2", {})
    n = flush_l1_to_l2()
    assert n == 2
    assert not L1_BUFFER
    print("M.1.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
