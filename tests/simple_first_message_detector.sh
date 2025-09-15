#!/bin/bash
# SIMPLE First Message Detector
# Works with current telegram_manager.sh output format

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

TARGET_DATE="${1:-$(TZ=Europe/Moscow date '+%Y-%m-%d')}"
CHANNEL="${2:-@aiclubsweggs}"

echo -e "${CYAN}📅 SIMPLE FIRST MESSAGE DETECTOR${NC}"
echo "================================="
echo "Target Date: $TARGET_DATE"
echo "Channel: $CHANNEL"
echo ""

echo -e "${BLUE}🔍 Getting messages in reverse order...${NC}"

# Get messages in reverse order (newest first) to access recent dates
MESSAGES=$(../telegram_manager.sh read "$CHANNEL" --limit 200 --order reverse 2>/dev/null)

echo -e "${GREEN}✅ Messages retrieved${NC}"

echo -e "\n${BLUE}📊 Analyzing messages for $TARGET_DATE...${NC}"

# Look for the date header for our target date
DATE_HEADER_PATTERN="==== $TARGET_DATE"

# Check if our target date exists in the messages
if echo "$MESSAGES" | grep -q "$DATE_HEADER_PATTERN"; then
    echo -e "${GREEN}✅ Found date section for $TARGET_DATE${NC}"

    # Extract all content after the target date header until the next date header
    # Since messages are in reverse order (newest first), we need the LAST message from the section
    SECTION_CONTENT=$(echo "$MESSAGES" | awk "
        /$DATE_HEADER_PATTERN/ { found=1; next }
        /^==== [0-9]+-[0-9]+-[0-9]+/ && found { exit }
        found { print }
    ")

    # Find the first actual message (chronologically) - since we're in reverse order, this is the LAST message in the section
    FIRST_MESSAGE=$(echo "$SECTION_CONTENT" | grep -E '^\[.*\].*:' | tail -1)

    if [[ -n "$FIRST_MESSAGE" ]]; then
        echo -e "\n${GREEN}🎯 FIRST MESSAGE OF $TARGET_DATE:${NC}"
        echo "=================================="
        echo "$FIRST_MESSAGE"

        # Extract timestamp and sender for analysis
        if [[ "$FIRST_MESSAGE" =~ ^\[([0-9:]+)\]\ (.+):\ (.+) ]]; then
            TIMESTAMP="${BASH_REMATCH[1]}"
            SENDER="${BASH_REMATCH[2]}"
            CONTENT="${BASH_REMATCH[3]}"

            echo ""
            echo -e "${BLUE}📋 Message Details:${NC}"
            echo "Time: $TIMESTAMP (Moscow time)"
            echo "Sender: $SENDER"
            echo "Content: $CONTENT"
        fi

        # Show context - messages around the first one (in chronological order)
        echo -e "\n${BLUE}📋 First few messages of $TARGET_DATE (chronological order):${NC}"
        echo "$SECTION_CONTENT" | grep -E '^\[.*\].*:' | tail -3 | tac | nl

    else
        echo -e "${RED}❌ No messages found in the $TARGET_DATE section${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Date section $TARGET_DATE not found${NC}"

    # Show available dates for debugging
    echo -e "\n${YELLOW}📊 Available dates in messages:${NC}"
    echo "$MESSAGES" | grep -E '^==== [0-9]+-[0-9]+-[0-9]+' | head -5
    exit 1
fi

echo -e "\n${CYAN}✅ DETECTION COMPLETE${NC}"
echo "First message successfully identified using chronological order and date headers."