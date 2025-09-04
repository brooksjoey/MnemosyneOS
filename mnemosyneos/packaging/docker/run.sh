#!/bin/bash
# Service runner for MnemosyneOS (Mnemosyne v2)
# This script activates the virtual environment and starts the FastAPI service

set -e

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
VENV_PATH="${SCRIPT_DIR}/.venv"
APP_PATH="${SCRIPT_DIR}/app"
CONFIG_PATH="/etc/jb-vps/ai.env"

# Check if the virtual environment exists
if [ ! -d "${VENV_PATH}" ]; then
    echo "Error: Virtual environment not found at ${VENV_PATH}"
    echo "Please run the installer first: installers/install-mnemo.sh"
    exit 1
fi

# Parse command line arguments
HOST="127.0.0.1"
PORT=8077
DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --host=*)
            HOST="${1#*=}"
            shift
            ;;
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--host=HOST] [--port=PORT] [--debug]"
            exit 1
            ;;
    esac
done

# Activate the virtual environment and start the service
echo "Starting MnemosyneOS service..."
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo "Debug: ${DEBUG}"

# Load environment variables if config exists
if [ -f "${CONFIG_PATH}" ]; then
    echo "Loading configuration from ${CONFIG_PATH}"
    export $(grep -v '^#' "${CONFIG_PATH}" | xargs)
fi

# Activate virtual environment and start server
source "${VENV_PATH}/bin/activate"

if [ "${DEBUG}" = true ]; then
    # Debug mode with auto-reload
    exec uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
else
    # Production mode
    exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
fi
