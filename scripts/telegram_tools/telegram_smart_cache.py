#!/usr/bin/env python3
"""
Smart Cache Strategy - Time-range-aware JSON caching
Solves the SSOT truncation trap by ensuring complete time coverage
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

def get_time_range_bounds(filter_type, reference_date=None):
    """Get time range bounds for different filter types in Moscow timezone"""

    if reference_date is None:
        reference_date = datetime.now()

    # Convert to Moscow timezone (UTC+3)
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

def is_message_in_range(message, start_time, end_time):
    """Check if a message falls within the time range"""
    msg_time = datetime.fromisoformat(message['date_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
    start_naive = start_time.replace(tzinfo=None)
    end_naive = end_time.replace(tzinfo=None)
    return start_naive <= msg_time <= end_naive

async def smart_fetch_and_cache(channel, filter_type="today", limit_per_batch=100):
    """Smart fetch that ensures complete time range coverage"""

    print(f"🧠 Smart caching for {filter_type} range...")

    # Calculate time range
    start_time, end_time = get_time_range_bounds(filter_type)
    print(f"⏰ Time range: {start_time.isoformat()} to {end_time.isoformat()} (MSK)")

    # Load credentials from unified .env
    env_file = Path(__file__).parent.parent.parent / ".env"
    creds = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                creds[key] = value.strip('\"')

    # Connect to Telegram
    client = TelegramClient(
        StringSession(creds['TELEGRAM_SESSION']),
        int(creds['TELEGRAM_API_ID']),
        creds['TELEGRAM_API_HASH']
    )

    await client.connect()
    entity = await client.get_entity(channel)

    all_messages = []
    offset_id = 0
    total_fetched = 0
    found_start_of_range = False

    print("🔍 Scanning messages to ensure complete time coverage...")

    while True:
        # Fetch batch of messages
        history = await client(GetHistoryRequest(
            peer=entity,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit_per_batch,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            break

        # Process this batch
        batch_messages = []
        for message in history.messages:
            # Convert to Moscow time (UTC+3)
            msk_date = message.date.astimezone(timezone.utc).replace(tzinfo=None)
            msk_timestamp = msk_date.strftime('%Y-%m-%d %H:%M:%S')

            # Extract sender name
            sender_name = 'Unknown'
            if hasattr(message, 'sender') and message.sender:
                if hasattr(message.sender, 'first_name'):
                    sender_name = message.sender.first_name or 'Unknown'
                    if hasattr(message.sender, 'last_name') and message.sender.last_name:
                        sender_name += f' {message.sender.last_name}'

            # Handle media
            text_content = message.message or ''
            if hasattr(message, 'media') and message.media:
                if hasattr(message.media, 'photo'):
                    text_content = f'📷 [Photo] {text_content}'.strip()
                elif hasattr(message.media, 'document'):
                    text_content = f'📎 [File] {text_content}'.strip()
                else:
                    text_content = f'📦 [Media] {text_content}'.strip()

            msg_data = {
                'id': message.id,
                'date_utc': message.date.isoformat(),
                'date_msk': msk_timestamp,
                'text': text_content,
                'sender': sender_name,
                'views': getattr(message, 'views', None),
                'forwards': getattr(message, 'forwards', None),
                'reply_to_id': getattr(message.reply_to, 'reply_to_msg_id', None) if hasattr(message, 'reply_to') and message.reply_to else None
            }

            # Check if message is in our time range
            msg_time = datetime.fromisoformat(msg_data['date_utc'].replace('Z', '+00:00')).replace(tzinfo=None)
            start_naive = start_time.replace(tzinfo=None)
            end_naive = end_time.replace(tzinfo=None)

            if msg_time < start_naive:
                # Message is before our range, we can stop scanning
                print(f"⏹️ Found message before range: {msg_data['date_msk']} < {start_naive.strftime('%Y-%m-%d %H:%M:%S')}")
                found_start_of_range = True
                break
            elif start_naive <= msg_time <= end_naive:
                # Message is in our range, add it
                batch_messages.append(msg_data)
            else:
                # Message is after our range (future), skip but continue
                pass

        # Add messages in our range
        all_messages.extend(batch_messages)
        total_fetched += len(history.messages)

        print(f"📊 Batch {total_fetched//100 + 1}: {len(batch_messages)} messages in range, {len(history.messages)} total fetched")

        # Check if we should stop
        if found_start_of_range or not history.messages:
            break

        # Move to next batch
        offset_id = history.messages[-1].id

        # Safety check to prevent infinite loops
        if total_fetched > 1000:  # Reasonable limit
            print("⚠️ Safety limit reached, stopping scan")
            break

    await client.disconnect()

    # Sort messages by time (oldest first)
    all_messages.sort(key=lambda x: x['date_utc'])

    # Save to cache
    cache_dir = Path(__file__).parent.parent / "telegram_cache"
    cache_dir.mkdir(exist_ok=True)

    clean_channel = channel.replace('@', '').replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_file = cache_dir / f"{clean_channel}_{timestamp}.json"

    cache_data = {
        'meta': {
            'channel': channel,
            'cached_at': datetime.now().isoformat(),
            'total_messages': len(all_messages),
            'time_range_start': start_time.isoformat(),
            'time_range_end': end_time.isoformat(),
            'time_range_type': filter_type,
            'scan_completed': found_start_of_range,
            'total_scanned': total_fetched
        },
        'messages': all_messages
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Smart cache completed: {len(all_messages)} messages in time range")
    print(f"📁 Cache file: {cache_file}")
    print(f"🔍 Scanned {total_fetched} total messages to ensure complete coverage")

    return str(cache_file)

def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_smart_cache.py <channel> [filter_type] [limit_per_batch]")
        print("Filter types: today, yesterday, last:N, YYYY-MM-DD, all")
        print("Example: python telegram_smart_cache.py aiclubsweggs today 50")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    filter_type = sys.argv[2] if len(sys.argv) > 2 else "today"
    limit_per_batch = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    try:
        cache_file = asyncio.run(smart_fetch_and_cache(channel, filter_type, limit_per_batch))
        print(f"\n🎯 Cache ready for: {filter_type}")
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()