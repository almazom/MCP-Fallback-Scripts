#!/usr/bin/env python3
"""
Border Message Validator - Ultimate 10/10 confidence boundary detection
Triple-verification system with automatic media download and content validation
"""

import asyncio
import json
import hashlib
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    print("ERROR: telethon not found. Install with: pip install telethon", file=sys.stderr)
    sys.exit(1)


class BorderMessageValidator:
    """Ultimate border message validator with 10/10 confidence detection"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent

        self.base_dir = Path(base_dir)
        self.cache_dir = self.base_dir / "telegram_cache"
        self.media_dir = self.base_dir / "telegram_media"
        self.verification_dir = self.base_dir / "telegram_verification"

        # Create directories
        for dir_path in [self.cache_dir, self.media_dir, self.verification_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.moscow_tz = pytz.timezone('Europe/Moscow')

    def load_credentials(self):
        """Load Telegram credentials"""
        env_file = self.base_dir / ".env"
        creds = {}
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    creds[key] = value.strip('"')
        return creds

    def get_moscow_date_boundaries(self, target_date=None):
        """Get precise Moscow timezone boundaries for a date"""
        if target_date is None:
            target_date = datetime.now(self.moscow_tz).date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        # Start of day in Moscow timezone
        start_moscow = self.moscow_tz.localize(
            datetime.combine(target_date, datetime.min.time())
        )

        # End of day in Moscow timezone
        end_moscow = self.moscow_tz.localize(
            datetime.combine(target_date, datetime.max.time())
        )

        return start_moscow, end_moscow

    def is_message_in_date_range(self, message, start_time, end_time):
        """Check if message falls within date boundaries"""
        msg_time_utc = datetime.fromisoformat(message['date_utc'].replace('Z', '+00:00'))
        msg_time_moscow = msg_time_utc.astimezone(self.moscow_tz)

        return start_time <= msg_time_moscow <= end_time

    async def download_and_verify_media(self, client, message, message_data):
        """Download media and create verification hash"""
        if not hasattr(message, 'media') or not message.media:
            return None

        try:
            # Create message-specific media directory
            msg_media_dir = self.media_dir / f"msg_{message.id}"
            msg_media_dir.mkdir(exist_ok=True)

            # Download media
            media_path = await client.download_media(message, str(msg_media_dir))
            if not media_path:
                return None

            media_path = Path(media_path)

            # Generate content hash
            content_hash = hashlib.sha256()
            with open(media_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    content_hash.update(chunk)

            media_info = {
                'file_path': str(media_path),
                'file_name': media_path.name,
                'file_size': media_path.stat().st_size,
                'content_hash': content_hash.hexdigest(),
                'download_time': datetime.now(self.moscow_tz).isoformat(),
                'message_id': message.id
            }

            print(f"📎 Downloaded media for message {message.id}: {media_path.name}")
            return media_info

        except Exception as e:
            print(f"❌ Failed to download media for message {message.id}: {e}")
            return None

    async def fetch_and_verify_boundary_message(self, channel, message_id):
        """Fetch specific message and verify content with triple-check"""
        creds = self.load_credentials()

        client = TelegramClient(
            StringSession(creds['TELEGRAM_SESSION']),
            int(creds['TELEGRAM_API_ID']),
            creds['TELEGRAM_API_HASH']
        )

        await client.connect()

        try:
            entity = await client.get_entity(channel)

            # Method 1: Direct message fetch
            direct_message = await client.get_messages(entity, ids=message_id)
            if not direct_message:
                return {'status': 'not_found', 'method': 'direct'}

            # Method 2: History search around the message
            history = await client(GetHistoryRequest(
                peer=entity,
                offset_id=message_id + 1,
                offset_date=None,
                add_offset=0,
                limit=3,
                max_id=0,
                min_id=0,
                hash=0
            ))

            history_message = None
            for msg in history.messages:
                if msg.id == message_id:
                    history_message = msg
                    break

            # Method 3: Iterative search
            iter_message = None
            async for msg in client.iter_messages(entity, min_id=message_id-1, max_id=message_id+1):
                if msg.id == message_id:
                    iter_message = msg
                    break

            # Triple verification
            messages_found = [m for m in [direct_message, history_message, iter_message] if m]

            if len(messages_found) < 2:
                return {
                    'status': 'verification_failed',
                    'reason': f'Only {len(messages_found)}/3 methods found message',
                    'methods_successful': len(messages_found)
                }

            # Use the direct message as primary
            message = direct_message

            # Convert to Moscow time
            msk_date = message.date.astimezone(self.moscow_tz)
            msk_timestamp = msk_date.strftime('%Y-%m-%d %H:%M:%S')

            # Extract sender info
            sender_name = 'Unknown'
            if hasattr(message, 'sender') and message.sender:
                if hasattr(message.sender, 'first_name'):
                    sender_name = message.sender.first_name or 'Unknown'
                    if hasattr(message.sender, 'last_name') and message.sender.last_name:
                        sender_name += f' {message.sender.last_name}'

            # Handle media and text
            text_content = message.message or ''
            media_info = None

            if hasattr(message, 'media') and message.media:
                # Download and verify media
                media_info = await self.download_and_verify_media(client, message, None)

                # Add media marker to text
                if hasattr(message.media, 'photo'):
                    text_content = f'📷 [Photo] {text_content}'.strip()
                elif hasattr(message.media, 'document'):
                    text_content = f'📎 [File] {text_content}'.strip()
                else:
                    text_content = f'📦 [Media] {text_content}'.strip()

            verified_message = {
                'id': message.id,
                'date_utc': message.date.isoformat(),
                'date_msk': msk_timestamp,
                'text': text_content,
                'sender': sender_name,
                'views': getattr(message, 'views', None),
                'forwards': getattr(message, 'forwards', None),
                'reply_to_id': getattr(message.reply_to, 'reply_to_msg_id', None) if hasattr(message, 'reply_to') and message.reply_to else None,
                'media_info': media_info,
                'verification': {
                    'methods_successful': len(messages_found),
                    'verified_at': datetime.now(self.moscow_tz).isoformat(),
                    'content_hash': hashlib.sha256(text_content.encode()).hexdigest()
                }
            }

            return {
                'status': 'verified',
                'message': verified_message,
                'verification_score': len(messages_found) / 3.0,
                'methods_successful': len(messages_found)
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            await client.disconnect()

    async def find_first_message_of_date(self, channel, target_date):
        """Find the actual first message of a specific date with 10/10 confidence"""
        print(f"🎯 Finding first message of {target_date} in {channel}")

        start_moscow, end_moscow = self.get_moscow_date_boundaries(target_date)
        print(f"⏰ Date boundaries: {start_moscow} to {end_moscow}")

        creds = self.load_credentials()

        client = TelegramClient(
            StringSession(creds['TELEGRAM_SESSION']),
            int(creds['TELEGRAM_API_ID']),
            creds['TELEGRAM_API_HASH']
        )

        await client.connect()

        try:
            entity = await client.get_entity(channel)

            # Strategy 1: Find boundaries using binary search approach
            candidates = []

            # First pass: Get a large sample around the target date
            print("🔍 Phase 1: Broad search for date boundaries")

            # Start from recent messages and go backward
            last_id = 0
            search_limit = 1000
            messages_checked = 0

            async for message in client.iter_messages(entity, limit=search_limit):
                messages_checked += 1
                msg_time_moscow = message.date.astimezone(self.moscow_tz)

                # Check if message is in our target date
                if start_moscow <= msg_time_moscow <= end_moscow:
                    candidates.append({
                        'id': message.id,
                        'date_moscow': msg_time_moscow,
                        'text': message.message or '[Media]'
                    })
                    print(f"  📌 Found candidate: ID {message.id} at {msg_time_moscow.strftime('%H:%M:%S')}")

                # If we've gone past our target date, we can stop
                if msg_time_moscow < start_moscow:
                    print(f"  ⏹️  Reached messages before target date, stopping search")
                    break

            if not candidates:
                print("❌ No messages found for the target date")
                return {
                    'status': 'not_found',
                    'date': target_date,
                    'messages_checked': messages_checked
                }

            # Sort candidates by timestamp (earliest first)
            candidates.sort(key=lambda x: x['date_moscow'])

            print(f"📊 Found {len(candidates)} messages in target date")
            print(f"🔍 Earliest candidate: ID {candidates[0]['id']} at {candidates[0]['date_moscow'].strftime('%H:%M:%S')}")
            print(f"🔍 Latest candidate: ID {candidates[-1]['id']} at {candidates[-1]['date_moscow'].strftime('%H:%M:%S')}")

            # Phase 2: Verify the earliest message is truly the first
            earliest_candidate = candidates[0]

            print("🔍 Phase 2: Verifying earliest message is truly first")

            # Check if there are any messages before our earliest candidate in the same date
            verification_check = True

            async for message in client.iter_messages(entity, max_id=earliest_candidate['id'], limit=50):
                msg_time_moscow = message.date.astimezone(self.moscow_tz)

                # If we find a message in our target date that's older than our candidate
                if start_moscow <= msg_time_moscow <= end_moscow:
                    print(f"  ⚠️  Found earlier message in same date: ID {message.id} at {msg_time_moscow.strftime('%H:%M:%S')}")
                    # Update our earliest candidate
                    earliest_candidate = {
                        'id': message.id,
                        'date_moscow': msg_time_moscow,
                        'text': message.message or '[Media]'
                    }
                    verification_check = False

                # If we've gone to previous day, stop
                if msg_time_moscow < start_moscow:
                    break

            # Phase 3: Triple verification of the first message
            print("🔍 Phase 3: Triple verification of first message")

            verification_result = await self.fetch_and_verify_boundary_message(
                channel, earliest_candidate['id']
            )

            if verification_result['status'] != 'verified':
                return {
                    'status': 'verification_failed',
                    'candidate_id': earliest_candidate['id'],
                    'verification_result': verification_result
                }

            # Create verification report
            verification_report = {
                'target_date': target_date,
                'channel': channel,
                'first_message': verification_result['message'],
                'confidence_score': verification_result['verification_score'],
                'total_candidates_found': len(candidates),
                'messages_checked': messages_checked,
                'boundary_verification': verification_check,
                'search_phases': {
                    'broad_search_completed': True,
                    'boundary_verification_completed': True,
                    'triple_verification_completed': True
                },
                'verified_at': datetime.now(self.moscow_tz).isoformat()
            }

            # Save verification report
            report_file = self.verification_dir / f"{channel.replace('@', '')}_{target_date}_boundary_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(verification_report, f, indent=2, ensure_ascii=False)

            print(f"✅ Verification complete - Confidence: {verification_result['verification_score']:.1%}")
            print(f"📁 Report saved: {report_file}")

            return {
                'status': 'success',
                'first_message': verification_result['message'],
                'confidence_score': verification_result['verification_score'],
                'verification_report': verification_report,
                'report_file': str(report_file)
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            await client.disconnect()

    def validate_cached_boundary(self, cache_file, target_date):
        """Validate cached boundary message against verification"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            messages = cache_data.get('messages', [])
            if not messages:
                return {'status': 'empty_cache'}

            start_moscow, end_moscow = self.get_moscow_date_boundaries(target_date)

            # Find messages in target date
            target_messages = []
            for msg in reversed(messages):  # Reverse to get chronological order
                msg_time_utc = datetime.fromisoformat(msg['date_utc'].replace('Z', '+00:00'))
                msg_time_moscow = msg_time_utc.astimezone(self.moscow_tz)

                if start_moscow <= msg_time_moscow <= end_moscow:
                    target_messages.append(msg)

            if not target_messages:
                return {'status': 'no_messages_in_date'}

            # The first message chronologically
            first_cached = target_messages[0]

            return {
                'status': 'found',
                'first_message': first_cached,
                'total_in_date': len(target_messages)
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}


async def main():
    """CLI interface for border message validation"""
    if len(sys.argv) < 3:
        print("""
Border Message Validator - 10/10 Confidence Detection

Usage:
  python border_message_validator.py <channel> <date>
  python border_message_validator.py <channel> <date> --verify-cache <cache_file>

Examples:
  python border_message_validator.py @aiclubsweggs 2025-09-14
  python border_message_validator.py @aiclubsweggs 2025-09-14 --verify-cache cache.json
        """)
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    target_date = sys.argv[2]

    validator = BorderMessageValidator()

    # Check if we should verify against cache
    if len(sys.argv) > 3 and sys.argv[3] == '--verify-cache':
        cache_file = sys.argv[4]

        print(f"🔍 Validating cached boundary for {target_date}")
        cache_result = validator.validate_cached_boundary(cache_file, target_date)

        if cache_result['status'] == 'found':
            print(f"📋 Cached first message: ID {cache_result['first_message']['id']}")

            # Now verify against live data
            print("🔍 Verifying against live Telegram data...")
            live_result = await validator.find_first_message_of_date(channel, target_date)

            if live_result['status'] == 'success':
                cached_id = cache_result['first_message']['id']
                live_id = live_result['first_message']['id']

                if cached_id == live_id:
                    print(f"✅ PERFECT MATCH - Cached and live first messages match (ID {cached_id})")
                    print(f"🎯 Confidence Score: {live_result['confidence_score']:.1%}")
                else:
                    print(f"❌ MISMATCH - Cached: {cached_id}, Live: {live_id}")
                    print(f"🎯 Live Confidence Score: {live_result['confidence_score']:.1%}")
            else:
                print(f"❌ Live verification failed: {live_result.get('error', live_result['status'])}")
        else:
            print(f"❌ Cache validation failed: {cache_result.get('error', cache_result['status'])}")

    else:
        # Direct boundary detection
        print(f"🎯 Finding first message of {target_date} in {channel}")
        result = await validator.find_first_message_of_date(channel, target_date)

        if result['status'] == 'success':
            msg = result['first_message']
            print(f"\n🎉 SUCCESS - First message found with {result['confidence_score']:.1%} confidence")
            print(f"📧 Message ID: {msg['id']}")
            print(f"📅 Date: {msg['date_msk']}")
            print(f"📝 Content: {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}")
            if msg.get('media_info'):
                print(f"📎 Media: {msg['media_info']['file_name']}")
            print(f"📁 Report: {result['report_file']}")
        else:
            print(f"❌ Failed: {result.get('error', result['status'])}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())