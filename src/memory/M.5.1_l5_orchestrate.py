"""
M.5.1 — L5 Orchestrator Module
PURPOSE: Coordinate ingestion, flushing, extraction, storage, and recall across all memory levels (L1–L4).
INPUTS: event_type (str), content (str), metadata (dict)
ACTIONS:
  1. Ingest event to L1.
  2. Flush L1 to L2 if needed.
  3. Extract semantics from L2 and store in L3.
  4. Archive knowledge to L4.
  5. Provide recall and diagnostics interfaces.
OUTPUT/STATE: All memory levels updated and synchronized
ROLLBACK: N/A (orchestrator, delegates rollback)
QUICKTEST: python -m memory.M.5.1_l5_orchestrate --test
"""

from typing import Dict, Any, List
from .M.1.1_l1_ingest import ingest_l1, L1_BUFFER
from .M.1.2_l1_flush import flush_l1_to_l2
from .M.2.1_l2_ingest import L2_EPISODES, ingest_l2
from .M.3.1_l3_extract import extract_semantics
from .M.3.2_l3_store import store_semantics, L3_SEMANTICS
from .M.4.1_l4_archive import archive_l4, L4_ARCHIVE


def orchestrate_event(event_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest and propagate an event through all memory levels."""
    e = ingest_l1(event_type, content, metadata)
    # For demo: flush L1 immediately (in production, use thresholds)
    flush_l1_to_l2()
    sem = extract_semantics([e])
    store_semantics(sem)
    archive_l4(sem)
    return {
        "L1": list(L1_BUFFER),
        "L2": list(L2_EPISODES),
        "L3": list(L3_SEMANTICS),
        "L4": list(L4_ARCHIVE),
    }

def quicktest():
    orchestrate_event("note", "brilliant memory system", {"user": "test"})
    assert L1_BUFFER == []
    assert L2_EPISODES
    assert L3_SEMANTICS
    assert L4_ARCHIVE
    print("M.5.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
