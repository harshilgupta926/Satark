#!/usr/bin/env bash
set -Eeuo pipefail

# Local service acceptance probe. It contacts only loopback endpoints by default.
# Run this after downloading all images/models and while external networking is disabled
# if you want to record an offline-mode acceptance result.

APP_URL="${SATARK_APP_URL:-http://127.0.0.1:3000}"
SUPABASE_URL="${SATARK_LOCAL_SUPABASE_URL:-http://127.0.0.1:54321}"
OLLAMA_URL="${SATARK_LOCAL_OLLAMA_URL:-http://127.0.0.1:11434}"
MODEL="${SATARK_OLLAMA_MODEL:-qwen2.5:3b}"
COMPOSE_FILE="${SATARK_COMPOSE_FILE:-docker-compose.local.yml}"

pass() { printf '[PASS] %s\n' "$*"; }
fail() { printf '[FAIL] %s\n' "$*" >&2; exit 1; }
check_local_url() {
  local label="$1" url="$2" host
  host="$(python3 - "$url" <<'PY'
import sys
from urllib.parse import urlparse
u = urlparse(sys.argv[1])
print((u.hostname or "").lower())
PY
)"
  case "$host" in
    localhost|127.0.0.1|::1) ;;
    *) fail "$label must resolve to loopback for this probe; got host '$host'. Set the SATARK_LOCAL_* variable only for a local service." ;;
  esac
}

command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v python3 >/dev/null 2>&1 || fail "python3 is required"
command -v docker >/dev/null 2>&1 || fail "Docker is required"
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required"

check_local_url "SATARK_APP_URL" "$APP_URL"
check_local_url "SATARK_LOCAL_SUPABASE_URL" "$SUPABASE_URL"
check_local_url "SATARK_LOCAL_OLLAMA_URL" "$OLLAMA_URL"

http_ok() {
  local label="$1" url="$2" body
  body="$(mktemp)"
  if ! curl --fail --silent --show-error --max-time 8 "$url" --output "$body"; then
    rm -f "$body"
    fail "$label did not return a successful HTTP response ($url)"
  fi
  rm -f "$body"
  pass "$label responds locally"
}

http_ok "SATARK web home" "$APP_URL/"
http_ok "SATARK health snapshot" "$APP_URL/api/health"
http_ok "Local Supabase Auth health" "$SUPABASE_URL/auth/v1/health"

tags_file="$(mktemp)"
trap 'rm -f "$tags_file"' EXIT
curl --fail --silent --show-error --max-time 8 "$OLLAMA_URL/api/tags" --output "$tags_file" || fail "Local Ollama API is unavailable"
python3 - "$tags_file" "$MODEL" <<'PY' || fail "Configured local model is not present in Ollama; pull it before offline acceptance"
import json, sys
path, wanted = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as f:
    data = json.load(f)
names = {item.get("name") for item in data.get("models", [])}
if wanted not in names:
    print(f"Expected local model '{wanted}', found: {', '.join(sorted(n for n in names if n)) or '(none)'}", file=sys.stderr)
    raise SystemExit(1)
print(f"[PASS] Local Ollama model is available: {wanted}")
PY

# Show service state but do not treat a running container as proof of application correctness.
docker compose -f "$COMPOSE_FILE" ps
pass "Local endpoint and model checks completed"
printf '\nIMPORTANT: this script proves only that the listed services are reachable on loopback and the configured model is downloaded. To claim offline operation, run it with external networking disabled and also complete a real sign-in, create/read a test case, run deterministic analysis, restart the stack, and verify persistence. This script does not execute response actions or prove Wazuh/Defender connectivity.\n'
