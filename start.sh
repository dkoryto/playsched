#!/usr/bin/env bash
# start.sh - Launch PlaySched on Linux / macOS
# Usage: ./start.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="PlaySched"
PORT="${FLASK_RUN_PORT:-9093}"
HOST="${FLASK_RUN_HOST:-127.0.0.1}"
PID_FILE="${SCRIPT_DIR}/.playsched.pid"
LOG_FILE="${SCRIPT_DIR}/app.log"

cd "${SCRIPT_DIR}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check if .env exists
if [[ ! -f ".env" ]]; then
    error ".env file not found!"
    echo "Please copy .env-sample to .env and configure it:"
    echo "  cp .env-sample .env"
    exit 1
fi

# Check if port is already in use
if command -v lsof &>/dev/null; then
    if lsof -Pi ":${PORT}" -sTCP:LISTEN -t &>/dev/null; then
        error "Port ${PORT} is already in use."
        echo "Another instance of ${APP_NAME} may be running."
        echo "Check: lsof -i :${PORT}"
        exit 1
    fi
elif command -v ss &>/dev/null; then
    if ss -tlnp | grep -q ":${PORT} "; then
        error "Port ${PORT} is already in use."
        exit 1
    fi
elif command -v netstat &>/dev/null; then
    if netstat -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        error "Port ${PORT} is already in use."
        exit 1
    fi
fi

# Activate virtual environment if present
if [[ -d "venv" && -f "venv/bin/activate" ]]; then
    info "Activating virtual environment (venv)..."
    # shellcheck source=/dev/null
    source venv/bin/activate
elif [[ -d ".venv" && -f ".venv/bin/activate" ]]; then
    info "Activating virtual environment (.venv)..."
    # shellcheck source=/dev/null
    source .venv/bin/activate
fi

# Verify Python is available
if ! command -v python3 &>/dev/null; then
    error "python3 not found in PATH. Please install Python 3."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
info "Using Python ${PYTHON_VERSION}"

# Verify dependencies (quick import check)
if ! python3 -c "import flask, spotipy, apscheduler, dotenv" 2>/dev/null; then
    warn "Some Python dependencies appear to be missing."
    echo "Install them with: pip install -r requirements.txt"
    exit 1
fi

# Start the app
info "Starting ${APP_NAME}..."
info "URL: https://${HOST}:${PORT}"
info "Logs: ${LOG_FILE}"

# Run in background, detached from terminal
nohup python3 run.py > "${LOG_FILE}" 2>&1 &
PID=$!

# Save PID
echo $PID > "${PID_FILE}"

sleep 2

# Verify it started
if kill -0 $PID 2>/dev/null; then
    info "${APP_NAME} started successfully (PID: ${PID})."
    echo ""
    echo "Open your browser at: https://${HOST}:${PORT}"
    echo "To stop: ./stop.sh"
else
    error "Failed to start ${APP_NAME}. Check ${LOG_FILE} for details."
    rm -f "${PID_FILE}"
    exit 1
fi
