"""
M.6.5 — Multi-Page Web Crawler Module
PURPOSE: Crawl and ingest content from multiple linked pages (e.g., pagination, next/prev links) with depth and breadth control.
INPUTS: start_url (str), link_selector (str), content_selector (str), max_pages (int), ingest_level (str)
ACTIONS:
  1. Fetch start_url and extract content.
  2. Follow links matching link_selector up to max_pages.
  3. Ingest content from each page, deduplicating and summarizing as needed.
OUTPUT/STATE: Multi-page web content ingested into memory
ROLLBACK: Remove last batch of ingested pages
QUICKTEST: python -m memory.M.6.5_web_multipage --test
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Set
import logging
from .M.6.1_web_scrape import ingest_web_content

logger = logging.getLogger("memory.web_multipage")

def crawl_multipage(start_url: str, link_selector: str, content_selector: str, max_pages: int = 10, ingest_level: str = "L2"):
    visited: Set[str] = set()
    to_visit = [start_url]
    count = 0
    while to_visit and count < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # Ingest content
            content = "\n".join(e.get_text(strip=True) for e in soup.select(content_selector))
            if content:
                ingest_web_content(url, content_selector, ingest_level)
                count += 1
            # Find next links
            for a in soup.select(link_selector):
                href = a.get("href")
                if href and href.startswith("http") and href not in visited:
                    to_visit.append(href)
            visited.add(url)
        except Exception as e:
            logger.error(f"[M.6.5] Error crawling {url}: {e}")
    logger.info(f"[M.6.5] Crawled {count} pages starting from {start_url}")
    return count

def quicktest():
    print("M.6.5 quicktest: (requires real multipage site)")

if __name__ == "__main__":
    quicktest()
