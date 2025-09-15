#!/usr/bin/env python3
"""
Temporal Anchor - Manages anchor points for daily message boundaries
Implements RTM requirements FR-003, TR-003
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytz


class TemporalAnchor:
    """Manages temporal anchor points for message fetching"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"

        self.base_dir = Path(base_dir)
        self.anchors_file = self.base_dir / "anchors.json"
        self.moscow_tz = pytz.timezone('Europe/Moscow')

        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Load existing anchors
        self.anchors = self._load_anchors()

    def _load_anchors(self):
        """Load anchor data from file"""
        if not self.anchors_file.exists():
            return {}

        try:
            with open(self.anchors_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not load anchors.json: {e}")
            return {}

    def _save_anchors(self):
        """Save anchor data to file"""
        try:
            # Create backup first
            if self.anchors_file.exists():
                backup_file = self.anchors_file.with_suffix('.json.backup')
                self.anchors_file.rename(backup_file)

            with open(self.anchors_file, 'w', encoding='utf-8') as f:
                json.dump(self.anchors, f, indent=2, ensure_ascii=False)

            # Remove backup on successful save
            backup_file = self.anchors_file.with_suffix('.json.backup')
            if backup_file.exists():
                backup_file.unlink()

            return True

        except Exception as e:
            print(f"❌ Failed to save anchors: {e}")
            # Restore backup if available
            backup_file = self.anchors_file.with_suffix('.json.backup')
            if backup_file.exists():
                backup_file.rename(self.anchors_file)
            return False

    def get_moscow_date(self, dt=None):
        """Get current or specified date in Moscow timezone"""
        if dt is None:
            dt = datetime.now(self.moscow_tz)
        elif dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=pytz.UTC).astimezone(self.moscow_tz)

        return dt.date()

    def set_anchor(self, channel, message_id, timestamp, date=None):
        """Set anchor point for a channel"""
        if date is None:
            date = self.get_moscow_date()

        clean_channel = channel.replace('@', '')

        # Ensure channel entry exists
        if clean_channel not in self.anchors:
            self.anchors[clean_channel] = {}

        # Convert timestamp to string if it's a datetime
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime('%H:%M:%S')
        else:
            timestamp_str = str(timestamp)

        anchor_data = {
            'message_id': message_id,
            'timestamp': timestamp_str,
            'date': date.isoformat(),
            'created_at': datetime.now(self.moscow_tz).isoformat(),
            'anchor_version': '1.0'
        }

        self.anchors[clean_channel][date.isoformat()] = anchor_data

        if self._save_anchors():
            print(f"✅ Set anchor for {channel} on {date}: message {message_id} at {timestamp_str}")
            return True
        else:
            print(f"❌ Failed to save anchor for {channel}")
            return False

    def get_anchor(self, channel, date=None):
        """Get anchor point for a channel and date"""
        if date is None:
            date = self.get_moscow_date()

        clean_channel = channel.replace('@', '')
        date_str = date.isoformat()

        if clean_channel not in self.anchors:
            return None

        if date_str not in self.anchors[clean_channel]:
            return None

        return self.anchors[clean_channel][date_str]

    def get_previous_day_anchor(self, channel, date=None):
        """Get anchor point for the previous day"""
        if date is None:
            date = self.get_moscow_date()

        prev_date = date - timedelta(days=1)
        return self.get_anchor(channel, prev_date)

    def calculate_fetch_offset(self, channel, target_date=None):
        """Calculate the best offset for fetching messages"""
        if target_date is None:
            target_date = self.get_moscow_date()

        # Try to get previous day's anchor
        prev_anchor = self.get_previous_day_anchor(channel, target_date)

        if prev_anchor:
            # Use previous day's last message as offset
            return {
                'strategy': 'anchor',
                'offset_id': prev_anchor['message_id'],
                'reason': f"Using anchor from {prev_anchor['date']} at {prev_anchor['timestamp']}",
                'anchor_data': prev_anchor
            }

        # If no anchor available, try to find the closest available anchor
        clean_channel = channel.replace('@', '')
        if clean_channel in self.anchors:
            # Get all available dates for this channel
            available_dates = sorted(self.anchors[clean_channel].keys())

            if available_dates:
                # Use the most recent anchor available
                latest_date = available_dates[-1]
                latest_anchor = self.anchors[clean_channel][latest_date]

                return {
                    'strategy': 'closest_anchor',
                    'offset_id': latest_anchor['message_id'],
                    'reason': f"Using closest anchor from {latest_date} at {latest_anchor['timestamp']}",
                    'anchor_data': latest_anchor
                }

        # No anchors available - use smart offset strategy
        return {
            'strategy': 'smart_offset',
            'offset_id': 0,
            'reason': "No anchors available, using smart offset strategy",
            'anchor_data': None
        }

    def update_anchor_from_messages(self, channel, messages, date=None):
        """Update anchor based on fetched messages"""
        if not messages:
            return False

        if date is None:
            date = self.get_moscow_date()

        # Find the last message from the specified date
        last_message = None
        for msg in reversed(messages):  # Messages in reverse chronological order
            msg_date_str = msg.get('date_msk', '').split()[0]
            if msg_date_str == date.isoformat():
                last_message = msg
                break

        if last_message:
            # Extract time from timestamp
            time_part = last_message['date_msk'].split()[1]
            return self.set_anchor(
                channel,
                last_message['id'],
                time_part,
                date
            )

        return False

    def validate_anchor(self, channel, date=None):
        """Validate an anchor by checking message continuity"""
        anchor = self.get_anchor(channel, date)
        if not anchor:
            return False, "No anchor found"

        # Basic validation - anchor should have required fields
        required_fields = ['message_id', 'timestamp', 'date']
        for field in required_fields:
            if field not in anchor:
                return False, f"Missing required field: {field}"

        # Validate message ID is reasonable (positive integer)
        try:
            msg_id = int(anchor['message_id'])
            if msg_id <= 0:
                return False, "Invalid message ID"
        except (ValueError, TypeError):
            return False, "Message ID is not a valid integer"

        # Validate timestamp format
        try:
            datetime.strptime(anchor['timestamp'], '%H:%M:%S')
        except ValueError:
            return False, "Invalid timestamp format"

        # Validate date format
        try:
            datetime.fromisoformat(anchor['date'])
        except ValueError:
            return False, "Invalid date format"

        return True, "Anchor is valid"

    def list_anchors(self, channel=None):
        """List all anchors for a channel or all channels"""
        result = []

        if channel:
            clean_channel = channel.replace('@', '')
            if clean_channel in self.anchors:
                for date_str, anchor_data in self.anchors[clean_channel].items():
                    result.append({
                        'channel': f"@{clean_channel}",
                        'date': date_str,
                        **anchor_data
                    })
        else:
            for clean_channel, channel_data in self.anchors.items():
                for date_str, anchor_data in channel_data.items():
                    result.append({
                        'channel': f"@{clean_channel}",
                        'date': date_str,
                        **anchor_data
                    })

        return sorted(result, key=lambda x: (x['channel'], x['date']))

    def cleanup_old_anchors(self, retention_days=90):
        """Remove anchors older than retention period"""
        cutoff_date = self.get_moscow_date() - timedelta(days=retention_days)
        removed_count = 0

        for clean_channel in list(self.anchors.keys()):
            channel_data = self.anchors[clean_channel]
            for date_str in list(channel_data.keys()):
                try:
                    anchor_date = datetime.fromisoformat(date_str).date()
                    if anchor_date < cutoff_date:
                        del channel_data[date_str]
                        removed_count += 1
                except ValueError:
                    # Remove invalid date entries
                    del channel_data[date_str]
                    removed_count += 1

            # Remove empty channel entries
            if not channel_data:
                del self.anchors[clean_channel]

        if removed_count > 0:
            self._save_anchors()
            print(f"✅ Cleaned up {removed_count} old anchors")

        return removed_count

    def get_anchor_stats(self):
        """Get statistics about stored anchors"""
        stats = {
            'total_channels': len(self.anchors),
            'total_anchors': 0,
            'oldest_anchor': None,
            'newest_anchor': None,
            'channels': []
        }

        all_dates = []
        for clean_channel, channel_data in self.anchors.items():
            channel_stats = {
                'channel': f"@{clean_channel}",
                'anchor_count': len(channel_data),
                'date_range': None
            }

            if channel_data:
                dates = [datetime.fromisoformat(d).date() for d in channel_data.keys()]
                dates.sort()
                channel_stats['date_range'] = f"{dates[0]} to {dates[-1]}"
                all_dates.extend(dates)

            stats['channels'].append(channel_stats)
            stats['total_anchors'] += len(channel_data)

        if all_dates:
            all_dates.sort()
            stats['oldest_anchor'] = all_dates[0]
            stats['newest_anchor'] = all_dates[-1]

        return stats


def main():
    """CLI interface for temporal anchor operations"""
    import sys

    if len(sys.argv) < 2:
        print("""
Temporal Anchor Manager

Usage:
  python temporal_anchor.py set <channel> <message_id> <timestamp> [date]
  python temporal_anchor.py get <channel> [date]
  python temporal_anchor.py offset <channel> [date]
  python temporal_anchor.py list [channel]
  python temporal_anchor.py validate <channel> [date]
  python temporal_anchor.py cleanup [days]
  python temporal_anchor.py stats

Examples:
  python temporal_anchor.py set @aiclubsweggs 72856 00:58:11
  python temporal_anchor.py get @aiclubsweggs 2025-09-15
  python temporal_anchor.py offset @aiclubsweggs
  python temporal_anchor.py list @aiclubsweggs
  python temporal_anchor.py validate @aiclubsweggs
  python temporal_anchor.py cleanup 90
  python temporal_anchor.py stats
        """)
        sys.exit(1)

    ta = TemporalAnchor()
    command = sys.argv[1]

    if command == "set":
        if len(sys.argv) < 5:
            print("Error: set requires channel, message_id, and timestamp parameters")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        message_id = int(sys.argv[3])
        timestamp = sys.argv[4]

        date = None
        if len(sys.argv) > 5:
            date = datetime.strptime(sys.argv[5], '%Y-%m-%d').date()

        success = ta.set_anchor(channel, message_id, timestamp, date)
        sys.exit(0 if success else 1)

    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: get requires channel parameter")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        date = None
        if len(sys.argv) > 3:
            date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()

        anchor = ta.get_anchor(channel, date)
        if anchor:
            print(f"Anchor for {channel}:")
            print(f"  Date: {anchor['date']}")
            print(f"  Message ID: {anchor['message_id']}")
            print(f"  Timestamp: {anchor['timestamp']}")
            print(f"  Created: {anchor.get('created_at', 'Unknown')}")
        else:
            print(f"No anchor found for {channel}")
            sys.exit(1)

    elif command == "offset":
        if len(sys.argv) < 3:
            print("Error: offset requires channel parameter")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        date = None
        if len(sys.argv) > 3:
            date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()

        offset_info = ta.calculate_fetch_offset(channel, date)
        print(f"Fetch strategy for {channel}:")
        print(f"  Strategy: {offset_info['strategy']}")
        print(f"  Offset ID: {offset_info['offset_id']}")
        print(f"  Reason: {offset_info['reason']}")

    elif command == "list":
        channel = None
        if len(sys.argv) > 2:
            channel = sys.argv[2]
            if not channel.startswith('@'):
                channel = f'@{channel}'

        anchors = ta.list_anchors(channel)
        if not anchors:
            print("No anchors found")
        else:
            print(f"{'Channel':<20} {'Date':<12} {'Message ID':<12} {'Timestamp':<10}")
            print("-" * 60)
            for anchor in anchors:
                print(f"{anchor['channel']:<20} {anchor['date']:<12} "
                      f"{anchor['message_id']:<12} {anchor['timestamp']:<10}")

    elif command == "validate":
        if len(sys.argv) < 3:
            print("Error: validate requires channel parameter")
            sys.exit(1)

        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        date = None
        if len(sys.argv) > 3:
            date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()

        is_valid, message = ta.validate_anchor(channel, date)
        print(f"Validation result: {message}")
        sys.exit(0 if is_valid else 1)

    elif command == "cleanup":
        retention_days = 90
        if len(sys.argv) > 2:
            retention_days = int(sys.argv[2])

        removed = ta.cleanup_old_anchors(retention_days)
        print(f"Cleaned up {removed} old anchors")

    elif command == "stats":
        stats = ta.get_anchor_stats()
        print("Temporal Anchor Statistics:")
        print(f"  Total channels: {stats['total_channels']}")
        print(f"  Total anchors: {stats['total_anchors']}")
        print(f"  Oldest anchor: {stats['oldest_anchor']}")
        print(f"  Newest anchor: {stats['newest_anchor']}")
        print("  Channel details:")
        for channel in stats['channels']:
            print(f"    {channel['channel']}: {channel['anchor_count']} anchors "
                  f"({channel['date_range'] or 'No dates'})")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()