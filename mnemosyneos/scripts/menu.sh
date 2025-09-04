#!/bin/bash
# AI Assistant menu for JB-VPS

# Include base library
. "${JB_ROOT}/lib/base.sh"

# Menu Variables
MENU_TITLE="AI Assistant (Lucian Voss)"
MENU_DESCRIPTION="Manage Lucian Voss AI Assistant powered by MnemosyneOS"

# Function to check if the Mnemosyne service is running
check_mnemo_service() {
    if systemctl is-active --quiet mnemo.service; then
        return 0
    else
        return 1
    fi
}

# Function to handle service status display
mnemo_status_label() {
    if check_mnemo_service; then
        echo_success "RUNNING"
    else
        echo_error "STOPPED"
    fi
}

# Menu Actions
menu_ingest_docs() {
    read -p "Enter path to ingest (e.g., docs/): " path
    if [[ -z "${path}" ]]; then
        echo_error "No path specified"
        return 1
    fi
    
    jb ai:ingest-docs "${path}"
    pause_for_user
}

menu_add_rss() {
    read -p "Enter RSS feed URL: " url
    if [[ -z "${url}" ]]; then
        echo_error "No URL specified"
        return 1
    fi
    
    jb ai:rss:add "${url}"
    pause_for_user
}

menu_recall() {
    read -p "Enter search query: " query
    if [[ -z "${query}" ]]; then
        echo_error "No query specified"
        return 1
    fi
    
    jb ai:recall "${query}"
    pause_for_user
}

menu_reflect() {
    jb ai:reflect
    pause_for_user
}

menu_service_control() {
    if check_mnemo_service; then
        with_preview "sudo systemctl stop mnemo.service" "Stopping MnemosyneOS service..."
    else
        with_preview "sudo systemctl start mnemo.service" "Starting MnemosyneOS service..."
    fi
    
    sleep 2
    check_mnemo_service
    pause_for_user
}

menu_config() {
    jb ai:config
    pause_for_user
}

menu_status() {
    jb ai:status
    pause_for_user
}

# Define menu items
MENU_ITEMS=(
    "1:Ingest JB-VPS Docs:menu_ingest_docs:Ingest documentation to improve AI knowledge"
    "2:Add RSS Feed:menu_add_rss:Add an RSS feed for monitoring"
    "3:Recall from Memory:menu_recall:Search memories with a query"
    "4:Generate Reflections:menu_reflect:Generate reflections on existing memories"
    "5:Service $(mnemo_status_label):menu_service_control:Start/Stop the MnemosyneOS service"
    "6:Configuration:menu_config:Configure AI settings"
    "7:Status:menu_status:Check AI status and memory statistics"
)

# Handle menu display and interaction
handle_menu
