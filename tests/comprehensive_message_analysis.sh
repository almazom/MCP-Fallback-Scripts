#!/bin/bash
# Comprehensive Message Analysis
# Analyzes all candidate messages around September 14-15 boundary

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CHANNEL="${1:-@aiclubsweggs}"

echo -e "${CYAN}📊 COMPREHENSIVE MESSAGE ANALYSIS${NC}"
echo "================================="
echo "Channel: $CHANNEL"
echo "Focus: September 14-15 boundary analysis"
echo ""

echo -e "${BLUE}🔍 Getting extended message history...${NC}"
MESSAGES=$(../telegram_manager.sh read "$CHANNEL" --limit 500 --order reverse 2>/dev/null)

echo -e "${GREEN}✅ Messages retrieved${NC}"

echo -e "\n${BLUE}📋 ALL CANDIDATE MESSAGES AROUND BOUNDARY:${NC}"
echo "============================================="

# Extract messages from both Sept 14 and Sept 15, plus show exact boundary
echo "$MESSAGES" | awk '
    /^==== 2025-09-15/ {
        print "\n" CYAN "🟢 SEPTEMBER 15, 2025 (MONDAY) SECTION:" NC
        print "======================================"
        in_sept15 = 1
        in_sept14 = 0
        next
    }
    /^==== 2025-09-14/ {
        print "\n" YELLOW "🟡 SEPTEMBER 14, 2025 (SUNDAY) SECTION:" NC
        print "======================================"
        in_sept14 = 1
        in_sept15 = 0
        next
    }
    /^==== 2025-09-13/ {
        in_sept14 = 0
        in_sept15 = 0
        exit
    }
    in_sept15 && /^\[.*\].*:/ {
        print GREEN "  " $0 NC
    }
    in_sept14 && /^\[.*\].*:/ {
        print YELLOW "  " $0 NC
    }
    BEGIN {
        RED="\033[0;31m"
        GREEN="\033[0;32m"
        YELLOW="\033[1;33m"
        BLUE="\033[0;34m"
        CYAN="\033[0;36m"
        NC="\033[0m"
    }
'

echo -e "\n${CYAN}🎯 SPECIFIC RAG MESSAGE ANALYSIS:${NC}"
echo "================================="

# Find and highlight the RAG message
RAG_CONTEXT=$(echo "$MESSAGES" | grep -A3 -B3 "Запустил наконец раг")
echo "$RAG_CONTEXT" | while IFS= read -r line; do
    if [[ "$line" == *"Запустил наконец раг"* ]]; then
        echo -e "${RED}➤ RAG MESSAGE: $line${NC}"
    elif [[ "$line" == *"==== 2025-09-14"* ]]; then
        echo -e "${YELLOW}   Under date section: $line${NC}"
    else
        echo "   Context: $line"
    fi
done

echo -e "\n${CYAN}⏰ TIME SEQUENCE ANALYSIS:${NC}"
echo "========================="

echo -e "${BLUE}Messages in chronological order around boundary:${NC}"

# Show time progression
echo "$MESSAGES" | grep -E "^\[.*\].*:" | grep -A10 -B10 "22:13:23\|06:11:48\|04:31:33" | \
    awk '/22:13:23|06:11:48|04:31:33/ {
        if ($0 ~ /22:13:23/) print RED "🔴 " $0 " ← RAG MESSAGE" NC
        else if ($0 ~ /04:31:33/) print YELLOW "🟡 " $0 " ← BOUNDARY CANDIDATE" NC
        else if ($0 ~ /06:11:48/) print GREEN "🟢 " $0 " ← SIMPLE DETECTOR RESULT" NC
        else print "   " $0
    }
    !/22:13:23|06:11:48|04:31:33/ {print "   " $0}
    BEGIN {
        RED="\033[0;31m"
        GREEN="\033[0;32m"
        YELLOW="\033[1;33m"
        NC="\033[0m"
    }'

echo -e "\n${CYAN}🤔 ANALYSIS SUMMARY:${NC}"
echo "==================="
echo "1. RAG message: 22:13:23 (Sept 14 section) - 'Запустил наконец раг...'"
echo "2. Boundary candidate: 04:31:33 (Sept 14 section) - Photo message"
echo "3. Simple detector result: 06:11:48 (Sept 15 section) - 'Звучит как одна сплошная инновация!'"
echo ""
echo -e "${YELLOW}❓ QUESTION: Which message is truly the first of September 15?${NC}"
echo "   - User claims: RAG message (22:13:23) should be first of Sept 15"
echo "   - System shows: RAG message under Sept 14 section"
echo "   - Possible issue: Timezone conversion or date boundary logic"

echo -e "\n${CYAN}✅ ANALYSIS COMPLETE${NC}"