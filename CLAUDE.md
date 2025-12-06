# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nfty-say is a Go service that subscribes to ntfy.sh topics and speaks incoming messages using text-to-speech (Piper TTS via a say.sh script).

## Commands

All commands use `just` (justfile):

```bash
just              # Build and run locally
just build        # Build binary only
just watch        # Live reload during development (requires watchexec)
just docker-up    # Start containerized service (24/7 mode)
just docker-logs  # View container logs
just docker-down  # Stop container
```

## Configuration

Environment variables (via `.env` file, loaded automatically by justfile):
- `NFTY_SERVER` - ntfy server URL (default: https://ntfy.sh)
- `NFTY_TOPICS` - comma-separated topic list (required)
- `NFTY_SAY` - TTS command path (supports `~/` expansion; pre-configured in Docker)

Flags override env vars: `-server`, `-topics`, `-say`

## Architecture

Single-file Go application (`main.go`):
- Subscribes to ntfy JSON stream endpoint
- Auto-reconnects on connection failure (5s delay)
- Executes configurable TTS command for each message
- Graceful shutdown on SIGINT/SIGTERM

Docker setup mounts host PulseAudio socket so container audio plays on host speakers.
