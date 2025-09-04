# Mnemosyne Persistent Memory & Lucian Voss AI Assistant

## Overview

MnemosyneOS is the persistent memory and reasoning substrate powering the Lucian Voss AI Assistant within JB-VPS. It provides advanced memory, knowledge management, and automation capabilities, enabling intelligent command-line and menu-driven interactions.

- **Lucian Voss**: The AI persona and assistant
- **MnemosyneOS**: The memory and reasoning engine
- **JB-VPS**: The host shell and automation platform

## Architecture

### Memory System
- **7-Layer Memory Model**:
  - Episodic: Event-based memories
  - Semantic: Facts and knowledge
  - Procedural: How-to and scripts
  - Reflective: Insights and self-analysis
  - Affective: Emotional context
  - Identity: System/user profiles
  - Meta: Reasoning about reasoning
- **Document Ingestion**: Indexes and stores docs for recall
- **RSS Monitoring**: Tracks external info sources
- **Reflection Engine**: Generates insights from stored data

### Service Integration
- Runs as a systemd service (`mnemo.service`)
- CLI and menu integration via `jb ai:*` commands
- Configurable via `/etc/jb-vps/ai.env`

## Features

- Persistent, queryable memory
- Automated document ingestion
- RSS feed monitoring and recall
- Reflection and insight generation
- Secure configuration and API key management
- Preview and dry-run support for all actions
- Full menu and CLI access

## Usage

### Menu Options
- Ingest documentation (improves AI knowledge)
- Add RSS feeds for monitoring
- Recall memories with queries
- Generate reflections
- Start/stop MnemosyneOS service
- Configure AI settings
- Check AI status and statistics

### CLI Commands
- `jb ai:config` — Configure AI settings
- `jb ai:ingest-docs [PATH]` — Ingest docs
- `jb ai:remember "TEXT"` — Store a memory
- `jb ai:reflect` — Generate insights
- `jb ai:recall "QUERY"` — Query memory
- `jb ai:rss:add URL` — Add RSS feed
- `jb ai:rss:pull-now` — Pull RSS feeds
- `jb ai:status` — System status

## Configuration

- File: `/etc/jb-vps/ai.env`
- LLM provider settings (OpenAI, Anthropic, DeepSeek)
- API keys and secrets
- Data storage paths
- Service management options

## Logs & Data
- Service logs: `/var/log/jb-vps/ai.log`
- Memory data: `/var/lib/jb-vps/ai/`
- RSS data: `/var/lib/jb-vps/ai/rss/`

## Security
- All sensitive configs stored in secure locations
- API keys never exposed in logs
- Service runs with least privilege
- Audit trails for all memory and command actions

## Extending Lucian: Command Execution Plan

To enable Lucian Voss to execute commands and scripts on the command line:

1. **Command API**: Expose a secure API endpoint or CLI for Lucian to request command execution (e.g., `jb ai:exec "<command>"`).
2. **Validation Layer**: Implement strict input validation and allow-listing to prevent dangerous commands (use `lib/validation.sh`).
3. **Preview Mode**: Always show a preview of the command and its effects before execution.
4. **Audit Logging**: Log all executed commands with timestamp, user, and context.
5. **Role-Based Access**: Restrict command execution to authorized users/groups.
6. **Dry-Run Support**: Allow Lucian to simulate command execution for safety.
7. **Menu Integration**: Add "Execute Command" and "Run Script" options to the AI menu, with full preview and confirmation steps.
8. **Feedback Loop**: Capture output/errors and store in memory for future recall and analysis.

## Example Workflow

1. User selects "Execute Command" in AI menu
2. Lucian prompts for command/script
3. System validates and previews action
4. User confirms execution
5. Command runs, output logged and stored
6. Lucian can recall and reflect on results

## Troubleshooting
- Check service status: `sudo systemctl status mnemo.service`
- View logs: `cat /var/log/jb-vps/ai.log`
- Test memory recall: `jb ai:recall "test"`
- Validate config: `jb ai:config`

## Further Reading


For questions, improvements, or bug reports, see the main JB-VPS documentation or contact the repository maintainer.


## Commercial Value & Broader Use Cases



