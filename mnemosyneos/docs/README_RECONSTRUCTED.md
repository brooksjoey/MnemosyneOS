# MnemosyneOS — Reconstructed Snapshot

This folder is an automated reconstruction of the **MnemosyneOS** (AI persistent memory system) from your JB-VPS archive.
Selection rules:

- Include any directory that explicitly references `Mnemosyne` / `MnemosyneOS` (in path or file contents).
- Within those directories, include **all** files (to preserve robustness, not a minimal subset).
- Add any standalone files that scored highly for persistent-memory relevance (RAG, vector stores, embeddings, KB, env/config).
- Include nearby support files (requirements, pyproject, Dockerfile, compose).

Artifacts:
- `MNEMOSYNE_RECON_MANIFEST.csv` — file-by-file mapping (original path, selection score, reasons).
- This README.

> Tip: Start by scanning `docker-compose*`, `Dockerfile`, and any `requirements.txt` / `pyproject.toml` to rehydrate dependencies.
> Then look for modules or services named like `mnemosyne`, `memory`, `retrieval`, or `kb`, and their entrypoints (e.g., `main.py`, service `cmd` in compose).

