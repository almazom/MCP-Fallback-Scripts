#!/usr/bin/env python3
"""
Simple Boundary Check - KISS principle applied
Just checks: Is cache stale? How many messages behind?
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def check_cache_freshness(channel, max_age_minutes=60):
    """Simple staleness check - is cache older than N minutes?"""
    cache_dir = Path(__file__).parent.parent.parent / ".tmp" / "telegram_cache"

    # Find latest cache file
    cache_files = sorted(cache_dir.glob(f"{channel.replace('@', '')}_*.json"))
    if not cache_files:
        print("no_cache")
        return 1

    latest_cache = cache_files[-1]

    # Check file age
    file_age = datetime.now() - datetime.fromtimestamp(latest_cache.stat().st_mtime)
    if file_age > timedelta(minutes=max_age_minutes):
        print("stale")
        return 1

    print("fresh")
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_boundary_check.py <channel> [max_age_minutes]")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    max_age = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    exit_code = check_cache_freshness(channel, max_age)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()