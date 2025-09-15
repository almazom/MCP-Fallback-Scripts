#!/usr/bin/env python3
"""
Daily Persistence - Permanent storage for complete daily message caches
Implements RTM requirements FR-002, TR-002
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytz


class DailyPersistence:
    """Manages permanent storage of daily message caches"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"

        self.base_dir = Path(base_dir)
        self.daily_dir = self.base_dir / "daily"
        self.temp_dir = self.base_dir
        self.moscow_tz = pytz.timezone('Europe/Moscow')

        # Ensure directories exist
        self.daily_dir.mkdir(parents=True, exist_ok=True)

    def get_moscow_date(self, dt=None):
        """Get current or specified date in Moscow timezone"""
        if dt is None:
            dt = datetime.now(self.moscow_tz)
        elif dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=pytz.UTC).astimezone(self.moscow_tz)

        return dt.date()

    def get_daily_path(self, channel, date):
        """Get path for daily cache file"""
        clean_channel = channel.replace('@', '').replace('/', '_')
        date_str = date.strftime('%Y-%m-%d')
        return self.daily_dir / date_str / f"{clean_channel}.json"

    def archive_daily_cache(self, channel, date=None):
        """Archive the current cache as a daily cache"""
        if date is None:
            date = self.get_moscow_date()

        # Find the latest cache file for this channel
        clean_channel = channel.replace('@', '').replace('/', '_')
        cache_files = sorted(self.temp_dir.glob(f"{clean_channel}_*.json"))

        if not cache_files:
            print(f"❌ No cache files found for {channel}")
            return False

        latest_cache = cache_files[-1]
        daily_path = self.get_daily_path(channel, date)

        # Create directory if it doesn't exist
        daily_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy cache to daily storage
        try:
            with open(latest_cache, 'r', encoding='utf-8') as src:
                cache_data = json.load(src)

            # Add daily persistence metadata
            cache_data['meta']['archived_at'] = datetime.now(self.moscow_tz).isoformat()
            cache_data['meta']['archive_date'] = date.isoformat()
            cache_data['meta']['persistence_version'] = '1.0'

            with open(daily_path, 'w', encoding='utf-8') as dst:
                json.dump(cache_data, dst, indent=2, ensure_ascii=False)

            print(f"✅ Archived daily cache: {daily_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to archive daily cache: {str(e)}")
            return False

    def restore_daily_cache(self, channel, date):
        """Restore a daily cache to the temp directory"""
        daily_path = self.get_daily_path(channel, date)

        if not daily_path.exists():
            print(f"❌ No daily cache found for {channel} on {date}")
            return False

        # Create restored cache filename
        clean_channel = channel.replace('@', '').replace('/', '_')
        date_str = date.strftime('%Y%m%d')
        restored_path = self.temp_dir / f"{clean_channel}_{date_str}_restored.json"

        try:
            shutil.copy2(daily_path, restored_path)
            print(f"✅ Restored daily cache: {restored_path}")
            return str(restored_path)

        except Exception as e:
            print(f"❌ Failed to restore daily cache: {str(e)}")
            return False

    def get_daily_cache(self, channel, date):
        """Get daily cache data without restoring to temp"""
        daily_path = self.get_daily_path(channel, date)

        if not daily_path.exists():
            return None

        try:
            with open(daily_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to read daily cache: {str(e)}")
            return None

    def list_daily_caches(self, channel=None):
        """List all available daily caches"""
        caches = []

        if channel:
            clean_channel = channel.replace('@', '').replace('/', '_')
            for date_dir in self.daily_dir.iterdir():
                if date_dir.is_dir():
                    cache_file = date_dir / f"{clean_channel}.json"
                    if cache_file.exists():
                        caches.append({
                            'channel': channel,
                            'date': date_dir.name,
                            'path': str(cache_file),
                            'size': cache_file.stat().st_size
                        })
        else:
            # List all caches
            for date_dir in self.daily_dir.iterdir():
                if date_dir.is_dir():
                    for cache_file in date_dir.glob("*.json"):
                        channel_name = f"@{cache_file.stem}"
                        caches.append({
                            'channel': channel_name,
                            'date': date_dir.name,
                            'path': str(cache_file),
                            'size': cache_file.stat().st_size
                        })

        return sorted(caches, key=lambda x: (x['date'], x['channel']))

    def cleanup_old_caches(self, retention_days=30):
        """Remove daily caches older than retention period"""
        cutoff_date = self.get_moscow_date() - timedelta(days=retention_days)
        removed_count = 0

        for date_dir in self.daily_dir.iterdir():
            if date_dir.is_dir():
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d').date()
                    if dir_date < cutoff_date:
                        shutil.rmtree(date_dir)
                        removed_count += 1
                        print(f"🗑️  Removed old cache directory: {date_dir.name}")
                except ValueError:
                    # Skip directories that don't match date format
                    continue

        print(f"✅ Cleanup complete: removed {removed_count} old cache directories")
        return removed_count

    def get_cache_stats(self):
        """Get statistics about daily cache storage"""
        stats = {
            'total_dates': 0,
            'total_caches': 0,
            'total_size': 0,
            'oldest_date': None,
            'newest_date': None,
            'channels': set()
        }

        dates = []
        for date_dir in self.daily_dir.iterdir():
            if date_dir.is_dir():
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d').date()
                    dates.append(dir_date)
                    stats['total_dates'] += 1

                    for cache_file in date_dir.glob("*.json"):
                        stats['total_caches'] += 1
                        stats['total_size'] += cache_file.stat().st_size
                        stats['channels'].add(f"@{cache_file.stem}")

                except ValueError:
                    continue

        if dates:
            stats['oldest_date'] = min(dates)
            stats['newest_date'] = max(dates)

        stats['channels'] = sorted(list(stats['channels']))
        return stats


def main():
    """CLI interface for daily persistence operations"""
    import sys

    if len(sys.argv) < 2:
        print("""
Daily Persistence Manager

Usage:
  python daily_persistence.py archive <channel> [date]
  python daily_persistence.py restore <channel> <date>
  python daily_persistence.py list [channel]
  python daily_persistence.py cleanup [days]
  python daily_persistence.py stats

Examples:
  python daily_persistence.py archive @aiclubsweggs
  python daily_persistence.py restore @aiclubsweggs 2025-09-15
  python daily_persistence.py list @aiclubsweggs
  python daily_persistence.py cleanup 30
  python daily_persistence.py stats
        """)
        sys.exit(1)

    dp = DailyPersistence()
    command = sys.argv[1]

    if command == "archive":
        if len(sys.argv) < 3:
            print("Error: archive requires channel parameter")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        date = None
        if len(sys.argv) > 3:
            date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()

        success = dp.archive_daily_cache(channel, date)
        sys.exit(0 if success else 1)

    elif command == "restore":
        if len(sys.argv) < 4:
            print("Error: restore requires channel and date parameters")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()
        result = dp.restore_daily_cache(channel, date)
        sys.exit(0 if result else 1)

    elif command == "list":
        channel = None
        if len(sys.argv) > 2:
            channel = sys.argv[2]
            if not channel.startswith('@'):
                channel = f'@{channel}'

        caches = dp.list_daily_caches(channel)
        if not caches:
            print("No daily caches found")
        else:
            print(f"{'Date':<12} {'Channel':<20} {'Size':<10}")
            print("-" * 45)
            for cache in caches:
                size_kb = cache['size'] // 1024
                print(f"{cache['date']:<12} {cache['channel']:<20} {size_kb:>7} KB")

    elif command == "cleanup":
        retention_days = 30
        if len(sys.argv) > 2:
            retention_days = int(sys.argv[2])

        removed = dp.cleanup_old_caches(retention_days)
        print(f"Cleaned up {removed} old cache directories")

    elif command == "stats":
        stats = dp.get_cache_stats()
        print("Daily Cache Statistics:")
        print(f"  Total dates: {stats['total_dates']}")
        print(f"  Total caches: {stats['total_caches']}")
        print(f"  Total size: {stats['total_size'] // 1024 // 1024} MB")
        print(f"  Oldest date: {stats['oldest_date']}")
        print(f"  Newest date: {stats['newest_date']}")
        print(f"  Channels: {len(stats['channels'])}")
        for channel in stats['channels']:
            print(f"    {channel}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()