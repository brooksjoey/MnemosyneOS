#!/usr/bin/env bash
# Run bash syntax checks across key script locations
set -euo pipefail

shopt -s nullglob

declare -a files=()
files+=(bin/*.sh)
files+=(lib/*.sh)
files+=(plugins/*/plugin.sh)
files+=(areas/*/menu.sh)
files+=(services/*/run.sh)
files+=(installers/*.sh)

fail=0

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No files matched for syntax check." >&2
  exit 0
fi

echo "Running bash -n on ${#files[@]} files..."
for f in "${files[@]}"; do
  if bash -n "$f"; then
    printf "OK   %s\n" "$f"
  else
    printf "FAIL %s\n" "$f"
    fail=1
  fi
done

# Additional health checks
echo -e "\nRunning additional health checks..."

# Check if Mnemosyne service port is reachable
if nc -z 127.0.0.1 8077 2>/dev/null; then
  printf "OK   Mnemosyne service port (8077) is reachable\n"
else
  printf "WARN Mnemosyne service port (8077) is not reachable\n"
  # Not marking as fail since the service might not be installed yet
fi

exit $fail
