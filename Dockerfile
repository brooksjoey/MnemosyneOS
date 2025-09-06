FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8208 \
    DATA_DIR=/var/lib/mnemosyneos/data \
    VECTOR_DIR=/var/lib/mnemosyneos/vectorstore \
    VECTOR_BACKEND=chroma

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user and dirs
RUN useradd -r -s /usr/sbin/nologin mnemo && \
    mkdir -p /app /var/lib/mnemosyneos /var/log/mnemosyneos && \
    chown -R mnemo:mnemo /app /var/lib/mnemosyneos /var/log/mnemosyneos

WORKDIR /app
COPY . /app

# Install service dependencies
RUN python -m pip install --upgrade pip && \
    pip install -r "MnemosyneOS/Mnemosyne - main/services/mnemo/requirements.txt"

USER mnemo
EXPOSE 8208

# Run the service (FastAPI via uvicorn)
CMD ["python", "MnemosyneOS/Mnemosyne - main/services/mnemo/main.py"]