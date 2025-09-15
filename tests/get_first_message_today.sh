#!/bin/bash
# RELIABLE METHOD: Get the first message of today using border detection

set -euo pipefail

CHANNEL="${1:-@aiclubsweggs}"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🎯 GET FIRST MESSAGE OF TODAY${NC}"
echo "============================="
echo "Channel: $CHANNEL"
echo "Method: Border detection using yesterday's last message"
echo ""

echo -e "${BLUE}🔍 Scanning for day boundary...${NC}"

# Get messages in reverse order to find the boundary
MESSAGES=$(./telegram_manager.sh read "$CHANNEL" --limit 200 --order reverse 2>/dev/null)

# Find the exact border: messages before the "2025-09-14" header are today's messages
FIRST_MESSAGE=$(echo "$MESSAGES" | grep -B100 "==== 2025-09-14" | grep "^\[" | tail -1)

if [[ -n "$FIRST_MESSAGE" ]]; then
    # Extract time and details
    TIME=$(echo "$FIRST_MESSAGE" | grep -o '^\[[^]]*\]' | tr -d '[]')
    SENDER=$(echo "$FIRST_MESSAGE" | sed 's/^\[[^]]*\] //' | cut -d':' -f1)
    CONTENT=$(echo "$FIRST_MESSAGE" | sed 's/^\[[^]]*\] [^:]*: //' | head -c 100)

    echo -e "${GREEN}✅ FIRST MESSAGE OF TODAY FOUND!${NC}"
    echo ""
    echo "📅 Time: $TIME (Moscow time)"
    echo "👤 Sender: $SENDER"
    echo "💬 Content: $CONTENT..."
    echo ""

    # Validation: show the boundary context
    echo -e "${YELLOW}🔍 BORDER VALIDATION:${NC}"
    echo "$FIRST_MESSAGE"
    echo "   ⬇️  (DAY BOUNDARY)"
    echo "$(echo "$MESSAGES" | grep -A1 "==== 2025-09-14" | tail -1)"

    echo ""
    echo -e "${GREEN}🎯 RESULT: The first message of today was posted at $TIME${NC}"
else
    echo "❌ Could not detect the first message of today"
    exit 1
fi