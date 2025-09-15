#!/bin/bash
# Simple test to find the actual border between days

echo "🎯 SIMPLE BORDER TEST"
echo "===================="

echo -e "\n📍 Method: Get messages around the time boundary and manually identify"

# Get messages around midnight transition
echo "Getting messages in reverse order to see the natural boundary..."

./telegram_manager.sh read @aiclubsweggs --limit 200 --order reverse 2>/dev/null | \
  grep -E "(^\[|==== 2025-09-1[45])" | \
  head -20

echo -e "\n✅ Look for the transition between 2025-09-14 and the first message after it"
echo "The first message NOT under the 2025-09-14 header should be today's first message"