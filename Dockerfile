FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1     APP_HOST=0.0.0.0 APP_PORT=8208     DATA_DIR=/var/lib/mnemosyneos LOG_DIR=/var/log/mnemosyneos     VECTOR_BACKEND=chroma VECTOR_DIR=/var/lib/mnemosyneos/vectorstore

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

RUN useradd -r -s /usr/sbin/nologin mnemo &&     mkdir -p /app /var/lib/mnemosyneos /var/log/mnemosyneos &&     chown -R mnemo:mnemo /app /var/lib/mnemosyneos /var/log/mnemosyneos

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip

# If using requirements.txt, uncomment:
# COPY requirements.txt /app/requirements.txt
# RUN pip install -r /app/requirements.txt

USER mnemo
EXPOSE 8208
CMD ["python", "services/mnemo/main.py", "--host", "0.0.0.0", "--port", "8208"]
