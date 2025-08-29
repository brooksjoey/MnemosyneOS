"""
M.2.3 — L2 Episodic Prune Module
PURPOSE: Prune or rollover old events from L2 episodic memory to manage retention and storage.
INPUTS: max_events (int)
ACTIONS:
  1. If L2 exceeds max_events, remove oldest events.
  2. Log pruning operation.
OUTPUT/STATE: L2 episodic memory pruned to max_events
ROLLBACK: N/A (destructive, but can be extended)
QUICKTEST: python -m memory.M.2.3_l2_prune --test
"""

from .M.2.1_l2_ingest import L2_EPISODES
import logging

logger = logging.getLogger("memory.l2_prune")

def prune_l2(max_events: int) -> int:
    """Prune L2 to retain only the most recent max_events."""
    removed = 0
    while len(L2_EPISODES) > max_events:
        L2_EPISODES.pop(0)
        removed += 1
    if removed:
        logger.info(f"[M.2.3] Pruned {removed} events from L2.")
    return removed

def quicktest():
    from .M.2.1_l2_ingest import ingest_l2
    ingest_l2([{ "event_type": "test", "content": str(i), "metadata": {} } for i in range(10)])
    removed = prune_l2(5)
    assert removed == 5
    assert len(L2_EPISODES) == 5
    print("M.2.3 quicktest passed.")

if __name__ == "__main__":
    quicktest()
