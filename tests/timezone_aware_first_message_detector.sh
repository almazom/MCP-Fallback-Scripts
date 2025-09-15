#!/bin/bash
# TIMEZONE-AWARE First Message Detector
# Based on research findings: Telegram uses UTC exclusively, manual conversion required

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

echo -e "${CYAN}🌍 TIMEZONE-AWARE FIRST MESSAGE DETECTOR${NC}"
echo "=========================================="
echo "Target Date: $TARGET_DATE (Moscow time)"
echo "Channel: $CHANNEL"
echo ""
echo -e "${YELLOW}🔬 Research-Based Approach: UTC → Moscow Time Conversion${NC}"

# Function to convert UTC timestamp to Moscow time
utc_to_moscow() {
    local utc_timestamp="$1"
    # Convert UTC to Moscow time (+3 hours)
    date -d "$utc_timestamp UTC +3 hours" '+%Y-%m-%d %H:%M:%S'
}

# Function to extract date from Moscow timestamp
get_moscow_date() {
    local moscow_timestamp="$1"
    echo "$moscow_timestamp" | cut -d' ' -f1
}

echo -e "\n${BLUE}STEP 1: Get Raw Messages with UTC Timestamps${NC}"
echo "--------------------------------------------"

MESSAGES=$(../telegram_manager.sh read "$CHANNEL" --limit 1000 --order reverse 2>/dev/null)

echo -e "${GREEN}✅ Retrieved messages${NC}"

echo -e "\n${BLUE}STEP 2: Parse and Convert Timestamps${NC}"
echo "-----------------------------------"

# Create temporary file for processing
TEMP_FILE="/tmp/timezone_analysis_${TARGET_DATE}.txt"
echo "UTC_TIMESTAMP|MOSCOW_TIMESTAMP|MOSCOW_DATE|MESSAGE_ID|CONTENT" > "$TEMP_FILE"

# Process each message and convert timestamps
while IFS= read -r line; do
    if [[ "$line" =~ Message\ ([0-9]+)\ \(ID:\ ([0-9]+)\) ]]; then
        MSG_NUM="${BASH_REMATCH[1]}"
        MSG_ID="${BASH_REMATCH[2]}"

        # Get the timestamp line (should be next)
        TIMESTAMP_LINE=$(echo "$MESSAGES" | grep -A1 "Message $MSG_NUM (ID: $MSG_ID)" | tail -1)

        if [[ "$TIMESTAMP_LINE" =~ 📅\ Date:\ (.+) ]]; then
            UTC_TIME="${BASH_REMATCH[1]}"

            # Convert to Moscow time
            MOSCOW_TIME=$(utc_to_moscow "$UTC_TIME" 2>/dev/null || echo "CONVERSION_ERROR")

            if [[ "$MOSCOW_TIME" != "CONVERSION_ERROR" ]]; then
                MOSCOW_DATE=$(get_moscow_date "$MOSCOW_TIME")

                # Get message content (next few lines)
                CONTENT=$(echo "$MESSAGES" | grep -A3 "ID: $MSG_ID" | tail -1 | cut -c1-50)

                echo "$UTC_TIME|$MOSCOW_TIME|$MOSCOW_DATE|$MSG_ID|$CONTENT" >> "$TEMP_FILE"
            fi
        fi
    fi
done <<< "$MESSAGES"

echo -e "${GREEN}✅ Timestamp conversion complete${NC}"

echo -e "\n${BLUE}STEP 3: Filter Messages for Target Date${NC}"
echo "---------------------------------------"

# Find all messages that belong to our target date in Moscow time
TARGET_MESSAGES=$(grep "|$TARGET_DATE|" "$TEMP_FILE")

if [[ -z "$TARGET_MESSAGES" ]]; then
    echo -e "${RED}❌ No messages found for $TARGET_DATE in Moscow time${NC}"

    # Show nearby dates for debugging
    echo -e "\n${YELLOW}📊 Available dates around target:${NC}"
    cut -d'|' -f3 "$TEMP_FILE" | sort -u | grep -E "$(date -d "$TARGET_DATE - 1 day" '+%Y-%m-%d')|$TARGET_DATE|$(date -d "$TARGET_DATE + 1 day" '+%Y-%m-%d')" || true

    exit 1
fi

echo -e "${GREEN}✅ Found $(echo "$TARGET_MESSAGES" | wc -l) messages for $TARGET_DATE${NC}"

echo -e "\n${BLUE}STEP 4: Identify First Message${NC}"
echo "------------------------------"

# Sort by message ID (chronological order) and get the first one
FIRST_MESSAGE_LINE=$(echo "$TARGET_MESSAGES" | sort -t'|' -k4 -n | head -1)

# Parse the result
IFS='|' read -r UTC_TIME MOSCOW_TIME MOSCOW_DATE MSG_ID CONTENT <<< "$FIRST_MESSAGE_LINE"

echo -e "${GREEN}🎯 FIRST MESSAGE DETECTED:${NC}"
echo "=========================="
echo "Message ID: $MSG_ID"
echo "UTC Time: $UTC_TIME"
echo "Moscow Time: $MOSCOW_TIME"
echo "Content Preview: $CONTENT"

echo -e "\n${BLUE}STEP 5: Verification${NC}"
echo "--------------------"

# Verify this is actually the first message by checking no earlier messages exist for this date
EARLIER_COUNT=$(echo "$TARGET_MESSAGES" | awk -F'|' -v target_id="$MSG_ID" '$4 < target_id' | wc -l)

if [[ "$EARLIER_COUNT" -eq 0 ]]; then
    echo -e "${GREEN}✅ VERIFICATION PASSED: No earlier messages found for $TARGET_DATE${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: Found $EARLIER_COUNT messages with lower IDs${NC}"
fi

echo -e "\n${CYAN}📊 SUMMARY STATISTICS${NC}"
echo "===================="
echo "Total messages analyzed: $(tail -n +2 "$TEMP_FILE" | wc -l)"
echo "Messages for $TARGET_DATE: $(echo "$TARGET_MESSAGES" | wc -l)"
echo "First message ID: $MSG_ID"
echo "Timezone conversion: UTC → Moscow (+3 hours)"

# Show context around first message
echo -e "\n${BLUE}📋 MESSAGE CONTEXT${NC}"
echo "=================="
echo "$TARGET_MESSAGES" | sort -t'|' -k4 -n | head -3 | while IFS='|' read -r utc moscow date id content; do
    echo "ID $id: $moscow → $content"
done

echo -e "\n${CYAN}✅ TIMEZONE-AWARE DETECTION COMPLETE${NC}"
echo "First message of $TARGET_DATE (Moscow time): ID $MSG_ID at $MOSCOW_TIME"

# Cleanup
rm -f "$TEMP_FILE"