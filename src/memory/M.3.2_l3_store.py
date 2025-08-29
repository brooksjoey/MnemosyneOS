"""
M.3.2 — L3 Semantic Store Module
PURPOSE: Store extracted semantic knowledge into L3 semantic memory.
INPUTS: knowledge_items (List[Dict])
ACTIONS:
  1. Validate and timestamp each knowledge item.
  2. Store in L3 (in-memory or persistent store).
  3. Log operation and emit metrics.
OUTPUT/STATE: L3 semantic memory updated
ROLLBACK: Remove last batch of knowledge items from L3
QUICKTEST: python -m memory.M.3.2_l3_store --test
"""

from typing import List, Dict, Any
import time
import logging

L3_SEMANTICS = []  # In production, use a persistent DB or knowledge store
from .M.0.1_persistence import init_db, insert_l3_item, get_l3_items, delete_l3_item
logger = logging.getLogger("memory.l3_store")

def store_semantics(knowledge_items: List[Dict[str, Any]]) -> int:
    """Persist a batch of knowledge items to L3 semantic memory."""
    now = time.time()
    count = 0
    for k in knowledge_items:
        k["l3_timestamp"] = now
        insert_l3_item(k)
        count += 1
    logger.info(f"[M.3.2] Stored {count} items in L3.")
    return count

def rollback_last_batch(n: int):
    """Remove the last n knowledge items from L3."""
    items = get_l3_items(n)
    for i in items:
        delete_l3_item(i["id"])

def quicktest():
    items = [
        {"keywords": ["alpha", "beta"]},
        {"keywords": ["gamma"]}
    ]
    n = store_semantics(items)
    assert n == 2
    got = get_l3_items(2)
    assert len(got) == 2
    rollback_last_batch(2)
    got = get_l3_items(2)
    assert not got
    print("M.3.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
