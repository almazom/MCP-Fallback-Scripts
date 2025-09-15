#!/bin/bash
# CORRECT First Message Detector
# Uses the proper Telegram API to get the actual first message of today

set -euo pipefail

TARGET_DATE="${1:-today}"
CHANNEL="${2:-@aiclubsweggs}"

echo "🎯 Getting first message of $TARGET_DATE from $CHANNEL"

# Use the correct API call that handles timezone boundaries properly
MESSAGES=$(../telegram_manager.sh read_channel "$CHANNEL" --range "$TARGET_DATE" --limit 1000 2>/dev/null)

# Extract the first message from today's section
FIRST_MESSAGE=$(echo "$MESSAGES" | awk "
    /^==== $(date '+%Y-%m-%d')/ { found_today=1; next }
    /^==== [0-9]+-[0-9]+-[0-9]+/ && found_today { exit }
    found_today && /^\[.*\].*:/ { print; exit }
")

if [[ -n "$FIRST_MESSAGE" ]]; then
    echo "✅ FIRST MESSAGE OF TODAY:"
    echo "$FIRST_MESSAGE"
else
    echo "❌ No messages found for today"
    exit 1
fi