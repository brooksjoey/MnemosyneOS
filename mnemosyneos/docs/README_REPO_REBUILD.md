
# MnemosyneOS — Repository Rebuild Package

This is a **lossless reconstruction** of the MnemosyneOS (AI persistent memory system) extracted from your JB‑VPS archive.
It is **not** a minimal subset; all matched components and their support files are preserved.

## What's here

- Original directory layout under `services/mnemo` (detected root).
- High-signal files elsewhere pulled in by content relevance (RAG/embeddings/vector-store/KB) and env/config references.
- `_orchestration_refs/` contains compose/Docker/env/bootstrap files from the archive that reference Mnemosyne/Mnemo.
- `MNEMOSYNE_RECON_MANIFEST.csv` maps each file with selection scores and reasons.
- `.gitignore` tuned for Python/Node/Docker artifacts.

## Rebuild checklist (suggested)

1. **Create repo**
   ```bash
   git init
   git add .
   git commit -m "Rehydrate MnemosyneOS from JB-VPS snapshot"
   ```

2. **Dependencies**
   - If `services/mnemo/requirements.txt` or `pyproject.toml` exists, create a venv and install:
     ```bash
     python3 -m venv .venv && source .venv/bin/activate
     pip install -r services/mnemo/requirements.txt  # or: pip install -e .
     ```

3. **Environment**
   - Copy any `.env.example` to `.env` and fill secrets (vector DB URLs, API keys, storage paths).
   - Ensure data directories exist (e.g., `vectorstore/`, `chroma/`, `logs/`, `data/`).

4. **Orchestration (optional)**
   - Check `_orchestration_refs/` for `docker-compose*.yml` or Dockerfiles that reference Mnemosyne/Mnemo.
   - You can copy a compose file to project root or reference it in place:
     ```bash
     docker compose -f _orchestration_refs/path/to/compose.yml up --build
     ```

5. **Entrypoints**
   - Look for `main.py`, `app.py`, or service entry declared in compose (service `command:`).
   - If a CLI exists, try:
     ```bash
     python services/mnemo/main.py --help
     ```

6. **Smoke test**
   - Insert a trivial memory item and retrieve it back.
   - Verify vector store is created/populated (e.g., folder/file for Chroma/FAISS/Qdrant configs).

## Notes

- To audit exactly what was pulled, open `MNEMOSYNE_RECON_MANIFEST.csv`.
- If you prefer Docker-only, ensure the compose file includes the `services/mnemo` build context and env.
- Keep `_orchestration_refs/` around—it documents how this service fit into the larger VPS.

