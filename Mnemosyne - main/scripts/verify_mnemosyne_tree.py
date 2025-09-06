
#!/usr/bin/env python3
import os, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # repo root

targets = [
    ROOT / "services" / "mnemo",
    ROOT / "MNEMOSYNE_RECON_MANIFEST.csv",
    ROOT / "_orchestration_refs",
]

def main():
    ok = True
    for t in targets:
        print(f"[CHECK] {t.relative_to(ROOT)} ->", "OK" if t.exists() else "MISSING")
        if not t.exists():
            ok = False

    # Heuristics to find entrypoints
    entry_candidates = list((ROOT / "services" / "mnemo").rglob("main.py")) +                        list((ROOT / "services" / "mnemo").rglob("app.py"))
    if entry_candidates:
        print("\n[Entrypoint candidates]")
        for p in entry_candidates:
            print(" -", p.relative_to(ROOT))

    # Detect vector-store hints
    hints = ["chromadb", "faiss", "qdrant", "weaviate", "milvus", "pinecone"]
    found = set()
    for py in (ROOT / "services" / "mnemo").rglob("*.py"):
        try:
            txt = py.read_text(encoding="utf-8", errors="ignore")
            for h in hints:
                if re.search(h, txt, re.IGNORECASE):
                    found.add(h)
        except Exception:
            pass
    if found:
        print("\n[Vector store hints]:", ", ".join(sorted(found)))

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
