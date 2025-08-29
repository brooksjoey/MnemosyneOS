"""
M.5.4 — L5 API Adapter Module
PURPOSE: Expose the orchestrated memory system as a clean, modular API for external interfaces (CLI, web, voice, etc).
INPUTS: action (str), params (dict)
ACTIONS:
  1. Route API calls to the appropriate memory module (ingest, recall, diagnostics, backup, etc).
  2. Validate and sanitize inputs.
  3. Return results or errors in a standard format.
OUTPUT/STATE: API response dict
ROLLBACK: N/A (stateless adapter)
QUICKTEST: python -m memory.M.5.4_l5_api_adapter --test
"""

from typing import Dict, Any
from .M.5.1_l5_orchestrate import orchestrate_event
from .M.4.2_l4_recall import recall_l4
from .M.5.2_l5_diagnostics import sitrep
from .M.5.3_l5_selfhealing import backup_memory, restore_memory


def memory_api(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Route API calls to the appropriate memory module."""
    try:
        if action == "ingest":
            e = orchestrate_event(params["event_type"], params["content"], params.get("metadata", {}))
            return {"status": "ok", "result": e}
        elif action == "recall":
            results = recall_l4(params["query"], params.get("limit", 10))
            return {"status": "ok", "result": results}
        elif action == "sitrep":
            return {"status": "ok", "result": sitrep()}
        elif action == "backup":
            ok = backup_memory(params["backup_path"])
            return {"status": "ok" if ok else "error"}
        elif action == "restore":
            ok = restore_memory(params["restore_path"])
            return {"status": "ok" if ok else "error"}
        else:
            return {"status": "error", "error": f"Unknown action: {action}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def quicktest():
    r = memory_api("ingest", {"event_type": "note", "content": "test brilliance"})
    assert r["status"] == "ok"
    r = memory_api("recall", {"query": "brilliance"})
    assert r["status"] == "ok"
    r = memory_api("sitrep", {})
    assert r["status"] == "ok"
    print("M.5.4 quicktest passed.")

if __name__ == "__main__":
    quicktest()
