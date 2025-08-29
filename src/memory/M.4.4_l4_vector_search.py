"""
M.4.4 — L4 Vector Search Module
PURPOSE: Enable fast, accurate semantic recall from L4 archive using vector similarity search (FAISS backend).
INPUTS: query_embedding (List[float]), limit (int, default 10)
ACTIONS:
  1. Build or update FAISS index from L4 archive embeddings.
  2. Search for nearest neighbors to the query embedding.
  3. Return matching items with similarity scores.
OUTPUT/STATE: List of recalled knowledge items with scores
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.4.4_l4_vector_search --test
"""

from typing import List, Dict, Any
import numpy as np
import faiss
from .M.0.1_persistence import get_l4_items

VECTOR_DIM = 1536  # Adjust to match your embedding size

class L4VectorIndex:
    def __init__(self):
        self.index = faiss.IndexFlatL2(VECTOR_DIM)
        self.ids = []
        self._build_index()

    def _build_index(self):
        items = get_l4_items(10000)  # Adjust as needed
        vectors = []
        self.ids = []
        for item in items:
            emb = item.get("embedding")
            if emb and len(emb) == VECTOR_DIM:
                vectors.append(np.array(emb, dtype=np.float32))
                self.ids.append(item["id"])
        if vectors:
            arr = np.stack(vectors)
            self.index.add(arr)

    def search(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        if not self.ids:
            return []
        q = np.array([query_embedding], dtype=np.float32)
        D, I = self.index.search(q, limit)
        results = []
        items = get_l4_items(10000)
        id_to_item = {item["id"]: item for item in items}
        for idx, dist in zip(I[0], D[0]):
            if idx < len(self.ids):
                item_id = self.ids[idx]
                item = id_to_item.get(item_id)
                if item:
                    results.append({"item": item, "score": float(dist)})
        return results

# Example usage

def quicktest():
    # This is a stub; real test would require embeddings in L4
    print("M.4.4 quicktest: (requires L4 items with embeddings)")

if __name__ == "__main__":
    quicktest()
