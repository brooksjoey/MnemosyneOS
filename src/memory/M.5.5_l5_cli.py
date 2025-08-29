"""
M.5.5 — L5 CLI Interface Module
PURPOSE: Provide a command-line interface for interacting with the memory system via the API adapter.
INPUTS: CLI arguments (action, params)
ACTIONS:
  1. Parse CLI arguments for action and parameters.
  2. Call memory_api and print results.
OUTPUT/STATE: CLI output
ROLLBACK: N/A (stateless interface)
QUICKTEST: python -m memory.M.5.5_l5_cli --test
"""

import argparse
import json
from .M.5.4_l5_api_adapter import memory_api

def main():
    parser = argparse.ArgumentParser(description="Mnemosyne Memory CLI")
    parser.add_argument("action", choices=["ingest", "recall", "sitrep", "backup", "restore"], help="Action to perform")
    parser.add_argument("--event_type", type=str, help="Event type for ingest")
    parser.add_argument("--content", type=str, help="Content for ingest")
    parser.add_argument("--metadata", type=json.loads, default="{}", help="Metadata as JSON string")
    parser.add_argument("--query", type=str, help="Query for recall")
    parser.add_argument("--limit", type=int, default=10, help="Limit for recall")
    parser.add_argument("--backup_path", type=str, help="Path for backup file")
    parser.add_argument("--restore_path", type=str, help="Path for restore file")
    args = parser.parse_args()

    params = {}
    if args.action == "ingest":
        params = {"event_type": args.event_type, "content": args.content, "metadata": args.metadata}
    elif args.action == "recall":
        params = {"query": args.query, "limit": args.limit}
    elif args.action == "backup":
        params = {"backup_path": args.backup_path}
    elif args.action == "restore":
        params = {"restore_path": args.restore_path}
    result = memory_api(args.action, params)
    print(json.dumps(result, indent=2))

def quicktest():
    import sys
    sys.argv = ["M.5.5_l5_cli.py", "sitrep"]
    main()
    print("M.5.5 quicktest passed.")

if __name__ == "__main__":
    main()
