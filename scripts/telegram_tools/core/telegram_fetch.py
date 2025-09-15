#!/usr/bin/env python3
"""
Telegram Fetch - Simple JSON caching for messages
30 lines - fetch messages from Telegram and cache as JSON
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytz
from temporal_anchor import TemporalAnchor
from daily_persistence import DailyPersistence

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("ERROR: telethon not found. Install with: pip install telethon", file=sys.stderr)
    sys.exit(1)

async def fetch_and_cache(channel, limit=100, offset_id=0, suffix="", use_anchor=True):
    """Fetch messages and save to cache with full metadata

    Args:
        channel: Telegram channel to fetch from
        limit: Maximum number of messages to fetch
        offset_id: Message ID to start from (0 for latest)
        suffix: Suffix for cache filename
        use_anchor: Whether to use temporal anchoring for smart offset
    """

    # Initialize temporal anchor and daily persistence
    ta = TemporalAnchor()
    dp = DailyPersistence()
    moscow_tz = pytz.timezone('Europe/Moscow')

    # Determine optimal offset using temporal anchoring
    actual_offset_id = offset_id
    fetch_strategy = "manual"

    if use_anchor and offset_id == 0:
        # Use temporal anchoring to calculate best offset
        offset_info = ta.calculate_fetch_offset(channel)
        actual_offset_id = offset_info['offset_id']
        fetch_strategy = offset_info['strategy']

        print(f"🎯 Temporal Anchoring: {offset_info['reason']}")
        if offset_info['anchor_data']:
            anchor = offset_info['anchor_data']
            print(f"   Using anchor: message {anchor['message_id']} from {anchor['date']} at {anchor['timestamp']}")

    # Load credentials from unified .env file
    env_file = Path(__file__).parent.parent.parent.parent / ".env"
    creds = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                creds[key] = value.strip('"')

    # Connect to Telegram
    client = TelegramClient(
        StringSession(creds['TELEGRAM_SESSION']),
        int(creds['TELEGRAM_API_ID']),
        creds['TELEGRAM_API_HASH']
    )

    await client.connect()
    entity = await client.get_entity(channel)

    # Use GetHistoryRequest for full metadata
    history = await client(GetHistoryRequest(
        peer=entity,
        offset_id=actual_offset_id,
        offset_date=None,
        add_offset=0,
        limit=limit,
        max_id=0,
        min_id=0,
        hash=0
    ))

    # Convert to JSON with Moscow time
    messages_data = []
    for message in history.messages:
        # Convert to Moscow time (UTC+3)
        msk_date = message.date.astimezone(moscow_tz)
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
        messages_data.append(msg_data)

    # Save to cache
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    cache_dir.mkdir(exist_ok=True)

    clean_channel = channel.replace('@', '').replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix_part = f"_{suffix}" if suffix else ""
    cache_file = cache_dir / f"{clean_channel}_{timestamp}{suffix_part}.json"

    cache_data = {
        'meta': {
            'channel': channel,
            'cached_at': datetime.now(moscow_tz).isoformat(),
            'total_messages': len(messages_data),
            'limit_requested': limit,
            'offset_id': actual_offset_id,
            'original_offset_id': offset_id,
            'fetch_strategy': fetch_strategy,
            'suffix': suffix,
            'temporal_anchor_version': '1.0'
        },
        'messages': messages_data
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    await client.disconnect()

    # Update temporal anchor if we fetched current day's data
    if use_anchor and messages_data:
        current_date = datetime.now(moscow_tz).date()
        anchor_updated = ta.update_anchor_from_messages(channel, messages_data, current_date)
        if anchor_updated:
            print(f"🔗 Updated temporal anchor for {channel}")

    print(f"✅ Cached {len(messages_data)} messages from {channel}")
    print(f"📁 Cache file: {cache_file}")
    if fetch_strategy != "manual":
        print(f"🎯 Fetch strategy: {fetch_strategy}")
    return str(cache_file)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_fetch.py <channel> [limit] [offset_id] [suffix] [--no-anchor]")
        print("Example: python telegram_fetch.py aiclubsweggs 100")
        print("Example: python telegram_fetch.py aiclubsweggs 100 72857 older")
        print("Example: python telegram_fetch.py aiclubsweggs 100 0 today --no-anchor")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    offset_id = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    suffix = sys.argv[4] if len(sys.argv) > 4 else ""

    # Check for --no-anchor flag
    use_anchor = True
    if "--no-anchor" in sys.argv:
        use_anchor = False

    try:
        await fetch_and_cache(channel, limit, offset_id, suffix, use_anchor)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())