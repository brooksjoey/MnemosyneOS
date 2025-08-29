"""
M.3.1 — L3 Semantic Extraction Module
PURPOSE: Extract knowledge or semantic information from L2 episodic events.
INPUTS: events (List[Dict])
ACTIONS:
  1. Analyze events for semantic content (stub: extract keywords).
  2. Return extracted knowledge objects.
OUTPUT/STATE: List of semantic knowledge items
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.3.1_l3_extract --test
"""

from typing import List, Dict, Any

def extract_semantics(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Stub: Extract keywords from event content."""
    out = []
    for e in events:
        content = e.get("content", "")
        # Simple keyword extraction: split by space (replace with NLP in prod)
        keywords = list(set(content.lower().split()))
        out.append({
            "source_event": e,
            "keywords": keywords,
        })
    return out

def quicktest():
    events = [
        {"event_type": "note", "content": "alpha beta gamma", "metadata": {}},
        {"event_type": "note", "content": "beta delta", "metadata": {}}
    ]
    sem = extract_semantics(events)
    assert sem[0]["keywords"] == ["alpha", "beta", "gamma"] or sem[0]["keywords"] == ["gamma", "beta", "alpha"]
    print("M.3.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
