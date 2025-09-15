#!/usr/bin/env python3
"""
Boundary Freshness Detector - Ensures SSOT temporal integrity
Sophisticated system for detecting cache boundary staleness and incomplete coverage
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("ERROR: telethon not found. Install with: pip install telethon", file=sys.stderr)
    sys.exit(1)

class BoundaryFreshnessDetector:
    """Sophisticated boundary freshness detection for SSOT integrity"""

    def __init__(self, channel):
        self.channel = channel
        self.cache_dir = Path(__file__).parent.parent.parent / ".tmp" / "telegram_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_credentials(self):
        """Load credentials from unified .env file"""
        env_file = Path(__file__).parent.parent.parent / ".env"
        creds = {}
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    creds[key.strip()] = value.strip('"')
        return creds

    def get_time_range_bounds(self, filter_type, reference_date=None):
        """Get precise time range bounds in Moscow timezone"""
        if reference_date is None:
            reference_date = datetime.now()

        # Moscow timezone (MSK, UTC+3)
        msk_offset = timedelta(hours=3)
        msk_now = reference_date + msk_offset

        if filter_type == "today":
            start = msk_now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = msk_now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filter_type == "yesterday":
            yesterday = msk_now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif filter_type.startswith("last:"):
            days = int(filter_type.split(':')[1])
            start = (msk_now - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = msk_now
        elif filter_type == "all":
            start = datetime.min
            end = msk_now
        else:
            # Specific date in YYYY-MM-DD format
            try:
                target_date = datetime.strptime(filter_type, '%Y-%m-%d')
                start = target_date + msk_offset
                end = start + timedelta(days=1) - timedelta(microseconds=1)
            except ValueError:
                raise ValueError(f"Invalid date format: {filter_type}")

        return start, end

    def is_message_in_range(self, message, start_time, end_time):
        """Check if a message falls within the time range"""
        msg_time = datetime.fromisoformat(message['date_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
        start_naive = start_time.replace(tzinfo=None)
        end_naive = end_time.replace(tzinfo=None)
        return start_naive <= msg_time <= end_naive

    def analyze_cache_boundaries(self, cache_file, time_range_start, time_range_end):
        """Analyze cache boundaries for freshness and completeness"""
        print(f"🔍 Analyzing cache boundaries for {self.channel}")
        print(f"⏰ Time range: {time_range_start} to {time_range_end}")

        with open(cache_file, 'r') as f:
            cache_data = json.load(f)

        messages = cache_data.get('messages', [])

        if not messages:
            return {
                'status': 'empty',
                'message': 'Cache is empty'
            }

        # Find boundaries in cache
        latest_cached = messages[0]  # First in array = most recent
        earliest_cached = messages[-1]  # Last in array = oldest

        print(f"📊 Cache boundaries:")
        print(f"  Latest: {latest_cached['date_msk']} (ID: {latest_cached['id']})")
        print(f"  Earliest: {earliest_cached['date_msk']} (ID: {earliest_cached['id']})")

        # Check if boundaries are in our time range
        latest_in_range = self.is_message_in_range(latest_cached, time_range_start, time_range_end)
        earliest_in_range = self.is_message_in_range(earliest_cached, time_range_start, time_range_end)

        print(f"📍 Boundary status:")
        print(f"  Latest in range: {latest_in_range}")
        print(f"  Earliest in range: {earliest_in_range}")

        return {
            'latest_cached': latest_cached,
            'earliest_cached': earliest_cached,
            'latest_in_range': latest_in_range,
            'earliest_in_range': earliest_in_range,
            'total_messages': len(messages)
        }

    async def check_live_boundaries(self, creds, latest_cached_id, earliest_cached_id):
        """Check boundaries against live Telegram data"""
        print("📡 Checking live Telegram boundaries...")

        client = TelegramClient(
            StringSession(creds['TELEGRAM_SESSION']),
            int(creds['TELEGRAM_API_ID']),
            creds['TELEGRAM_API_HASH']
        )

        await client.connect()
        entity = await client.get_entity(self.channel)

        boundary_analysis = {
            'latest_live': None,
            'earliest_live': None,
            'latest_is_fresh': False,
            'earliest_is_complete': True,
            'expansion_needed': False,
            'expansion_direction': None,
            'expansion_reason': None
        }

        try:
            # Check latest boundary
            print(f"🔍 Checking latest boundary (cached ID: {latest_cached_id})")

            # Get latest message from live Telegram
            latest_live = None
            async for message in client.iter_messages(entity, limit=1):
                latest_live = {
                    'id': message.id,
                    'date_utc': message.date.isoformat(),
                    'date_msk': message.date.astimezone(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S'),
                    'text': message.text or '[Media]'
                }
                break

            if latest_live:
                print(f"  Live latest: {latest_live['date_msk']} (ID: {latest_live['id']})")

                # Check if live is newer than cached
                if latest_live['id'] > latest_cached_id:
                    boundary_analysis['latest_is_fresh'] = False
                    boundary_analysis['expansion_needed'] = True
                    boundary_analysis['expansion_direction'] = 'forward'
                    boundary_analysis['expansion_reason'] = f"Live has newer messages (ID {latest_live['id']} > {latest_cached_id})"
                    print(f"  ❌ Latest boundary is STALE")
                else:
                    boundary_analysis['latest_is_fresh'] = True
                    print(f"  ✅ Latest boundary is FRESH")

            # Check if we need to expand backward for earlier messages
            print(f"🔍 Checking earliest boundary completeness (cached ID: {earliest_cached_id})")

            # Get messages before our cached earliest to check if we're missing any
            async for message in client.iter_messages(entity, limit=10, max_id=earliest_cached_id - 1):
                # Check if this message is in our time range
                msg_time = message.date.astimezone(timezone.utc).replace(tzinfo=None)

                boundary_analysis['earliest_is_complete'] = False
                boundary_analysis['expansion_needed'] = True
                boundary_analysis['expansion_direction'] = 'backward' if boundary_analysis['expansion_direction'] is None else 'both'
                boundary_analysis['expansion_reason'] = f"Messages exist before cached earliest (ID {message.id} < {earliest_cached_id})"
                print(f"  ❌ Found message before cached earliest: {msg_time.strftime('%Y-%m-%d %H:%M:%S')} (ID: {message.id})")
                break
            else:
                print(f"  ✅ No messages found before cached earliest")

        except Exception as e:
            print(f"❌ Error checking live boundaries: {e}")
            boundary_analysis['error'] = str(e)

        finally:
            await client.disconnect()

        return boundary_analysis

    async def smart_cache_expansion(self, creds, current_cache, expansion_direction, expansion_steps=50):
        """Intelligently expand cache boundaries"""
        print(f"🚀 Smart cache expansion: {expansion_direction} direction, {expansion_steps} steps")

        client = TelegramClient(
            StringSession(creds['TELEGRAM_SESSION']),
            int(creds['TELEGRAM_API_ID']),
            creds['TELEGRAM_API_HASH']
        )

        await client.connect()
        entity = await client.get_entity(self.channel)

        current_messages = current_cache.get('messages', [])
        current_latest = current_messages[0] if current_messages else None
        current_earliest = current_messages[-1] if current_messages else None

        new_messages = []
        expansion_details = {
            'direction': expansion_direction,
            'steps_requested': expansion_steps,
            'messages_added': 0,
            'boundary_reached': False,
            'time_range_extended': False
        }

        try:
            if expansion_direction in ['forward', 'both']:
                print("📈 Expanding forward...")
                # Get messages newer than our current latest
                async for message in client.iter_messages(entity, limit=expansion_steps, min_id=current_latest['id']):
                    # Convert to our format
                    msg_data = {
                        'id': message.id,
                        'date_utc': message.date.isoformat(),
                        'date_msk': message.date.astimezone(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S'),
                        'text': message.text or '[Media]',
                        'sender': 'Unknown',
                        'views': getattr(message, 'views', None),
                        'forwards': getattr(message, 'forwards', None),
                        'reply_to_id': getattr(message.reply_to, 'reply_to_msg_id', None) if hasattr(message, 'reply_to') and message.reply_to else None
                    }
                    new_messages.append(msg_data)

                expansion_details['messages_added'] += len(new_messages)
                print(f"  📈 Added {len(new_messages)} messages forward")

            if expansion_direction in ['backward', 'both']:
                print("📈 Expanding backward...")
                # Get messages older than our current earliest
                backward_messages = []
                async for message in client.iter_messages(entity, limit=expansion_steps, max_id=current_earliest['id'] - 1):
                    msg_data = {
                        'id': message.id,
                        'date_utc': message.date.isoformat(),
                        'date_msk': message.date.astimezone(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S'),
                        'text': message.text or '[Media]',
                        'sender': 'Unknown',
                        'views': getattr(message, 'views', None),
                        'forwards': getattr(message, 'forwards', None),
                        'reply_to_id': getattr(message.reply_to, 'reply_to_msg_id', None) if hasattr(message, 'reply_to') and message.reply_to else None
                    }
                    backward_messages.append(msg_data)

                expansion_details['messages_added'] += len(backward_messages)
                print(f"  📈 Added {len(backward_messages)} messages backward")

                # Add backward messages to the beginning (they're older)
                new_messages = backward_messages + new_messages

        except Exception as e:
            print(f"❌ Error during expansion: {e}")
            expansion_details['error'] = str(e)

        finally:
            await client.disconnect()

        # Combine with existing messages
        all_messages = new_messages + current_messages

        expansion_details['total_messages'] = len(all_messages)
        print(f"  📊 Total messages after expansion: {len(all_messages)}")

        return all_messages, expansion_details

    async def run_boundary_analysis(self, filter_type="today"):
        """Complete boundary analysis and expansion workflow"""
        print(f"🔬 Running complete boundary analysis for {self.channel}")
        print(f"🎯 Filter type: {filter_type}")

        creds = self.load_credentials()
        time_range_start, time_range_end = self.get_time_range_bounds(filter_type)

        # Step 1: Find latest cache file
        cache_files = sorted(self.cache_dir.glob(f"{self.channel.replace('@', '')}_*.json"))
        if not cache_files:
            print("❌ No cache files found")
            return {'status': 'no_cache'}

        latest_cache = cache_files[-1]
        print(f"📁 Using cache: {latest_cache.name}")

        # Step 2: Analyze cache boundaries
        boundary_analysis = self.analyze_cache_boundaries(latest_cache, time_range_start, time_range_end)

        if 'status' in boundary_analysis and boundary_analysis['status'] == 'empty':
            return boundary_analysis

        # Step 3: Check against live data
        live_analysis = await self.check_live_boundaries(
            creds,
            boundary_analysis['latest_cached']['id'],
            boundary_analysis['earliest_cached']['id']
        )

        # Step 4: Smart expansion if needed
        if live_analysis.get('expansion_needed'):
            print(f"🚀 Expansion needed: {live_analysis['expansion_reason']}")

            # Load current cache for expansion
            with open(latest_cache, 'r') as f:
                current_cache = json.load(f)

            # Perform expansion
            expanded_messages, expansion_details = await self.smart_cache_expansion(
                creds, current_cache, live_analysis['expansion_direction']
            )

            # Save expanded cache
            new_cache_file = self.cache_dir / f"{self.channel.replace('@', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_expanded.json"

            expanded_cache = {
                'meta': {
                    'channel': self.channel,
                    'cached_at': datetime.now().isoformat(),
                    'original_cache': str(latest_cache),
                    'expansion_details': expansion_details,
                    'boundary_analysis': {
                        'original_boundaries': boundary_analysis,
                        'live_analysis': live_analysis
                    }
                },
                'messages': expanded_messages
            }

            with open(new_cache_file, 'w', encoding='utf-8') as f:
                json.dump(expanded_cache, f, indent=2, ensure_ascii=False)

            print(f"✅ Expanded cache saved: {new_cache_file}")
            print(f"📊 Added {expansion_details['messages_added']} messages")

            return {
                'status': 'expanded',
                'original_cache': str(latest_cache),
                'new_cache': str(new_cache_file),
                'messages_added': expansion_details['messages_added'],
                'boundary_analysis': boundary_analysis,
                'live_analysis': live_analysis
            }

        else:
            print("✅ Cache boundaries are FRESH and COMPLETE")
            return {
                'status': 'fresh',
                'cache_file': str(latest_cache),
                'boundary_analysis': boundary_analysis,
                'live_analysis': live_analysis
            }

def main():
    if len(sys.argv) < 2:
        print("Usage: python boundary_detector.py <channel> [filter_type]")
        print("Filter types: today, yesterday, last:N, YYYY-MM-DD, all")
        print("Example: python boundary_detector.py @aiclubsweggs today")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    filter_type = sys.argv[2] if len(sys.argv) > 2 else "today"

    try:
        detector = BoundaryFreshnessDetector(channel)
        result = asyncio.run(detector.run_boundary_analysis(filter_type))

        print("\n" + "="*60)
        print("📊 BOUNDARY ANALYSIS RESULTS")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Channel: {channel}")
        print(f"Filter: {filter_type}")

        if result['status'] == 'expanded':
            print(f"📈 Messages added: {result['messages_added']}")
            print(f"📁 New cache: {result['new_cache']}")
        elif result['status'] == 'fresh':
            print("✅ Cache is fresh and complete")

        print("="*60)

    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()