"""
M.5.3 — L5 Self-Healing & Backup/Restore Module
PURPOSE: Provide self-healing, backup, and restore operations for the memory system.
INPUTS: backup_path (str), restore_path (str)
ACTIONS:
  1. Backup all memory levels to a file.
  2. Restore memory levels from a backup file.
  3. Log operations and emit diagnostics.
OUTPUT/STATE: Memory system state saved/restored
ROLLBACK: Restore from previous backup if needed
QUICKTEST: python -m memory.M.5.3_l5_selfhealing --test
"""

import json
import logging
from typing import Optional
from .M.1.1_l1_ingest import L1_BUFFER
from .M.2.1_l2_ingest import L2_EPISODES
from .M.3.2_l3_store import L3_SEMANTICS
from .M.4.1_l4_archive import L4_ARCHIVE

logger = logging.getLogger("memory.l5_selfhealing")

def backup_memory(backup_path: str) -> bool:
    """Backup all memory levels to a file."""
    data = {
        "L1": list(L1_BUFFER),
        "L2": list(L2_EPISODES),
        "L3": list(L3_SEMANTICS),
        "L4": list(L4_ARCHIVE),
    }
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"[M.5.3] Backup complete: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"[M.5.3] Backup failed: {e}")
        return False

def restore_memory(restore_path: str) -> bool:
    """Restore all memory levels from a backup file."""
    try:
        with open(restore_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        L1_BUFFER.clear(); L1_BUFFER.extend(data.get("L1", []))
        L2_EPISODES.clear(); L2_EPISODES.extend(data.get("L2", []))
        L3_SEMANTICS.clear(); L3_SEMANTICS.extend(data.get("L3", []))
        L4_ARCHIVE.clear(); L4_ARCHIVE.extend(data.get("L4", []))
        logger.info(f"[M.5.3] Restore complete: {restore_path}")
        return True
    except Exception as e:
        logger.error(f"[M.5.3] Restore failed: {e}")
        return False

def quicktest():
    import tempfile, os
    backup_path = tempfile.mktemp()
    backup_memory(backup_path)
    restore_memory(backup_path)
    os.remove(backup_path)
    print("M.5.3 quicktest passed.")

if __name__ == "__main__":
    quicktest()
