"""
M.5.2 — L5 Diagnostics & SITREP Module
PURPOSE: Provide diagnostics, health checks, and SITREP reporting for all memory levels.
INPUTS: None
ACTIONS:
  1. Gather status from L1–L4 modules (buffer sizes, integrity, recent events).
  2. Format and return a SITREP summary.
OUTPUT/STATE: SITREP string/report
ROLLBACK: N/A (read-only)
QUICKTEST: python -m memory.M.5.2_l5_diagnostics --test
"""

from .M.1.1_l1_ingest import L1_BUFFER
from .M.2.1_l2_ingest import L2_EPISODES
from .M.3.2_l3_store import L3_SEMANTICS
from .M.4.1_l4_archive import L4_ARCHIVE
from .M.4.3_l4_integrity import check_l4_integrity


def sitrep() -> str:
    """Return a SITREP summary of memory system health."""
    l1 = len(L1_BUFFER)
    l2 = len(L2_EPISODES)
    l3 = len(L3_SEMANTICS)
    l4 = len(L4_ARCHIVE)
    l4_issues = check_l4_integrity()
    report = [
        f"SITREP:",
        f"  L1 buffer: {l1} events",
        f"  L2 episodic: {l2} events",
        f"  L3 semantic: {l3} items",
        f"  L4 archive: {l4} items",
        f"  L4 integrity issues: {len(l4_issues)}",
    ]
    if l4_issues:
        for issue in l4_issues:
            report.append(f"    - L4 issue at index {issue['index']}: {issue['error']}")
    return "\n".join(report)


def quicktest():
    print(sitrep())
    print("M.5.2 quicktest passed.")

if __name__ == "__main__":
    quicktest()
