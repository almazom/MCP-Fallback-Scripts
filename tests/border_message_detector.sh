#!/bin/bash
# Border Message Detector - Find first message of today using yesterday's last message as reference

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

CHANNEL="${1:-@aiclubsweggs}"

echo -e "${YELLOW}🎯 BORDER MESSAGE DETECTION${NC}"
echo "============================"
echo "Channel: $CHANNEL"
echo ""

echo -e "${BLUE}STEP 1: Find YESTERDAY'S last message${NC}"
echo "Using reverse scan to find the boundary..."

# Get messages in reverse chronological order and find the day boundary
MESSAGES=$(./telegram_manager.sh read "$CHANNEL" --limit 300 --order reverse 2>/dev/null)

echo -e "\n${BLUE}STEP 2: Extract yesterday's last message time${NC}"
# Find yesterday's date header and the first message after it
YESTERDAY_LAST=$(echo "$MESSAGES" | grep -A5 "2025-09-14.*Sunday" | grep "^\[" | head -1)

if [[ -n "$YESTERDAY_LAST" ]]; then
    YESTERDAY_TIME=$(echo "$YESTERDAY_LAST" | grep -o '^\[[^]]*\]' | tr -d '[]')
    echo "📅 Yesterday's last message: $YESTERDAY_TIME"
    echo "   Content: $(echo "$YESTERDAY_LAST" | cut -d']' -f2- | head -c 50)..."
else
    echo "❌ Could not find yesterday's last message"
    exit 1
fi

echo -e "\n${BLUE}STEP 3: Find TODAY'S first message${NC}"
# The next message in chronological order after yesterday's last message should be today's first

# Get messages and find what comes after the yesterday boundary
TODAY_FIRST=$(echo "$MESSAGES" | grep -B20 "$YESTERDAY_TIME" | grep "^\[" | tail -1)

if [[ -n "$TODAY_FIRST" ]]; then
    TODAY_TIME=$(echo "$TODAY_FIRST" | grep -o '^\[[^]]*\]' | tr -d '[]')
    echo "📅 Today's first message: $TODAY_TIME"
    echo "   Content: $(echo "$TODAY_FIRST" | cut -d']' -f2- | head -c 50)..."

    # Validate this is actually from today (2025-09-15)
    VALIDATION=$(echo "$MESSAGES" | grep -A1 -B1 "$TODAY_TIME" | grep "2025-09-15\|06:11")
    if [[ -n "$VALIDATION" ]]; then
        echo -e "\n${GREEN}✅ BORDER DETECTION SUCCESSFUL!${NC}"
        echo "📊 Yesterday ends at: $YESTERDAY_TIME"
        echo "📊 Today begins at: $TODAY_TIME"

        # Show the border transition
        echo -e "\n${YELLOW}📍 BORDER TRANSITION:${NC}"
        echo "$YESTERDAY_LAST"
        echo "   ⬇️  (TIME BOUNDARY - END OF DAY)"
        echo "$TODAY_FIRST"
    else
        echo "⚠️  Warning: Time validation inconclusive"
    fi
else
    echo "❌ Could not find today's first message"
    exit 1
fi

echo -e "\n${GREEN}🎯 RESULT: First message of today is at $TODAY_TIME${NC}"