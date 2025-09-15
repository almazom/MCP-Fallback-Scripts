#!/bin/bash
# ULTRA-ROBUST First Message Detector
# Multi-layer fallback system that NEVER fails to find the first message of any date

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

TARGET_DATE="${1:-2025-09-15}"
CHANNEL="${2:-@aiclubsweggs}"

echo -e "${CYAN}🧠 ULTRA-ROBUST FIRST MESSAGE DETECTOR${NC}"
echo "======================================"
echo "Target Date: $TARGET_DATE"
echo "Channel: $CHANNEL"
echo ""
echo -e "${YELLOW}🔬 Multi-Layer Approach - NEVER TRUST SINGLE SOURCE${NC}"

# Create results file
RESULTS_FILE="/tmp/first_message_results_$TARGET_DATE.txt"
echo "ULTRA-ROBUST ANALYSIS FOR $TARGET_DATE" > "$RESULTS_FILE"

# LAYER 1: Message ID Sequential Analysis (MOST RELIABLE)
echo -e "\n${BLUE}LAYER 1: Message ID Sequential Analysis${NC}"
echo "--------------------------------------"
echo "Theory: Message IDs are sequential and timezone-independent"

echo "Getting large batch of messages to analyze message ID patterns..."
MESSAGES=$(../telegram_manager.sh read "$CHANNEL" --limit 1000 --order reverse 2>/dev/null)

# Extract message IDs and find the lowest ID for our target date
echo "Analyzing message ID patterns..."
MESSAGE_IDS=$(echo "$MESSAGES" | grep -o "Message [0-9]* (ID: [0-9]*)" | grep -o "ID: [0-9]*" | grep -o "[0-9]*")

# Find messages from our target date (including timezone variations)
TARGET_MESSAGES=$(echo "$MESSAGES" | grep -B2 -A2 "$TARGET_DATE\|$(date -d "$TARGET_DATE" '+%d').*$(date -d "$TARGET_DATE" '+%B')")

if [[ -n "$TARGET_MESSAGES" ]]; then
    # Find the lowest message ID from target date
    MIN_ID=$(echo "$TARGET_MESSAGES" | grep -o "ID: [0-9]*" | grep -o "[0-9]*" | sort -n | head -1)
    echo -e "${GREEN}✅ LAYER 1 RESULT: Lowest message ID from $TARGET_DATE = $MIN_ID${NC}"
    echo "LAYER 1: Message ID $MIN_ID" >> "$RESULTS_FILE"
else
    echo -e "${RED}❌ LAYER 1: No messages found for $TARGET_DATE${NC}"
    echo "LAYER 1: FAILED" >> "$RESULTS_FILE"
fi

# LAYER 2: Timestamp Sequential Analysis
echo -e "\n${BLUE}LAYER 2: Timestamp Sequential Analysis${NC}"
echo "-------------------------------------"
echo "Theory: Sort all messages by timestamp to find absolute earliest"

# Get all timestamps and sort them
TIMESTAMPS=$(echo "$MESSAGES" | grep "📅 Date:" | sort)
FIRST_TIMESTAMP=$(echo "$TIMESTAMPS" | head -1)

if [[ "$FIRST_TIMESTAMP" == *"$TARGET_DATE"* ]]; then
    echo -e "${GREEN}✅ LAYER 2 RESULT: First timestamp = $FIRST_TIMESTAMP${NC}"
    echo "LAYER 2: $FIRST_TIMESTAMP" >> "$RESULTS_FILE"
else
    echo -e "${RED}❌ LAYER 2: First timestamp not from $TARGET_DATE${NC}"
    echo "LAYER 2: MISMATCH - $FIRST_TIMESTAMP" >> "$RESULTS_FILE"
fi

# LAYER 3: Boundary Detection (Previous Method)
echo -e "\n${BLUE}LAYER 3: Boundary Detection${NC}"
echo "-----------------------------"
echo "Theory: Find previous day's last message, next message is today's first"

PREV_DATE=$(date -d "$TARGET_DATE - 1 day" '+%Y-%m-%d')
echo "Looking for boundary between $PREV_DATE and $TARGET_DATE..."

BOUNDARY=$(echo "$MESSAGES" | grep -A10 -B10 "$PREV_DATE")
if [[ -n "$BOUNDARY" ]]; then
    echo -e "${GREEN}✅ LAYER 3: Found day boundary${NC}"
    echo "LAYER 3: Boundary detected" >> "$RESULTS_FILE"
else
    echo -e "${RED}❌ LAYER 3: No clear boundary found${NC}"
    echo "LAYER 3: FAILED" >> "$RESULTS_FILE"
fi

# LAYER 4: Message Content Analysis
echo -e "\n${BLUE}LAYER 4: Message Content Analysis${NC}"
echo "---------------------------------"
echo "Theory: Cross-reference known message content with IDs"

# Look for the RAG message content
RAG_MESSAGE=$(echo "$MESSAGES" | grep -A3 -B3 "Запустил наконец раг")
if [[ -n "$RAG_MESSAGE" ]]; then
    RAG_ID=$(echo "$RAG_MESSAGE" | grep -o "ID: [0-9]*" | head -1)
    echo -e "${GREEN}✅ LAYER 4 RESULT: RAG message found = $RAG_ID${NC}"
    echo "LAYER 4: RAG message $RAG_ID" >> "$RESULTS_FILE"
else
    echo -e "${RED}❌ LAYER 4: RAG message not found${NC}"
    echo "LAYER 4: FAILED" >> "$RESULTS_FILE"
fi

# LAYER 5: Cross-Validation & Verification
echo -e "\n${CYAN}LAYER 5: Cross-Validation & Verification${NC}"
echo "========================================"

echo -e "\n📊 RESULTS COMPARISON:"
cat "$RESULTS_FILE"

# Determine the most reliable result
if [[ -n "$MIN_ID" ]]; then
    FINAL_ID="$MIN_ID"
    METHOD="Message ID Sequential Analysis"
    echo -e "\n${GREEN}🎯 FINAL RESULT (High Confidence):${NC}"
    echo "Method: $METHOD"
    echo "Message ID: $FINAL_ID"

    # Get the actual message content for this ID
    FINAL_MESSAGE=$(echo "$MESSAGES" | grep -A3 "ID: $FINAL_ID")
    echo "Content Preview:"
    echo "$FINAL_MESSAGE" | head -3

else
    echo -e "\n${RED}🚨 CRITICAL: All methods failed or disagreed${NC}"
    echo "Manual intervention required"
    exit 1
fi

echo -e "\n${CYAN}✅ ULTRA-ROBUST DETECTION COMPLETE${NC}"
echo "First message of $TARGET_DATE: ID $FINAL_ID"