"""
M.4.3 — L4 Integrity Check & Repair Module
PURPOSE: Verify and repair the integrity of L4 archival memory.
INPUTS: None
ACTIONS:
  1. Scan L4 archive for corruption or missing fields.
  2. Attempt repair or log issues.
  3. Emit diagnostics and metrics.
OUTPUT/STATE: L4 archive health status
ROLLBACK: N/A (read-only, but can be extended)
QUICKTEST: python -m memory.M.4.3_l4_integrity --test
"""

from .M.4.1_l4_archive import L4_ARCHIVE
import logging
from typing import List, Dict, Any

logger = logging.getLogger("memory.l4_integrity")

def check_l4_integrity() -> List[Dict[str, Any]]:
    """Scan L4 archive for missing or corrupt entries."""
    issues = []
    for idx, k in enumerate(L4_ARCHIVE):
        if not isinstance(k, dict) or "keywords" not in k:
            issues.append({"index": idx, "error": "Missing or corrupt entry", "entry": k})
    if issues:
        logger.warning(f"[M.4.3] Found {len(issues)} integrity issues in L4.")
    else:
        logger.info("[M.4.3] L4 archive integrity OK.")
    return issues

def quicktest():
    from .M.4.1_l4_archive import L4_ARCHIVE
    L4_ARCHIVE.append("corrupt")
    issues = check_l4_integrity()
    assert issues and issues[0]["error"] == "Missing or corrupt entry"
    L4_ARCHIVE.pop()
    print("M.4.3 quicktest passed.")

if __name__ == "__main__":
    quicktest()
