#!/bin/bash
# HiOS Daily Brief — runs via launchd at 7:00 AM
# Invokes Claude Code to generate the morning brief

set -euo pipefail

VAULT_DIR="$HOME/Documents/Visual Climate Hermes"
LOG_DIR="$VAULT_DIR/.hios/logs"
LOG_FILE="$LOG_DIR/daily-brief-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

echo "$(date): Starting daily brief..." >> "$LOG_FILE"

# Run Claude Code with /today command
cd "$VAULT_DIR"
/usr/local/bin/claude --print \
  --permission-mode acceptEdits \
  --allowedTools "Read,Write,Edit,Glob,Grep" \
  "Run /today. Generate the daily note for today. Read all project STATUS files, check the inbox, and create the daily brief." \
  >> "$LOG_FILE" 2>&1

echo "$(date): Daily brief complete." >> "$LOG_FILE"

# macOS notification
osascript -e 'display notification "Daily brief generated. Check your daily note." with title "HiOS" subtitle "Morning Brief"' 2>/dev/null || true
