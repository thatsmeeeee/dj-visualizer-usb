#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

LOG_FILE="${TMPDIR:-/tmp}/djviz-server.log"
SERVER_PID=""
URL=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

is_ready() {
  local url="$1"
  curl -fsS --max-time 1 "$url" >/dev/null 2>&1
}

start_with_cmd() {
  local cmd="$1"
  local p
  for p in 8080 8081 8082; do
    URL="http://localhost:${p}/dj-visualizer.html"
    nohup bash -lc "${cmd/__PORT__/$p}" >"${LOG_FILE}" 2>&1 &
    SERVER_PID=$!

    local i
    for i in {1..48}; do
      if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        break
      fi
      if is_ready "$URL"; then
        return 0
      fi
      sleep 0.25
    done

    if kill -0 "$SERVER_PID" 2>/dev/null; then
      kill "$SERVER_PID" 2>/dev/null || true
    fi
    SERVER_PID=""
  done
  return 1
}

if command -v python3 >/dev/null 2>&1; then
  start_with_cmd "python3 -m http.server __PORT__" || true
elif command -v python >/dev/null 2>&1; then
  start_with_cmd "python -m http.server __PORT__" || true
elif command -v npx >/dev/null 2>&1; then
  start_with_cmd "npx --yes http-server -p __PORT__ -c-1 ." || true
else
  echo "Could not find Python or Node.js (npx)."
  echo "Install Python 3 or Node.js and run start.command again."
  exit 1
fi

if [[ -z "${SERVER_PID}" || -z "${URL}" ]]; then
  echo "Failed to start server on ports 8080/8081/8082."
  exit 2
fi

echo "Server running at ${URL}"

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [[ -x "${CHROME_BIN}" ]]; then
  BROWSER_PID=""
  if [[ -n "${TMPDIR:-}" && -d "${TMPDIR}" && -w "${TMPDIR}" ]]; then
    PROFILE_DIR="${TMPDIR%/}/djviz-profile-$$"
    mkdir -p "${PROFILE_DIR}" || true
    "${CHROME_BIN}" --new-window --user-data-dir="${PROFILE_DIR}" "${URL}" >/dev/null 2>&1 &
    BROWSER_PID=$!
    sleep 0.4
    if ! kill -0 "$BROWSER_PID" 2>/dev/null; then
      BROWSER_PID=""
    fi
  fi
  if [[ -z "${BROWSER_PID}" ]]; then
    "${CHROME_BIN}" --new-window "${URL}" >/dev/null 2>&1 &
    BROWSER_PID=$!
  fi
  wait "${BROWSER_PID}" || true
else
  open "${URL}"
  echo "Chrome not found, opening default browser."
  read -r -p "Press Enter when done to stop the server..." _
fi
