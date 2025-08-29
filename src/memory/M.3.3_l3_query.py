"""
M.3.3 — L3 Semantic Query Module
PURPOSE: Query semantic knowledge from L3 memory by keyword or filter.
INPUTS: keyword (str), limit (int, default 10)
ACTIONS:
  1. Search L3 for knowledge items containing the keyword.
  2. Return up to N matching items.
OUTPUT/STATE: List of matching knowledge items
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.3.3_l3_query --test
"""

from typing import List, Dict, Any
from .M.3.2_l3_store import L3_SEMANTICS

def query_semantics(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query L3 for knowledge items containing the keyword."""
    matches = [k for k in L3_SEMANTICS if keyword.lower() in (kw.lower() for kw in k.get("keywords", []))]
    return matches[:limit]

def quicktest():
    from .M.3.2_l3_store import store_semantics, rollback_last_batch
    store_semantics([
        {"keywords": ["alpha", "beta"]},
        {"keywords": ["gamma"]},
        {"keywords": ["beta", "delta"]}
    ])
    results = query_semantics("beta", 2)
    assert len(results) == 2
    rollback_last_batch(3)
    print("M.3.3 quicktest passed.")

if __name__ == "__main__":
    quicktest()
