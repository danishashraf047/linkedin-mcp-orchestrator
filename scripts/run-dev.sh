#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".venv/bin/activate" ]]; then
  echo "Missing .venv/bin/activate. Create the virtual environment first:"
  echo "  python -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -r requirements.txt"
  exit 1
fi

source .venv/bin/activate

pids=()

cleanup() {
  local status=$?
  trap - EXIT INT TERM

  if [[ ${#pids[@]} -gt 0 ]]; then
    echo
    echo "Stopping FastAPI and FastMCP..."
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI at http://127.0.0.1:8000"
uvicorn app.main:app --reload &
pids+=("$!")

echo "Starting FastMCP at http://127.0.0.1:8765/mcp"
LINKEDIN_MCP_TRANSPORT=streamable-http \
FASTMCP_HOST=127.0.0.1 \
FASTMCP_PORT=8765 \
FASTMCP_STREAMABLE_HTTP_PATH=/mcp \
python -m app.mcp_server &
pids+=("$!")

echo
echo "Both services are running. Press Ctrl+C to stop."

while :; do
  for pid in "${pids[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid"
      exit $?
    fi
  done
  sleep 1
done
