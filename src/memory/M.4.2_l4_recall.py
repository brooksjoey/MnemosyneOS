"""
M.4.2 — L4 Hybrid Recall Module
PURPOSE: Recall knowledge from L4 archive using hybrid (vector + keyword) search.
INPUTS: query (str), limit (int, default 10)
ACTIONS:
  1. Search L4 archive for items matching query (stub: keyword match).
  2. Return up to N best matches.
OUTPUT/STATE: List of recalled knowledge items
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.4.2_l4_recall --test
"""

from typing import List, Dict, Any
from .M.4.1_l4_archive import L4_ARCHIVE

def recall_l4(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Recall items from L4 archive matching the query (stub: keyword match)."""
    q = query.lower()
    matches = [k for k in L4_ARCHIVE if any(q in (kw.lower()) for kw in k.get("keywords", []))]
    return matches[:limit]

def quicktest():
    from .M.4.1_l4_archive import archive_l4, rollback_last_batch
    archive_l4([
        {"keywords": ["alpha", "beta"]},
        {"keywords": ["gamma"]},
        {"keywords": ["beta", "delta"]}
    ])
    results = recall_l4("beta", 2)
    assert len(results) == 2
    rollback_last_batch(3)
    print("M.4.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
