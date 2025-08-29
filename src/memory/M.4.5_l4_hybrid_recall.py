"""
M.4.5 — L4 Hybrid Recall Module
PURPOSE: Combine vector similarity and keyword search for best-in-class memory recall from L4 archive.
INPUTS: query_embedding (List[float]), query_text (str), limit (int, default 10)
ACTIONS:
  1. Perform vector search (via FAISS) and keyword search (text match) in L4.
  2. Merge and rescore results for hybrid ranking.
  3. Return top N items with scores and match type.
OUTPUT/STATE: List of recalled knowledge items with scores and match type
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.4.5_l4_hybrid_recall --test
"""

from typing import List, Dict, Any
from .M.4.4_l4_vector_search import L4VectorIndex
from .M.0.1_persistence import get_l4_items


def hybrid_recall(query_embedding: List[float], query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    # Vector search
    vindex = L4VectorIndex()
    vector_results = vindex.search(query_embedding, limit * 2)
    # Keyword search
    all_items = get_l4_items(10000)
    keyword_results = [
        {"item": item, "score": 1.0, "match": "keyword"}
        for item in all_items if query_text.lower() in " ".join(str(item.get("keywords", []))).lower()
    ]
    # Merge and rescore
    id_seen = set()
    merged = []
    for r in vector_results:
        item_id = r["item"]["id"]
        if item_id not in id_seen:
            merged.append({"item": r["item"], "score": 1.0 / (1.0 + r["score"]), "match": "vector"})
            id_seen.add(item_id)
    for r in keyword_results:
        item_id = r["item"]["id"]
        if item_id not in id_seen:
            merged.append(r)
            id_seen.add(item_id)
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:limit]


def quicktest():
    print("M.4.5 quicktest: (requires L4 items with embeddings and keywords)")

if __name__ == "__main__":
    quicktest()
