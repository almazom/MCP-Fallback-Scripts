#!/usr/bin/env python3
"""
Telegram Cache Intelligence - Smart TTL and cache management
15 lines - manage cache lifecycle with intelligent rules
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Cache TTL rules (in minutes)
CACHE_TTL = {
    "today": 5,        # 5 minutes for today's messages
    "recent": 60,      # 1 hour for last 7 days
    "archive": 1440    # 24 hours for older messages
}

def get_cache_age_minutes(cache_file):
    """Get cache file age in minutes"""
    if not cache_file.exists():
        return float('inf')

    # Extract timestamp from filename: channel_YYYYMMDD_HHMMSS.json
    try:
        timestamp_str = cache_file.stem.split('_')[-2] + '_' + cache_file.stem.split('_')[-1]
        cache_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        return (datetime.now() - cache_time).total_seconds() / 60
    except:
        return float('inf')

def is_cache_valid(channel, filter_type="today"):
    """Check if cache is still valid based on TTL rules"""
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    clean_channel = channel.replace('@', '').replace('/', '_')

    cache_files = sorted(cache_dir.glob(f"{clean_channel}_*.json"))
    if not cache_files:
        return False, None

    latest_cache = cache_files[-1]
    age_minutes = get_cache_age_minutes(latest_cache)

    # Determine TTL based on filter type
    if filter_type == "today":
        ttl = CACHE_TTL["today"]
    elif filter_type.startswith("last:"):
        days = int(filter_type.split(':')[1])
        ttl = CACHE_TTL["recent"] if days <= 7 else CACHE_TTL["archive"]
    elif filter_type in ["yesterday", "all"]:
        ttl = CACHE_TTL["recent"]
    else:
        # Specific date - assume archive
        ttl = CACHE_TTL["archive"]

    is_valid = age_minutes < ttl
    return is_valid, latest_cache

def clean_old_caches(channel=None, keep_latest=3):
    """Clean old cache files, keeping only the latest N files per channel"""
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"

    if channel:
        # Clean specific channel
        clean_channel = channel.replace('@', '').replace('/', '_')
        cache_files = sorted(cache_dir.glob(f"{clean_channel}_*.json"))

        if len(cache_files) > keep_latest:
            for old_file in cache_files[:-keep_latest]:
                old_file.unlink()
                print(f"🧹 Removed old cache: {old_file.name}")
    else:
        # Clean all channels
        channels = set()
        for cache_file in cache_dir.glob("*.json"):
            channel_name = '_'.join(cache_file.stem.split('_')[:-2])
            channels.add(channel_name)

        for channel_name in channels:
            cache_files = sorted(cache_dir.glob(f"{channel_name}_*.json"))
            if len(cache_files) > keep_latest:
                for old_file in cache_files[:-keep_latest]:
                    old_file.unlink()
                    print(f"🧹 Removed old cache: {old_file.name}")

def cache_info():
    """Show cache information and statistics"""
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    cache_files = list(cache_dir.glob("*.json"))

    if not cache_files:
        print("📭 No cache files found")
        return

    print(f"📁 Cache directory: {cache_dir}")
    print(f"📊 Total cache files: {len(cache_files)}")
    print()

    # Group by channel
    channels = {}
    total_size = 0

    for cache_file in cache_files:
        try:
            channel_name = '_'.join(cache_file.stem.split('_')[:-2])
            if channel_name not in channels:
                channels[channel_name] = []

            age_minutes = get_cache_age_minutes(cache_file)
            size_kb = cache_file.stat().st_size / 1024
            total_size += size_kb

            # Load message count
            with open(cache_file, 'r') as f:
                data = json.load(f)
                msg_count = len(data.get('messages', []))

            channels[channel_name].append({
                'file': cache_file.name,
                'age_minutes': age_minutes,
                'size_kb': size_kb,
                'messages': msg_count
            })
        except Exception as e:
            print(f"⚠️ Error reading {cache_file.name}: {e}")

    print("📋 Cache by channel:")
    for channel, caches in channels.items():
        print(f"  @{channel}:")
        for cache in sorted(caches, key=lambda x: x['age_minutes']):
            age_str = f"{cache['age_minutes']:.0f}m ago" if cache['age_minutes'] < 60 else f"{cache['age_minutes']/60:.1f}h ago"
            print(f"    {cache['file']} - {cache['messages']} msgs, {cache['size_kb']:.1f}KB, {age_str}")

    print(f"\n💾 Total cache size: {total_size:.1f}KB")

def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_cache.py <command> [options]")
        print("\nCommands:")
        print("  info                    Show cache information")
        print("  clean [channel]         Clean old caches")
        print("  check <channel> [type]  Check if cache is valid")
        print("\nExamples:")
        print("  python telegram_cache.py info")
        print("  python telegram_cache.py clean aiclubsweggs")
        print("  python telegram_cache.py check aiclubsweggs today")
        sys.exit(1)

    command = sys.argv[1]

    if command == "info":
        cache_info()
    elif command == "clean":
        channel = sys.argv[2] if len(sys.argv) > 2 else None
        clean_old_caches(channel)
        print("✅ Cache cleanup completed")
    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: python telegram_cache.py check <channel> [type]")
            sys.exit(1)

        channel = sys.argv[2]
        filter_type = sys.argv[3] if len(sys.argv) > 3 else "today"

        is_valid, cache_file = is_cache_valid(channel, filter_type)
        if is_valid:
            print(f"✅ Cache valid for @{channel} ({filter_type}): {cache_file.name}")
        else:
            print(f"❌ Cache stale for @{channel} ({filter_type})")
            if cache_file:
                age = get_cache_age_minutes(cache_file)
                print(f"   Last cache: {cache_file.name} ({age:.0f}m old)")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()