bash <<'BOOTSTRAP'
set -Eeuo pipefail
IFS=$'\n\t'

TARGET="${HOME}/.local/bin/filer"
mkdir -p "$(dirname "$TARGET")" "${HOME}/.filer" "${HOME}/.filer/inbox" "${HOME}/.filer/archive"

cat >"$TARGET" <<'SCRIPT'
#!/usr/bin/env bash
# ======================================================
# JB-VPS Filer Plugin v3
# Enterprise-grade AI-driven virtual inbox & file agent
# Robust | Versatile | Idempotent | Traceable
# ======================================================

set -Eeuo pipefail
IFS=$'\n\t'

CONFIG_DIR="${HOME}/.filer"
INBOX_DIR="${CONFIG_DIR}/inbox"
ARCHIVE_DIR="${CONFIG_DIR}/archive"
LOG_FILE="${CONFIG_DIR}/filer.log"
ENV_FILE="${CONFIG_DIR}/.env"

mkdir -p "$CONFIG_DIR" "$INBOX_DIR" "$ARCHIVE_DIR"

log(){ printf '%(%Y-%m-%d %H:%M:%S)T | %s\n' -1 "$*" >>"$LOG_FILE"; }
fatal(){ echo "ERROR: $*" >&2; log "FATAL: $*"; exit 1; }

ensure_env(){
  if [[ -f "$ENV_FILE" ]]; then set -a; source "$ENV_FILE"; set +a; fi
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    read -r -p "Enter your OPENAI_API_KEY: " OPENAI_API_KEY
    [[ -z "$OPENAI_API_KEY" ]] && fatal "OPENAI_API_KEY required"
    umask 077
    { echo "OPENAI_API_KEY=\"$OPENAI_API_KEY\""; echo "OPENAI_MODEL=\"gpt-4\""; } >"$ENV_FILE"
    log "API key saved to $ENV_FILE"
  fi
}

check_deps(){
  local deps=(jq curl)
  for d in "${deps[@]}"; do
    command -v "$d" >/dev/null 2>&1 || fatal "Missing dependency: $d"
  done
}

api_call(){
  local sys="$1" usr="$2" payload resp
  payload="$(jq -n --arg model "${OPENAI_MODEL:-gpt-4}" --arg sys "$sys" --arg usr "$usr" \
    '{model:$model,messages:[{role:"system",content:$sys},{role:"user",content:$usr}] }')"
  resp="$(curl -sS -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -X POST "https://api.openai.com/v1/chat/completions" -d "$payload" \
    | jq -r '.choices[0].message.content? // empty')"
  [[ -n "$resp" ]] || fatal "Empty response from API"
  echo "$resp"
}

safe_filename(){
  local content="$1"
  local name
  name="$(api_call "You are a file organizer. Suggest a short, safe, unique filename with extension based on content. No spaces, no special chars." "$content")"
  name="$(echo "$name" | tr -d '[:space:]' | tr -c '[:alnum:]._-' '_')"
  [[ -n "$name" ]] || name="snippet_$(date +%s).txt"
  echo "$name"
}

inbox_add(){
  local tmp file name
  tmp="$(mktemp)"
  echo "Paste your code (Ctrl-D when done):"
  cat >"$tmp"
  name="$(safe_filename "$(cat "$tmp")")"
  read -r -p "Filename [$name]: " custom
  [[ -n "$custom" ]] && name="$custom"
  file="$INBOX_DIR/$name"
  mv "$tmp" "$file"
  echo "📥 Saved: $file"
  log "Added to inbox: $file"
}

inbox_list(){
  echo "Inbox contents:"
  ls -1 "$INBOX_DIR" || echo "(empty)"
}

inbox_show(){
  read -r -p "File to display: " f
  [[ -f "$INBOX_DIR/$f" ]] || fatal "Not found"
  echo "---- $f ----"
  cat "$INBOX_DIR/$f"
  echo "------------"
}

inbox_move(){
  inbox_list
  read -r -p "File to move: " f
  [[ -f "$INBOX_DIR/$f" ]] || fatal "Not found"
  read -r -p "Destination path: " dest
  mkdir -p "$(dirname "$dest")"
  mv "$INBOX_DIR/$f" "$dest"
  echo "📂 Moved: $dest"
  log "Moved $f -> $dest"
}

inbox_archive(){
  inbox_list
  read -r -p "File to archive: " f
  [[ -f "$INBOX_DIR/$f" ]] || fatal "Not found"
  mv "$INBOX_DIR/$f" "$ARCHIVE_DIR/$f.$(date +%s)"
  echo "🗄️ Archived $f"
  log "Archived $f"
}

menu(){
  PS3="Choose option: "
  select opt in \
    "Add code" \
    "List inbox" \
    "Show file" \
    "Move file" \
    "Archive file" \
    "Quit"; do
    case $REPLY in
      1) inbox_add;;
      2) inbox_list;;
      3) inbox_show;;
      4) inbox_move;;
      5) inbox_archive;;
      6) exit 0;;
      *) echo "Invalid";;
    esac
  done
}

main(){
  ensure_env
  check_deps
  mkdir -p "$INBOX_DIR" "$ARCHIVE_DIR"
  case "$1" in
    add) inbox_add;;
    list) inbox_list;;
    show) inbox_show;;
    move) inbox_move;;
    archive) inbox_archive;;
    *) menu;;
  esac
}

main "$@"
SCRIPT

chmod +x "$TARGET"
echo "Installed: $TARGET"
"$TARGET"
BOOTSTRAP
