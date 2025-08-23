README.md
# Hippocampus (mnemosyneos)

Level‑5 reflective, self‑healing memory service with fast recall.

## Install (bare metal, Ubuntu/NUC)
```bash
./scripts/provision_ubuntu.sh
./scripts/db_setup.sh
# put a key at /etc/mnemo/backup.key (chmod 400) and env at /etc/mnemo/env
sudo -u mnemo ./scripts/venv.sh
sudo -u mnemo venv/bin/alembic upgrade head
./scripts/install_systemd.sh
sudo systemctl start mnemosyneos mnemo-worker mnemo-beat

API
    •	POST /remember {source_id, content, metadata} → idempotent on (source_id, content_hash)
    •	GET /recall?query=&k= hybrid (pgvector HNSW cosine + FTS)
    •	POST /compress {clusters: [[id]]} → summarize episodes via LLM
    •	POST /reflect → contradiction detection → belief updates
    •	POST /backup {kind} → AES‑256‑GCM encrypted snapshot
    •	POST /restore {path} → restore snapshot
    •	GET /provenance/{memory_id} → journal (append‑only, SHA‑256 verified)

Auth: Authorization: Bearer <API_KEY>

Performance targets
    •	p95 ≤ 50ms @ k=5, N≈100k with HNSW m=16, ef_construction=128.
    •	Query rescoring uses cosine distance→similarity normalization.

Self‑healing
    1.	Verify journal checksums; if mismatch, attempt restore.
    2.	Validate index presence; rebuild if missing.
    3.	Ensure FTS column + GIN index exist.

Observability
    •	/metrics (Prometheus), /healthz, /readyz
    •	Optional OTLP endpoint via OTEL_EXPORTER_OTLP_ENDPOINT.

Security
    •	API key auth, size limit, PII redaction, AES‑GCM snapshots with HKDF‑derived key.