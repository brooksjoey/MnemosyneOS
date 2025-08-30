"""
M.4.1 — L4 Archive Module
PURPOSE: Archive semantic knowledge from L3 into L4 long-term, vectorized storage.
INPUTS: knowledge_items (List[Dict])
ACTIONS:
  1. Validate and prepare each knowledge item for archival.
  2. Store in L4 (persistent vector DB).
  3. Log operation and emit metrics.
OUTPUT/STATE: L4 archive updated
ROLLBACK: Remove last batch of items from L4
QUICKTEST: python -m memory.M.4.1_l4_archive --test
"""

from typing import List, Dict, Any
import time
import logging
from .M.0.1_persistence import init_db, insert_l4_item, get_l4_items, delete_l4_item

logger = logging.getLogger("memory.l4_archive")
init_db()

def archive_l4(knowledge_items: List[Dict[str, Any]]) -> int:
    """Archive a batch of knowledge items to persistent L4."""
    now = time.time()
    count = 0
    for k in knowledge_items:
        k["l4_timestamp"] = now
        insert_l4_item(k)
        count += 1
    logger.info(f"[M.4.1] Archived {count} items to L4.")
    return count

def rollback_last_batch(n: int):
    """Remove the last n items from persistent L4."""
    items = get_l4_items(n)
    for i in items:
        delete_l4_item(i["id"])

def quicktest():
    items = [
        {"keywords": ["alpha"]},
        {"keywords": ["beta"]}
    ]
    n = archive_l4(items)
    assert n == 2
    got = get_l4_items(2)
    assert len(got) == 2
    rollback_last_batch(2)
    got = get_l4_items(2)
    assert not got
    print("M.4.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()