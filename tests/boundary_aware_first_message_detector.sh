#!/bin/bash
# BOUNDARY-AWARE First Message Detector
# Solves timezone boundary issues by searching across date sections

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

echo -e "${CYAN}🌍 BOUNDARY-AWARE FIRST MESSAGE DETECTOR${NC}"
echo "========================================"
echo "Target Date: $TARGET_DATE (Moscow time)"
echo "Channel: $CHANNEL"
echo ""
echo -e "${YELLOW}🔬 Theory: Messages can appear under wrong date due to timezone boundaries${NC}"

# Calculate previous day for boundary checking
PREV_DATE=$(date -d "$TARGET_DATE - 1 day" '+%Y-%m-%d')

echo -e "\n${BLUE}🔍 Getting messages and checking boundaries...${NC}"
echo "Checking both $PREV_DATE and $TARGET_DATE sections for boundary issues"

# Get messages with larger limit to ensure we capture boundary messages
MESSAGES=$(../telegram_manager.sh read "$CHANNEL" --limit 300 --order reverse 2>/dev/null)

echo -e "${GREEN}✅ Messages retrieved${NC}"

# Function to extract messages from a specific date section
extract_date_section() {
    local date_pattern="==== $1"
    echo "$MESSAGES" | awk "
        /$date_pattern/ { found=1; next }
        /^==== [0-9]+-[0-9]+-[0-9]+/ && found { exit }
        found && /^\[.*\].*:/ { print }
    "
}

echo -e "\n${BLUE}📊 Analyzing boundary between $PREV_DATE and $TARGET_DATE...${NC}"

# Get messages from both date sections
PREV_SECTION=$(extract_date_section "$PREV_DATE")
TARGET_SECTION=$(extract_date_section "$TARGET_DATE")

echo "Previous day ($PREV_DATE) messages: $(echo "$PREV_SECTION" | wc -l)"
echo "Target day ($TARGET_DATE) messages: $(echo "$TARGET_SECTION" | wc -l)"

# Function to convert time to minutes since midnight for comparison
time_to_minutes() {
    local time_str="$1"
    if [[ "$time_str" =~ \[([0-9]+):([0-9]+):([0-9]+)\] ]]; then
        local hours="${BASH_REMATCH[1]}"
        local minutes="${BASH_REMATCH[2]}"
        echo $((hours * 60 + minutes))
    else
        echo "9999"  # Invalid time
    fi
}

# Look for early morning messages that might be misplaced
echo -e "\n${BLUE}🕐 Checking for early morning messages in previous day section...${NC}"

EARLY_MORNING_CANDIDATES=""
if [[ -n "$PREV_SECTION" ]]; then
    # Check last few messages from previous day for early morning times (00:00-06:00)
    LATE_MESSAGES=$(echo "$PREV_SECTION" | tail -5)

    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            MINUTES=$(time_to_minutes "$line")
            # Check if time is between 00:00 and 06:00 (0-360 minutes)
            if [[ $MINUTES -le 360 ]]; then
                echo -e "${YELLOW}⚠️  Potential boundary issue found:${NC}"
                echo "   $line"
                echo "   → This early morning message might belong to $TARGET_DATE"
                EARLY_MORNING_CANDIDATES+="$line"$'\n'
            fi
        fi
    done <<< "$LATE_MESSAGES"
fi

# Look for the earliest message in target section
echo -e "\n${BLUE}🎯 Finding first message in $TARGET_DATE section...${NC}"

TARGET_FIRST=""
if [[ -n "$TARGET_SECTION" ]]; then
    TARGET_FIRST=$(echo "$TARGET_SECTION" | tail -1)  # Last in reverse order = first chronologically
    echo "First message in $TARGET_DATE section: $TARGET_FIRST"
fi

# Determine the actual first message
echo -e "\n${CYAN}🧠 BOUNDARY ANALYSIS RESULTS:${NC}"
echo "============================"

ACTUAL_FIRST=""
SOURCE_SECTION=""

if [[ -n "$EARLY_MORNING_CANDIDATES" ]]; then
    # There are early morning candidates from previous day section
    EARLIEST_CANDIDATE=$(echo "$EARLY_MORNING_CANDIDATES" | head -1)
    CANDIDATE_MINUTES=$(time_to_minutes "$EARLIEST_CANDIDATE")

    if [[ -n "$TARGET_FIRST" ]]; then
        TARGET_MINUTES=$(time_to_minutes "$TARGET_FIRST")

        # If candidate is earlier than target section's first message, it's likely the real first
        if [[ $CANDIDATE_MINUTES -lt $TARGET_MINUTES ]]; then
            ACTUAL_FIRST="$EARLIEST_CANDIDATE"
            SOURCE_SECTION="Previous day section (boundary crossing)"
            echo -e "${YELLOW}📍 BOUNDARY CROSSING DETECTED:${NC}"
            echo "Early morning message from $PREV_DATE section is actually first message of $TARGET_DATE"
        else
            ACTUAL_FIRST="$TARGET_FIRST"
            SOURCE_SECTION="Target day section"
        fi
    else
        ACTUAL_FIRST="$EARLIEST_CANDIDATE"
        SOURCE_SECTION="Previous day section (boundary crossing)"
        echo -e "${YELLOW}📍 BOUNDARY CROSSING DETECTED:${NC}"
        echo "No messages in $TARGET_DATE section, but early morning message found in $PREV_DATE section"
    fi
elif [[ -n "$TARGET_FIRST" ]]; then
    ACTUAL_FIRST="$TARGET_FIRST"
    SOURCE_SECTION="Target day section"
else
    echo -e "${RED}❌ No messages found for $TARGET_DATE${NC}"
    exit 1
fi

# Display final result
echo -e "\n${GREEN}🎯 ACTUAL FIRST MESSAGE OF $TARGET_DATE:${NC}"
echo "========================================"
echo "$ACTUAL_FIRST"
echo ""
echo -e "${BLUE}📋 Detection Details:${NC}"
echo "Source: $SOURCE_SECTION"

# Parse message details
if [[ "$ACTUAL_FIRST" =~ ^\[([0-9:]+)\]\ (.+):\ (.+) ]]; then
    TIMESTAMP="${BASH_REMATCH[1]}"
    SENDER="${BASH_REMATCH[2]}"
    CONTENT="${BASH_REMATCH[3]}"

    echo "Time: $TIMESTAMP (Moscow time)"
    echo "Sender: $SENDER"
    echo "Content: ${CONTENT:0:100}$([ ${#CONTENT} -gt 100 ] && echo "...")"
fi

echo -e "\n${CYAN}✅ BOUNDARY-AWARE DETECTION COMPLETE${NC}"
echo "Successfully handled timezone boundary issues and identified the actual first message."