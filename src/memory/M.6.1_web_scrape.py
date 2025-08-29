"""
M.6.1 — Web Scrape & Ingest Module
PURPOSE: Securely fetch, parse, and ingest web content into the memory stack (L1–L4) with enterprise-grade reliability.
INPUTS: url (str), selectors (optional), ingest_level (str, default 'L2'), metadata (dict)
ACTIONS:
  1. Fetch web page with robust error handling and timeouts.
  2. Parse and extract relevant content (optionally using CSS selectors).
  3. Summarize or preprocess content if needed.
  4. Ingest content into the specified memory level with full traceability.
OUTPUT/STATE: Web content stored in memory, with provenance and metadata
ROLLBACK: Remove last ingested web content (by URL or ID)
QUICKTEST: python -m memory.M.6.1_web_scrape --test
"""


import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
import logging
import time
from .M.1.1_l1_ingest import ingest_l1
from .M.2.1_l2_ingest import ingest_l2
from .M.3.2_l3_store import store_semantics
from .M.4.1_l4_archive import archive_l4
from .M.6.2_web_summarize import summarize_content
from .M.6.3_web_dedupe import is_duplicate, content_hash

logger = logging.getLogger("memory.web_scrape")


def fetch_web_content(url: str, selectors: Optional[str] = None, timeout: int = 10) -> str:
    try:
        resp = requests.get(url, timeout=timeout)
        status = resp.status_code
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        if selectors:
            elements = soup.select(selectors)
            content = "\n".join(e.get_text(strip=True) for e in elements)
        else:
            content = soup.get_text(separator="\n", strip=True)
        return content, status
    except Exception as e:
        logger.error(f"[M.6.1] Failed to fetch {url}: {e}")
        return "", None


def ingest_web_content(url: str, selectors: Optional[str] = None, ingest_level: str = "L2", metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    content, status = fetch_web_content(url, selectors)
    if not content:
        return None
    meta = metadata or {}
    meta.update({
        "source_url": url,
        "fetch_time": time.time(),
        "http_status": status,
        "content_hash": content_hash(content)
    })
    # Deduplication
    if is_duplicate(url, content):
        logger.info(f"[M.6.1] Duplicate content for {url}, skipping ingest.")
        return None
    # Summarization
    summary = summarize_content(content, method=meta.get("summarize_method", "extractive"), max_length=meta.get("summary_length", 512))
    meta["summary"] = summary
    if ingest_level == "L1":
        ingest_l1("web", summary, meta)
    elif ingest_level == "L2":
        ingest_l2([{"event_type": "web", "content": summary, "metadata": meta}])
    elif ingest_level == "L3":
        store_semantics([{"keywords": [], "source_event": {"url": url, "content": summary}, "metadata": meta}])
    elif ingest_level == "L4":
        archive_l4([{"keywords": [], "source_event": {"url": url, "content": summary}, "metadata": meta}])
    else:
        logger.error(f"[M.6.1] Unknown ingest level: {ingest_level}")
        return None
    logger.info(f"[M.6.1] Ingested content from {url} into {ingest_level}")
    return summary


def quicktest():
    url = "https://example.com"
    content = ingest_web_content(url, ingest_level="L2")
    assert content
    print("M.6.1 quicktest passed.")

if __name__ == "__main__":
    quicktest()
