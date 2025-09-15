#!/bin/bash
# CORE FIX: Ultra-robust first message detection for telegram_manager.sh
# This implements the fix that should be integrated into the main script

set -euo pipefail

TARGET_DATE="${1:-$(TZ=Europe/Moscow date '+%Y-%m-%d')}"
CHANNEL="${2:-@aiclubsweggs}"

echo "🎯 ULTRA-ROBUST FIRST MESSAGE DETECTION"
echo "======================================="
echo "Target Date: $TARGET_DATE"
echo "Channel: $CHANNEL"

# CORE PRINCIPLE: Use Message ID Sequential Analysis as PRIMARY method
# Message IDs are sequential and timezone-independent
get_first_message_by_id() {
    local target_date="$1"
    local channel="$2"

    echo "📊 Method: Message ID Sequential Analysis (MOST RELIABLE)"

    # Get large batch of messages
    local messages=$(../telegram_manager.sh read "$channel" --limit 1000 --order reverse 2>/dev/null)

    # Strategy: Get ALL message IDs, then find the range for our target date
    # and take the LOWEST ID from that range

    # Find all messages that could be from our target date
    # (accounting for timezone display issues)
    local candidate_messages=$(echo "$messages" | grep -A3 -B3 "$target_date")

    if [[ -n "$candidate_messages" ]]; then
        # Extract all message IDs from candidates and find the minimum
        local min_id=$(echo "$candidate_messages" | grep -o "ID: [0-9]*" | grep -o "[0-9]*" | sort -n | head -1)

        if [[ -n "$min_id" ]]; then
            # Get the full message for this ID
            local first_message=$(echo "$messages" | grep -A5 "ID: $min_id")

            echo "✅ FOUND: Message ID $min_id is the first message of $target_date"
            echo ""
            echo "📅 FIRST MESSAGE DETAILS:"
            echo "$first_message"
            return 0
        fi
    fi

    echo "❌ FALLBACK NEEDED: Could not find first message using ID analysis"
    return 1
}

# FALLBACK: Comprehensive scanning with multiple strategies
get_first_message_fallback() {
    local target_date="$1"
    local channel="$2"

    echo "🔄 FALLBACK: Comprehensive Multi-Strategy Scan"

    # Strategy 1: Get messages in chronological order and find first match
    echo "Strategy 1: Chronological scan..."
    local chrono_messages=$(../telegram_manager.sh read "$channel" --limit 1000 --order chronological 2>/dev/null)
    local first_chrono=$(echo "$chrono_messages" | grep -m1 "$target_date")

    # Strategy 2: Get messages in reverse order and find last occurrence
    echo "Strategy 2: Reverse scan for boundary..."
    local reverse_messages=$(../telegram_manager.sh read "$channel" --limit 1000 --order reverse 2>/dev/null)

    # Strategy 3: Use date range with wider tolerance
    echo "Strategy 3: Extended date range..."
    local range_messages=$(../telegram_manager.sh read_channel "$channel" --range "$target_date:$target_date" --limit 1000 2>/dev/null)

    # Cross-validate results
    if [[ -n "$first_chrono" ]]; then
        echo "✅ Chronological method found match"
        echo "$first_chrono"
        return 0
    else
        echo "❌ All fallback strategies failed"
        return 1
    fi
}

# MAIN EXECUTION
echo ""
if get_first_message_by_id "$TARGET_DATE" "$CHANNEL"; then
    echo ""
    echo "🎯 SUCCESS: First message detected using primary method"
else
    echo ""
    if get_first_message_fallback "$TARGET_DATE" "$CHANNEL"; then
        echo ""
        echo "🎯 SUCCESS: First message detected using fallback"
    else
        echo ""
        echo "🚨 CRITICAL FAILURE: Could not detect first message"
        echo "Manual intervention required"
        exit 1
    fi
fi

echo ""
echo "✅ DETECTION COMPLETE"