# AI Assistant (Lucian Voss)

This area contains menu and functionality for the Lucian Voss AI Assistant powered by MnemosyneOS.

## Overview

Lucian Voss is the resident AI for JB-VPS, with MnemosyneOS serving as its memory system. Together they form the mind and intelligence of JB-VPS:

- **JB-VPS** = the shell / operating body
- **MnemosyneOS** = the memory + reasoning substrate
- **Lucian Voss** = the emergent intelligence and assistant

## Components

- **Memory System**: 7-layer memory architecture (episodic, semantic, procedural, reflective, affective, identity, meta)
- **Knowledge Base**: Document ingestion and retrieval
- **RSS Monitoring**: External information source monitoring
- **Reflection Engine**: Automated insights generation

## Usage

The AI functionality can be accessed in two ways:

1. **CLI Commands**: Using the `jb ai:*` commands
2. **Menu Interface**: Through the AI Assistant menu

## Commands

- `jb ai:config` - Configure AI settings
- `jb ai:ingest-docs [PATH]` - Ingest documents into memory
- `jb ai:remember "TEXT"` - Store a memory
- `jb ai:reflect` - Generate reflections on memories
- `jb ai:recall "QUERY"` - Recall memories based on query
- `jb ai:rss:add URL` - Add an RSS feed to monitor
- `jb ai:rss:pull-now` - Pull RSS feeds immediately
- `jb ai:status` - Check AI system status

## Configuration

Configuration is stored in `/etc/jb-vps/ai.env` and includes:

- LLM Provider settings (OpenAI, Anthropic, DeepSeek)
- API keys for providers
- Directory paths for data storage
- Service configuration

## Service Management

The MnemosyneOS service runs as a systemd service and can be managed with standard systemd commands:

```bash
# Start the service
sudo systemctl start mnemo.service

# Stop the service
sudo systemctl stop mnemo.service

# Check status
sudo systemctl status mnemo.service
```

## Installation

To install the MnemosyneOS service:

```bash
# Install with default settings
./installers/install-mnemo.sh

# Preview installation without making changes
./installers/install-mnemo.sh --preview
```
