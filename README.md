# MnemosyneOS

Persistent memory operating system for VPS environments and AI orchestration.
MnemosyneOS provides a unified memory layer for your server, enabling long-term storage and retrieval of semantic context for AI systems. It is designed to stand alone as a service, or integrate seamlessly into JB-VPS as a plugin/module.

## ✨ Features

- **Semantic Memory Storage:** Embed, index, and store contextual memories across namespaces.
- **Multiple Backends:** Adapters for FAISS, Chroma, Qdrant (and extensible for others).
- **Flexible Embeddings:** Use OpenAI, HuggingFace, or custom embedding providers.
- **Structured API:** FastAPI routes for /healthz, /memories, and /search.
- **Configurable Runtime:** YAML + .env support for easy deployment.
- **Pluggable into JB-VPS:** Acts as a standalone container or an internal JB-VPS service.


## 📂 Repository Structure

```
mnemosyneos/
├─ config/             # .env + static configs
├─ scripts/            # bootstrap, install/uninstall
├─ packaging/          # docker-compose, systemd unit
├─ data/               # runtime data (gitignored)
├─ logs/               # runtime logs (gitignored)
├─ services/
│  └─ mnemo/
│     ├─ main.py       # entrypoint
│     ├─ api/          # FastAPI routes
│     ├─ core/         # models, pipeline, retrieval
│     ├─ adapters/     # embeddings + vectorstores
│     ├─ infra/        # config + wiring
│     └─ utils/        # helpers
├─ plugin_spec/        # OpenAPI spec for JB-VPS plugin
├─ tests/              # pytest test suite
└─ examples/           # usage examples (curl + Python client)
```

## 🚀 Installation

### Requirements
- Python 3.10+
- Docker (optional, for containerized deployment)
- Git

### Option 1: Run with Docker

```bash
docker build -t mnemosyneos:latest .
docker run -d --name mnemo \
  --env-file config/.env.example \
  -p 8208:8208 \
  -v mnemo-data:/var/lib/mnemosyneos \
  -v mnemo-logs:/var/log/mnemosyneos \
  mnemosyneos:latest
```

Or use the included compose file:

```bash
docker compose -f packaging/docker/docker-compose.standalone.yml up -d
```

### Option 2: Systemd Service

```bash
sudo ./scripts/install.sh
sudo systemctl enable mnemosyneos
sudo systemctl start mnemosyneos
```

### Option 3: Local Dev

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./scripts/bootstrap.sh
```


## ⚙️ Configuration

- **Environment Variables:** .env file in config/
- **Static Config:** config/settings.yaml
- **Logging:** config/logging.yaml

Example `.env.example`:

```env
EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx
VECTORSTORE_BACKEND=faiss
DATA_DIR=/opt/mnemosyneos/data
```

## 🌐 API

**Base URL:** `http://localhost:8208`

### Health Check
```http
GET /healthz → {"status": "ok"}
```

### Insert Memory
```http
POST /memories
```
```json
{
  "namespace": "default",
  "text": "Mnemosyne remembers everything."
}
```

### Search Memories
```http
POST /search
```
```json
{
  "namespace": "default",
  "query": "What does Mnemosyne remember?"
}
```

## 🧪 Development & Testing

Run the test suite:

```bash
pytest tests/
```

Lint and type-check:

```bash
flake8 services/
mypy services/
```

## 📌 Roadmap

- Extend vectorstore adapters (Weaviate, Milvus, Pinecone).
- Add streaming memory ingestion.
- UI dashboard for memory inspection.
- JB-VPS plugin auto-discovery.
```
