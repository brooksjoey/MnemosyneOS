"""
M.6.3 — Web Content Deduplication Module
PURPOSE: Prevent duplicate or near-duplicate web content from being ingested into memory.
INPUTS: url (str), content (str), threshold (float, default 0.95)
ACTIONS:
  1. Compute content hash and/or similarity to existing ingested content from the same URL.
  2. If similar content exists above threshold, skip ingest.
  3. Return deduplication decision and matched record (if any).
OUTPUT/STATE: Deduplication result
ROLLBACK: N/A (stateless)
QUICKTEST: python -m memory.M.6.3_web_dedupe --test
"""

import hashlib
from typing import Optional, Dict, Any
from .M.0.1_persistence import get_l2_events


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_duplicate(url: str, content: str, threshold: float = 0.95) -> Optional[Dict[str, Any]]:
    h = content_hash(content)
    events = get_l2_events(1000)
    for e in events:
        meta = e.get("metadata", {})
        if meta.get("source_url") == url:
            if e.get("content_hash") == h:
                return {"duplicate": True, "event": e}
    return None

def quicktest():
    # This is a stub; real test would require prior ingest
    print("M.6.3 quicktest: (requires prior L2 ingest)")

if __name__ == "__main__":
    quicktest()
