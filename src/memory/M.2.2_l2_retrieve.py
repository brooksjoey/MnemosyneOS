"""
M.2.2 — L2 Episodic Retrieval Module
PURPOSE: Retrieve recent events from L2 episodic memory (event timeline).
INPUTS: limit (int, default 10)
ACTIONS:
  1. Fetch the most recent N events from L2.
  2. Return events in reverse chronological order.
OUTPUT/STATE: List of recent events
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.2.2_l2_retrieve --test
"""

from typing import List, Dict, Any
from .M.2.1_l2_ingest import L2_EPISODES


def retrieve_l2_recent(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve the most recent N events from L2."""
    return list(reversed(L2_EPISODES[-limit:]))


def quicktest():
    from .M.2.1_l2_ingest import ingest_l2
    ingest_l2([
        {"event_type": "test", "content": f"event{i}", "metadata": {}} for i in range(5)
    ])
    recent = retrieve_l2_recent(3)
    assert len(recent) == 3
    assert recent[0]["content"] == "event4"
    assert recent[-1]["content"] == "event2"
    print("M.2.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
