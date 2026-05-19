#!/usr/bin/env bash
# stop.sh - Stop PlaySched on Linux / macOS
# Usage: ./stop.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.playsched.pid"
PORT="${FLASK_RUN_PORT:-9093}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

if [[ -f "${PID_FILE}" ]]; then
    PID=$(cat "${PID_FILE}")
    if kill -0 "$PID" 2>/dev/null; then
        info "Stopping PlaySched (PID: ${PID})..."
        kill "$PID"
        sleep 1
        rm -f "${PID_FILE}"
        info "Stopped."
        exit 0
    else
        error "PID file exists but process ${PID} is not running. Cleaning up..."
        rm -f "${PID_FILE}"
    fi
fi

# Fallback: kill by port
if command -v lsof &>/dev/null; then
    PID=$(lsof -Pi ":${PORT}" -sTCP:LISTEN -t 2>/dev/null | head -n1)
    if [[ -n "$PID" ]]; then
        info "Stopping PlaySched found on port ${PORT} (PID: ${PID})..."
        kill "$PID"
        info "Stopped."
        exit 0
    fi
fi

echo "PlaySched does not appear to be running."
