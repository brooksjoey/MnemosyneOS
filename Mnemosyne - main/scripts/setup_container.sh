# Paste this whole block and press Enter. It will: fix DNS (if needed), install Docker (official repo),
# fetch or reuse MnemosyneOS, fix the Dockerfile path, build the image, run the container with
# restart policy, and verify health. Idempotent. Ubuntu/Debian only.

cat >/tmp/mnemo_auto.sh <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

# ---------- tiny logger ----------
ok(){ printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }
info(){ printf "\033[1;36m[INFO]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[ERR]\033[0m %s\n" "$*"; exit 1; }

# ---------- config ----------
REPO_URL="https://github.com/brooksjoey/MnemosyneOS.git"
WORKDIR="/opt/mnemosyneos_src"
REPO_DIR="$WORKDIR/MnemosyneOS"
IMAGE="mnemosyneos:latest"
NAME="mnemo"
DEFAULT_PORT=8208
ZIP_FALLBACK="/root/MnemosyneOS.zip"

# ---------- root & OS check ----------
[ "$(id -u)" -eq 0 ] || die "Run as root (sudo su -)."
command -v apt-get >/dev/null 2>&1 || die "This installer supports Debian/Ubuntu (needs apt-get)."

export DEBIAN_FRONTEND=noninteractive
apt-get update -y >/dev/null
apt-get install -y --no-install-recommends ca-certificates curl git unzip jq iproute2 net-tools gnupg lsb-release >/dev/null
ok "Base tools installed."

# ---------- DNS quick repair if github.com fails ----------
if ! getent hosts github.com >/dev/null 2>&1; then
  warn "DNS cannot resolve github.com — applying safe resolver temporarily."
  chattr -i /etc/resolv.conf 2>/dev/null || true
  printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\noptions timeout:2 attempts:2\n' >/etc/resolv.conf
  chmod 644 /etc/resolv.conf
  getent hosts github.com >/dev/null 2>&1 && ok "DNS fixed." || warn "DNS still flaky; will try ZIP fallback if present."
fi

# ---------- Docker (official repo) ----------
if ! command -v docker >/dev/null 2>&1; then
  info "Installing Docker Engine from official repo…"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg" | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$ID $VERSION_CODENAME stable" >/etc/apt/sources.list.d/docker.list
  apt-get update -y >/dev/null
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
  systemctl enable --now docker
  ok "Docker installed."
else
  ok "Docker already present."
fi

# ---------- source acquisition ----------
mkdir -p "$WORKDIR"
cd "$WORKDIR"
if getent hosts github.com >/dev/null 2>&1; then
  if [ -d "$REPO_DIR/.git" ]; then
    info "Repo exists; pulling latest…"
    git -C "$REPO_DIR" fetch --all --prune || true
    git -C "$REPO_DIR" reset --hard origin/HEAD || true
  else
    info "Cloning $REPO_URL …"
    git clone "$REPO_URL" "$REPO_DIR"
  fi
elif [ -f "$ZIP_FALLBACK" ]; then
  info "Using ZIP fallback: $ZIP_FALLBACK"
  rm -rf "$REPO_DIR" /tmp/mnemo_zip
  mkdir -p /tmp/mnemo_zip
  unzip -q "$ZIP_FALLBACK" -d /tmp/mnemo_zip
  SRC="$(find /tmp/mnemo_zip -maxdepth 1 -type d -name 'MnemosyneOS' -print -quit)"
  [ -n "$SRC" ] || SRC="$(find /tmp/mnemo_zip -maxdepth 1 -type d ! -path /tmp/mnemo_zip | head -n1)"
  [ -n "$SRC" ] || die "Could not locate project folder in ZIP."
  mkdir -p "$REPO_DIR"
  rsync -a --delete "$SRC"/ "$REPO_DIR"/
else
  die "No git access and no ZIP fallback at $ZIP_FALLBACK."
fi
ok "Source ready at $(realpath "$REPO_DIR")"

# ---------- ensure .env ----------
ENV_FILE="$REPO_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  cat >"$ENV_FILE" <<EOFENV
APP_HOST=0.0.0.0
APP_PORT=${DEFAULT_PORT}
DEBUG=false
DATA_DIR=/var/lib/mnemosyneos/data
VECTOR_DIR=/var/lib/mnemosyneos/vectorstore
VECTOR_BACKEND=chroma
EOFENV
  ok "Created .env"
else
  ok ".env present"
fi

# ---------- fix Dockerfile path (only if wrong) ----------
DOCKERFILE="$REPO_DIR/Dockerfile"
if [ -f "$DOCKERFILE" ]; then
  if grep -q 'MnemosyneOS/Mnemosyne - main/services/mnemo/requirements.txt' "$DOCKERFILE"; then
    info "Fixing requirements path in Dockerfile…"
    sed -i 's|MnemosyneOS/Mnemosyne - main/services/mnemo/requirements.txt|Mnemosyne - main/services/mnemo/requirements.txt|g' "$DOCKERFILE"
    ok "Dockerfile corrected."
  fi
else
  die "Dockerfile not found at $DOCKERFILE"
fi

# ---------- build image ----------
info "Building image $IMAGE …"
docker build -t "$IMAGE" "$REPO_DIR"
ok "Image built."

# ---------- volumes ----------
docker volume create mnemo-data >/dev/null
docker volume create mnemo-logs >/dev/null

# ---------- choose ports safely (no bash-paren filters) ----------
read_port(){
  awk -F= '/^APP_PORT=/{print $2}' "$ENV_FILE" 2>/dev/null | tr -d '"[:space:]'
}
APP_PORT="$(read_port)"; [[ "$APP_PORT" =~ ^[0-9]+$ ]] || APP_PORT="$DEFAULT_PORT"
HOST_PORT="$APP_PORT"
in_use(){ ss -ltn | awk 'NR>1{print $4}' | grep -qE "[:.]'"$1"'$"; }
if in_use "$HOST_PORT"; then
  warn "Host port $HOST_PORT busy; finding next free…"
  p=$((HOST_PORT+1)); while in_use "$p"; do p=$((p+1)); done; HOST_PORT="$p"
  warn "Using host $HOST_PORT -> container $APP_PORT"
fi

# ---------- (re)run with restart policy ----------
docker rm -f "$NAME" >/dev/null 2>&1 || true
info "Starting $NAME on host ${HOST_PORT} (container ${APP_PORT})…"
docker run -d --name "$NAME" \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  -p "${HOST_PORT}:${APP_PORT}" \
  -v mnemo-data:/var/lib/mnemosyneos \
  -v mnemo-logs:/var/log/mnemosyneos \
  "$IMAGE" >/dev/null
ok "Container launched."

# ---------- health probe (host) ----------
try_urls=(
  "http://127.0.0.1:${HOST_PORT}/healthz"
  "http://127.0.0.1:${HOST_PORT}/health"
  "http://127.0.0.1:${HOST_PORT}/"
)
healthy=""
for i in $(seq 1 30); do
  for u in "${try_urls[@]}"; do
    out="$(curl -fsS --max-time 2 "$u" 2>/dev/null || true)"
    if [ -n "$out" ]; then healthy="$u"; break; fi
  done
  [ -n "$healthy" ] && break
  sleep 1
done

if [ -n "$healthy" ]; then
  ok "App responded at: $healthy"
  echo "$out"
else
  warn "No response via host. Inspecting inside the container…"
  docker logs --since=60s "$NAME" || true
  # Ensure curl & ss in container for diagnosis
  docker exec "$NAME" sh -lc 'command -v ss >/dev/null 2>&1 || (apt-get update >/dev/null && apt-get install -y --no-install-recommends iproute2 >/dev/null); command -v curl >/dev/null 2>&1 || (apt-get update >/dev/null && apt-get install -y --no-install-recommends curl >/dev/null)' || true
  docker exec "$NAME" sh -lc 'ss -lntp || true' || true

  # Fallback: try uvicorn run override to known app module without rebuild
  warn "Attempting runtime override to start FastAPI explicitly…"
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker run -d --name "$NAME" \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -p "${HOST_PORT}:${APP_PORT}" \
    -v mnemo-data:/var/lib/mnemosyneos \
    -v mnemo-logs:/var/log/mnemosyneos \
    "$IMAGE" sh -lc "uvicorn 'Mnemosyne - main.services.mnemo.api.server:app' --host 0.0.0.0 --port ${APP_PORT}" >/dev/null

  # Re-check health quickly
  for i in $(seq 1 20); do
    out="$(curl -fsS --max-time 2 "http://127.0.0.1:${HOST_PORT}/healthz" 2>/dev/null || true)"
    [ -n "$out" ] && { ok "App responded after override at /healthz"; echo "$out"; break; }
    sleep 1
  done
fi

echo "
========================================
 MnemosyneOS (Docker) — Deployment Summary
----------------------------------------
Container : $NAME
Image     : $IMAGE
Host Port : $HOST_PORT  (container $APP_PORT)
Env File  : $ENV_FILE
Repo      : $REPO_DIR
Health    : curl -sS http://127.0.0.1:${HOST_PORT}/healthz
Logs      : docker logs -f $NAME
========================================"
EOF

chmod +x /tmp/mnemo_auto.sh
sudo /tmp/mnemo_auto.sh