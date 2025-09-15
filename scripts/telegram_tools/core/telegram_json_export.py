#!/usr/bin/env python3
"""
Telegram JSON Export - Raw JSON message range extractor
Export filtered messages as raw JSON for analysis and verification
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def find_latest_cache(channel):
    """Find the most recent cache file for a channel"""
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    clean_channel = channel.replace('@', '').replace('/', '_')

    cache_files = sorted(cache_dir.glob(f"{clean_channel}_*.json"))
    return cache_files[-1] if cache_files else None

def filter_messages_json(channel, filter_type="today"):
    """Filter cached messages and return raw JSON"""

    cache_file = find_latest_cache(channel)
    if not cache_file:
        print(f"❌ No cache found for {channel}. Run: python telegram_fetch.py {channel}", file=sys.stderr)
        return []

    # Load cache
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    messages = data['messages']

    # Date filtering
    filtered = []
    if filter_type == "today":
        today = datetime.now().strftime('%Y-%m-%d')
        filtered = [m for m in messages if m['date_msk'].startswith(today)]
    elif filter_type == "yesterday":
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        filtered = [m for m in messages if m['date_msk'].startswith(yesterday)]
    elif filter_type.startswith("last:"):
        days = int(filter_type.split(':')[1])
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [m for m in messages
                   if datetime.strptime(m['date_msk'], '%Y-%m-%d %H:%M:%S') >= cutoff]
    elif filter_type == "all":
        filtered = messages
    else:
        # Assume it's a date in YYYY-MM-DD format
        filtered = [m for m in messages if m['date_msk'].startswith(filter_type)]

    return filtered

def export_range_summary(messages):
    """Export first/last message summary from raw JSON"""
    if not messages:
        return {
            "total": 0,
            "first_message": None,
            "last_message": None
        }

    # Messages are sorted newest first, so reverse for chronological order
    chronological = sorted(messages, key=lambda x: x['date_msk'])

    return {
        "total": len(messages),
        "first_message": chronological[0],
        "last_message": chronological[-1],
        "time_range": {
            "start": chronological[0]['date_msk'],
            "end": chronological[-1]['date_msk']
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_json_export.py <channel> [filter] [--summary|--full]")
        print("\nFilters:")
        print("  today      - Messages from today")
        print("  yesterday  - Messages from yesterday")
        print("  last:7     - Messages from last 7 days")
        print("  2025-09-15 - Messages from specific date")
        print("  all        - All cached messages")
        print("\nOutput modes:")
        print("  --summary  - First/last message summary (default)")
        print("  --full     - Complete JSON export")
        print("\nExamples:")
        print("  python telegram_json_export.py aiclubsweggs today --summary")
        print("  python telegram_json_export.py aiclubsweggs today --full")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    filter_type = sys.argv[2] if len(sys.argv) > 2 else "today"
    output_mode = sys.argv[3] if len(sys.argv) > 3 else "--summary"

    try:
        messages = filter_messages_json(channel, filter_type)

        if output_mode == "--summary":
            summary = export_range_summary(messages)
            print(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            # Full JSON export
            export_data = {
                "meta": {
                    "channel": channel,
                    "filter": filter_type,
                    "exported_at": datetime.now().isoformat(),
                    "total_messages": len(messages)
                },
                "messages": messages
            }
            print(json.dumps(export_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()