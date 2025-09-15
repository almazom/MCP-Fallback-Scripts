#!/usr/bin/env python3
"""
Telegram Fetch Large - Fetch more than 100 messages using pagination
Fetches messages in batches to bypass API limits
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("ERROR: telethon not found. Install with: pip install telethon", file=sys.stderr)
    sys.exit(1)

async def fetch_large_batch(channel, total_limit=1000):
    """Fetch messages in batches to get more than 100 messages"""

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

    all_messages = []
    offset_id = 0
    batch_size = 100  # Telegram API limit per request

    print(f"🔄 Fetching {total_limit} messages in batches of {batch_size}...")

    while len(all_messages) < total_limit:
        remaining = total_limit - len(all_messages)
        current_limit = min(batch_size, remaining)

        print(f"📥 Batch {len(all_messages)//batch_size + 1}: fetching {current_limit} messages...")

        # Fetch batch
        history = await client(GetHistoryRequest(
            peer=entity,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=current_limit,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            print(f"📭 No more messages available. Got {len(all_messages)} total.")
            break

        # Process messages
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
            all_messages.append(msg_data)

        # Set offset for next batch (use the ID of the oldest message we got)
        if history.messages:
            offset_id = history.messages[-1].id

        print(f"✅ Got {len(history.messages)} messages (total: {len(all_messages)})")

        # Break if we got less than requested (no more messages)
        if len(history.messages) < current_limit:
            print(f"📭 Reached end of available messages. Got {len(all_messages)} total.")
            break

    # Save to cache
    cache_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"
    cache_dir.mkdir(exist_ok=True)

    clean_channel = channel.replace('@', '').replace('/', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cache_file = cache_dir / f"{clean_channel}_large_{timestamp}.json"

    cache_data = {
        'meta': {
            'channel': channel,
            'cached_at': datetime.now().isoformat(),
            'total_messages': len(all_messages),
            'limit_requested': total_limit,
            'fetch_method': 'large_batch'
        },
        'messages': all_messages
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    await client.disconnect()

    print(f"🎉 Successfully cached {len(all_messages)} messages from {channel}")
    print(f"📁 Cache file: {cache_file}")
    return str(cache_file)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python telegram_fetch_large.py <channel> [limit]")
        print("Example: python telegram_fetch_large.py aiclubsweggs 1000")
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    try:
        await fetch_large_batch(channel, limit)
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())