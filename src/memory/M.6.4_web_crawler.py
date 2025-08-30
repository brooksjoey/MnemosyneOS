"""
M.6.4 — Web Crawler & Scheduler Module
PURPOSE: Periodically crawl and ingest content from a list of URLs, with scheduling and error handling.
INPUTS: urls (List[str]), interval (int, seconds), selectors (optional), ingest_level (str)
ACTIONS:
  1. For each URL, fetch and ingest content (using M.6.1).
  2. Schedule next crawl after interval.
  3. Log results and errors.
OUTPUT/STATE: Periodic ingestion of web content
ROLLBACK: N/A (stateless)
QUICKTEST: python -m memory.M.6.4_web_crawler --test
"""

import time
import threading
from typing import List, Optional
import logging
from .M.6.1_web_scrape import ingest_web_content

logger = logging.getLogger("memory.web_crawler")


def crawl_urls(urls: List[str], selectors: Optional[str] = None, ingest_level: str = "L2", interval: int = 3600):
    def crawl_once():
        for url in urls:
            try:
                ingest_web_content(url, selectors, ingest_level)
                logger.info(f"[M.6.4] Crawled and ingested: {url}")
            except Exception as e:
                logger.error(f"[M.6.4] Error crawling {url}: {e}")
    def loop():
        while True:
            crawl_once()
            time.sleep(interval)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t

def quicktest():
    print("M.6.4 quicktest: (schedules background crawl, demo only)")

if __name__ == "__main__":
    quicktest()
