#!/bin/bash
# Test to find the actual FIRST message of today

set -euo pipefail

echo "🎯 Finding the FIRST message of TODAY (2025-09-15)"
echo "================================================"

echo -e "\n📊 Method 1: Using reverse order and finding the last today message"
./telegram_manager.sh read @aiclubsweggs --limit 200 --order reverse 2>/dev/null | \
    grep -E "(📨.*ID:|📅.*2025-09-15)" | \
    grep -B1 "2025-09-15" | \
    tail -4

echo -e "\n📊 Method 2: Using read_channel with today range and limit 1"
./telegram_manager.sh read_channel @aiclubsweggs --range today --limit 1 2>/dev/null | \
    grep -E "(📨.*ID:|📅.*Date:|💬.*Text:)"

echo -e "\n📊 Method 3: Manual check - what's the earliest time from today's messages?"
./telegram_manager.sh read @aiclubsweggs --limit 200 --order reverse 2>/dev/null | \
    grep "📅.*2025-09-15" | \
    sort | \
    head -1

echo -e "\n✅ The FIRST message of today should be ID 72857 at 06:11:48"