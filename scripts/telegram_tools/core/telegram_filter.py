#!/usr/bin/env python3
"""
Telegram Filter - Lightning fast JSON filtering
20 lines - filter cached messages by date, pattern, or range
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from media_ocr_cache import DEFAULT_CACHE_PATH, OCRCache

_OCR_CACHE = None


def get_ocr_cache():
    """Lazily load the OCR cache to avoid unnecessary disk reads."""
    global _OCR_CACHE
    if _OCR_CACHE is None:
        _OCR_CACHE = OCRCache(DEFAULT_CACHE_PATH)
    return _OCR_CACHE

def find_latest_cache(channel):
    """Find the most recent cache file for a channel"""
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    clean_channel = channel.replace('@', '').replace('/', '_')

    cache_files = sorted(
        cache_dir.glob(f"{clean_channel}_*.json"),
        key=lambda p: p.stat().st_mtime
    )
    return cache_files[-1] if cache_files else None

def validate_border_detection(messages, filtered, target_date, channel=None):
    """Fallback border detection: check 3-7 messages before first filtered message"""
    if not filtered:
        print("🔍 Fallback border detection: No filtered messages found")
        return True

    # Find the index of the first filtered message in the original messages list
    first_filtered_id = filtered[-1]['id']  # Messages are in reverse chronological order
    first_index = None

    print(f"🔍 Fallback border detection: Looking for first filtered message ID {first_filtered_id}")

    for i, msg in enumerate(messages):
        if msg['id'] == first_filtered_id:
            first_index = i
            break

    if first_index is None:
        print(f"🔍 Fallback border detection: Could not find first filtered message in original list")
        return True

    # Determine how many messages we can check (minimum 3, maximum 7)
    available_prev_messages = len(messages) - first_index - 1
    min_check = 3
    max_check = 7

    if available_prev_messages < min_check:
        print(f"🔍 Fallback border detection: Not enough previous messages to validate (need min {min_check}, have {available_prev_messages})")

        # CRITICAL: Auto-fetch more messages for proper validation
        if channel:
            print(f"🚀 Auto-fetching more messages to ensure proper border validation...")
            print(f"🕐 Using timezone-aware Moscow time validation...")
            import subprocess
            import os

            # Calculate how many more messages we need (fetch extra to be safe)
            needed_messages = min_check - available_prev_messages
            fetch_limit = max(500, len(messages) + needed_messages + 100)  # Fetch significantly more

            try:
                # Get the script directory
                script_dir = Path(__file__).parent.parent.parent.parent

                # Run telegram fetch to get more messages
                result = subprocess.run([
                    'python3',
                    str(script_dir / 'scripts/telegram_tools/core/telegram_fetch.py'),
                    channel,
                    str(fetch_limit)
                ], cwd=str(script_dir), capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"✅ Auto-fetched {fetch_limit} messages with timezone-aware timestamps")

                    # Reload the new cache and retry validation
                    new_cache_file = find_latest_cache(channel)
                    if new_cache_file:
                        with open(new_cache_file, 'r', encoding='utf-8') as f:
                            new_data = json.load(f)
                        new_messages = new_data['messages']

                        print(f"🔄 Retrying border validation with {len(new_messages)} timezone-corrected messages...")
                        return validate_border_detection(new_messages, filtered, target_date, channel=None)  # Prevent infinite recursion

                else:
                    print(f"❌ Failed to auto-fetch messages: {result.stderr}")

            except Exception as e:
                print(f"❌ Error during auto-fetch: {str(e)}")

        print("⚠️  Proceeding with incomplete validation - border detection may be inaccurate")
        return True  # Can't validate, assume correct

    # Check 3-7 messages before (as many as available, up to 7)
    check_count = min(max_check, available_prev_messages)
    validation_messages = messages[first_index + 1:first_index + 1 + check_count]

    print(f"🔍 Fallback border detection: checking {check_count} messages before first {target_date} message...")
    print(f"    First filtered message: ID {first_filtered_id} at index {first_index}")
    print(f"    Available previous messages: {available_prev_messages}, checking: {check_count}")

    border_issues = 0
    total_checked = 0

    for i, vmsg in enumerate(validation_messages, 1):
        vmsg_date = vmsg['date_msk'].split()[0]
        print(f"    Validation {i}: {vmsg['id']} at {vmsg['date_msk']} (target: {target_date})")
        total_checked += 1

        if vmsg_date == target_date:
            print(f"⚠️  Border detection issue: Message {i} before border has same date ({vmsg_date})")
            print(f"    Message ID: {vmsg['id']}, Time: {vmsg['date_msk']}")
            border_issues += 1

    if border_issues > 0:
        print(f"❌ Border detection FAILED: {border_issues}/{total_checked} previous messages have same date")
        return False
    else:
        print(f"✅ Border detection confirmed: All {total_checked} previous messages are from different date")
        return True

def filter_messages(channel, filter_type="today", pattern=None, limit=None):
    """Filter cached messages with various criteria"""

    cache_file = find_latest_cache(channel)
    if not cache_file:
        print(f"❌ No cache found for {channel}. Run: python telegram_fetch.py {channel}")
        return []

    # Load cache
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data['messages']
    print(f"📁 Using cache: {cache_file.name} ({len(messages)} messages)")

    # Date filtering
    filtered = []
    target_date = None

    if filter_type == "today":
        target_date = datetime.now().strftime('%Y-%m-%d')
        filtered = [m for m in messages if m['date_msk'].startswith(target_date)]
    elif filter_type == "yesterday":
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        filtered = [m for m in messages if m['date_msk'].startswith(target_date)]
    elif filter_type.startswith("last:"):
        days = int(filter_type.split(':')[1])
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [m for m in messages
                   if datetime.strptime(m['date_msk'], '%Y-%m-%d %H:%M:%S') >= cutoff]
    elif filter_type == "all":
        filtered = messages
    else:
        # Assume it's a date in YYYY-MM-DD format
        target_date = filter_type
        filtered = [m for m in messages if m['date_msk'].startswith(filter_type)]

    # Perform fallback border detection for single-date filters
    if target_date and filtered:
        print(f"📍 Border detection triggered for {target_date} with {len(filtered)} filtered messages")
        validate_border_detection(messages, filtered, target_date, channel)

    # Pattern filtering
    if pattern:
        filtered = [m for m in filtered
                   if re.search(pattern, m['text'], re.IGNORECASE)]

    # Limit results
    if limit:
        filtered = filtered[:limit]

    return filtered

def display_messages(messages, channel=None, group_by_date=True):
    """Display messages in a readable format"""
    if not messages:
        print("📭 No messages found")
        return

    ocr_cache = None
    if channel:
        try:
            ocr_cache = get_ocr_cache()
        except Exception as exc:
            print(f"⚠️  Unable to load OCR cache: {exc}")

    if group_by_date:
        # Group by date
        current_date = None
        for msg in messages:
            msg_date = msg['date_msk'].split()[0]
            if current_date != msg_date:
                current_date = msg_date
                weekday = datetime.strptime(msg_date, '%Y-%m-%d').strftime('%A')
                print(f"\n==== {msg_date} ({weekday}) ====")

            # Format time and message
            time_part = msg['date_msk'].split()[1]
            print(f"[{time_part}] {msg['sender']}: {msg['text']}")

            # Show metadata if available
            if msg.get('views'):
                print(f"    👁️ {msg['views']} views")
            if msg.get('reply_to_id'):
                print(f"    ↪️ Reply to message {msg['reply_to_id']}")
            if ocr_cache and msg.get('media_info'):
                entry = ocr_cache.get_entry(channel, msg['id'])
                if entry:
                    ocr_text = (entry.get('ocr_text') or '').strip()
                    if ocr_text:
                        preview = ocr_text if len(ocr_text) <= 200 else ocr_text[:197] + '...'
                        print(f"    📝 OCR: {preview}")
                    elif entry.get('error'):
                        print(f"    ⚠️ OCR cached error: {entry['error']}")
                    elif entry.get('image_metadata'):
                        meta = entry['image_metadata']
                        if meta.get('width') and meta.get('height'):
                            print(f"    🖼️ Image: {meta['width']}x{meta['height']} {meta.get('format', '')}".rstrip())
    else:
        # Simple list
        for msg in messages:
            print(f"[{msg['date_msk']}] {msg['sender']}: {msg['text']}")

    print(f"\n📊 Total: {len(messages)} messages")

def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_filter.py <channel> [filter] [pattern] [limit]")
        print("\nFilters:")
        print("  today      - Messages from today")
        print("  yesterday  - Messages from yesterday")
        print("  last:7     - Messages from last 7 days")
        print("  2025-09-15 - Messages from specific date")
        print("  all        - All cached messages")
        print("\nExamples:")
        print("  python telegram_filter.py aiclubsweggs today")
        print("  python telegram_filter.py aiclubsweggs last:3 'gemini'")
        print("  python telegram_filter.py aiclubsweggs 2025-09-15")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    filter_type = sys.argv[2] if len(sys.argv) > 2 else "today"
    pattern = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    limit = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None

    try:
        messages = filter_messages(channel, filter_type, pattern, limit)
        display_messages(messages, channel)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
