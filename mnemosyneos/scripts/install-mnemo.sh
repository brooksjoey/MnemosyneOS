#!/bin/bash
# Mnemosyne v2 Installer for JB-VPS
# This installer sets up the Mnemosyne service with LangChain and ChromaDB

set -e

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BASE_DIR="$(dirname "${SCRIPT_DIR}")"
SERVICE_DIR="${BASE_DIR}/services/mnemo"
VENV_PATH="${SERVICE_DIR}/.venv"
SYSTEMD_SERVICE_PATH="/etc/systemd/system/mnemo.service"

# Data and config directories
DATA_DIR="/var/lib/jb-vps/mnemo"
LOG_DIR="/var/log/jb-vps"
CONFIG_DIR="/etc/jb-vps"
CHROMA_DIR="${DATA_DIR}/chroma"

# Flags
PREVIEW=false
FORCE=false

# Process command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --preview)
            PREVIEW=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--preview] [--force]"
            exit 1
            ;;
    esac
done

# Function to execute or preview a command
execute_or_preview() {
    if [ "$PREVIEW" = true ]; then
        echo "WOULD EXECUTE: $@"
    else
        echo "EXECUTING: $@"
        "$@"
    fi
}

# Check if Python 3.11 is installed
check_python() {
    if ! command -v python3.11 &> /dev/null; then
        echo "Error: Python 3.11 is required but not found."
        echo "Please install Python 3.11 first."
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    echo "Creating necessary directories..."
    
    # Create data directories
    execute_or_preview sudo mkdir -p "${DATA_DIR}"
    execute_or_preview sudo mkdir -p "${CHROMA_DIR}"
    execute_or_preview sudo mkdir -p "${LOG_DIR}"
    execute_or_preview sudo mkdir -p "${CONFIG_DIR}"
    
    # Set ownership and permissions
    execute_or_preview sudo chown -R jb:jb "${DATA_DIR}"
    execute_or_preview sudo chown -R jb:jb "${LOG_DIR}"
    execute_or_preview sudo chown -R jb:jb "${CONFIG_DIR}"
    
    # Create subdirectories for memory types
    execute_or_preview mkdir -p "${DATA_DIR}/episodic"
    execute_or_preview mkdir -p "${DATA_DIR}/semantic"
    execute_or_preview mkdir -p "${DATA_DIR}/procedural"
    execute_or_preview mkdir -p "${DATA_DIR}/reflective"
    execute_or_preview mkdir -p "${DATA_DIR}/affective"
    execute_or_preview mkdir -p "${DATA_DIR}/identity"
    execute_or_preview mkdir -p "${DATA_DIR}/meta"
    execute_or_preview mkdir -p "${DATA_DIR}/rss"
}

# Set up Python virtual environment and install dependencies
setup_venv() {
    echo "Setting up Python virtual environment..."
    
    # Check if venv already exists
    if [ -d "${VENV_PATH}" ]; then
        if [ "$FORCE" = true ]; then
            echo "Removing existing virtual environment..."
            execute_or_preview rm -rf "${VENV_PATH}"
        else
            echo "Virtual environment already exists at ${VENV_PATH}"
            echo "Use --force to recreate it."
            return
        fi
    fi
    
    # Create and activate venv
    execute_or_preview python3.11 -m venv "${VENV_PATH}"
    
    if [ "$PREVIEW" = false ]; then
        source "${VENV_PATH}/bin/activate"
        
        # Upgrade pip
        echo "Upgrading pip..."
        pip install --upgrade pip
        
        # Install dependencies
        echo "Installing dependencies..."
        pip install -r "${SERVICE_DIR}/requirements.txt"
        
        # Deactivate venv
        deactivate
    else
        echo "WOULD EXECUTE: source ${VENV_PATH}/bin/activate"
        echo "WOULD EXECUTE: pip install --upgrade pip"
        echo "WOULD EXECUTE: pip install -r ${SERVICE_DIR}/requirements.txt"
        echo "WOULD EXECUTE: deactivate"
    fi
}

# Create the systemd service file
create_systemd_service() {
    echo "Creating systemd service file..."
    
    # Prepare service file content
    SERVICE_CONTENT="[Unit]
Description=MnemosyneOS Memory Service
After=network.target

[Service]
User=jb
Group=jb
WorkingDirectory=${SERVICE_DIR}
ExecStart=${SERVICE_DIR}/run.sh
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"
    
    # Write service file
    if [ "$PREVIEW" = true ]; then
        echo "WOULD CREATE SERVICE FILE: ${SYSTEMD_SERVICE_PATH}"
        echo "SERVICE CONTENT:"
        echo "${SERVICE_CONTENT}"
    else
        echo "${SERVICE_CONTENT}" | sudo tee "${SYSTEMD_SERVICE_PATH}" > /dev/null
        echo "Created systemd service file at ${SYSTEMD_SERVICE_PATH}"
    fi
}

# Create default configuration file
create_config_file() {
    echo "Creating default configuration file..."
    
    CONFIG_FILE="${CONFIG_DIR}/ai.env"
    
    # Check if config already exists
    if [ -f "${CONFIG_FILE}" ]; then
        echo "Configuration file already exists at ${CONFIG_FILE}"
        echo "Not overwriting existing configuration."
        return
    fi
    
    # Prepare config content
    CONFIG_CONTENT="# MnemosyneOS Configuration
# API Provider Settings
LVC_PROVIDER=openai
LVC_DEFAULT_MODEL=gpt-4o

# API Keys - Replace with your actual keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key

# Directory Settings
CHROMA_DIR=${CHROMA_DIR}
LOG_DIR=${LOG_DIR}
STATE_DIR=${DATA_DIR}
CONFIG_DIR=${CONFIG_DIR}

# Service Settings
MNEMO_HOST=127.0.0.1
MNEMO_PORT=8077
"
    
    # Write config file
    if [ "$PREVIEW" = true ]; then
        echo "WOULD CREATE CONFIG FILE: ${CONFIG_FILE}"
        echo "CONFIG CONTENT:"
        echo "${CONFIG_CONTENT}"
    else
        echo "${CONFIG_CONTENT}" | sudo tee "${CONFIG_FILE}" > /dev/null
        sudo chmod 600 "${CONFIG_FILE}"  # Secure permissions for API keys
        sudo chown jb:jb "${CONFIG_FILE}"
        echo "Created configuration file at ${CONFIG_FILE}"
    fi
}

# Enable and start the service
enable_service() {
    echo "Enabling and starting the service..."
    
    if [ "$PREVIEW" = true ]; then
        echo "WOULD EXECUTE: sudo systemctl daemon-reload"
        echo "WOULD EXECUTE: sudo systemctl enable mnemo.service"
        echo "WOULD EXECUTE: sudo systemctl start mnemo.service"
    else
        sudo systemctl daemon-reload
        sudo systemctl enable mnemo.service
        sudo systemctl start mnemo.service
        echo "Mnemo service enabled and started"
    fi
}

# Main installation process
main() {
    echo "=== MnemosyneOS Installer ==="
    echo "Mode: $([ "$PREVIEW" = true ] && echo "Preview" || echo "Install")"
    
    # Check Python version
    check_python
    
    # Create directories
    create_directories
    
    # Set up virtual environment and install dependencies
    setup_venv
    
    # Create systemd service file
    create_systemd_service
    
    # Create configuration file
    create_config_file
    
    # Enable and start the service (if not in preview mode)
    if [ "$PREVIEW" = false ]; then
        enable_service
    else
        echo "WOULD ENABLE AND START SERVICE"
    fi
    
    echo ""
    echo "=== Installation $([ "$PREVIEW" = true ] && echo "Preview" || echo "Completed") ==="
    
    if [ "$PREVIEW" = true ]; then
        echo "To perform the actual installation, run without the --preview flag"
    else
        echo "MnemosyneOS has been installed and started"
        echo "Service status: sudo systemctl status mnemo.service"
        echo "Configuration file: ${CONFIG_DIR}/ai.env"
        echo "IMPORTANT: Edit the configuration file to add your API keys"
    fi
}

# Run the installation
main
