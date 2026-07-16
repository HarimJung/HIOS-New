#!/bin/bash
# HiOS Automation Installer
# Installs launchd agents for daily brief and Granary auto-export

set -euo pipefail

HIOS_DIR="$HOME/Documents/Visual Climate Hermes/.hios"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

echo "HiOS Automation Installer"
echo "========================="

# Create LaunchAgents dir if needed
mkdir -p "$LAUNCH_AGENTS"

# Install daily brief (7:00 AM)
echo ""
echo "1. Installing daily brief (7:00 AM)..."
cp "$HIOS_DIR/com.hios.daily-brief.plist" "$LAUNCH_AGENTS/"
launchctl load "$LAUNCH_AGENTS/com.hios.daily-brief.plist" 2>/dev/null && \
    echo "   Loaded: com.hios.daily-brief" || \
    echo "   Already loaded or error — try: launchctl load ~/Library/LaunchAgents/com.hios.daily-brief.plist"

# Install Granary auto-export (every 2 hours)
echo ""
echo "2. Installing Granary auto-export (every 2 hours)..."
if command -v granary &> /dev/null; then
    granary install 2>/dev/null && \
        echo "   Granary LaunchAgent installed." || \
        echo "   Granary already installed or error."
else
    echo "   Granary not found. Skip."
fi

echo ""
echo "Done. Installed automations:"
echo "  - Daily brief: 7:00 AM every day"
echo "  - Granary: every 2 hours (if installed)"
echo ""
echo "To uninstall:"
echo "  launchctl unload ~/Library/LaunchAgents/com.hios.daily-brief.plist"
echo "  granary uninstall"
