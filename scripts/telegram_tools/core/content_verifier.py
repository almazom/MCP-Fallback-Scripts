#!/usr/bin/env python3
"""
Content Verifier - Advanced verification for telegram message content
Ensures cache consistency and detects content mismatches
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
except ImportError:
    print("ERROR: telethon not found. Install with: pip install telethon", file=sys.stderr)
    sys.exit(1)


class ContentVerifier:
    """Advanced content verification system"""

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

    def calculate_content_hash(self, content):
        """Calculate hash for content verification"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()

    def verify_media_file(self, media_info):
        """Verify media file exists and matches hash"""
        if not media_info:
            return {'status': 'no_media', 'verified': True}

        file_path = Path(media_info.get('file_path', ''))
        expected_hash = media_info.get('content_hash')

        if not file_path.exists():
            return {
                'status': 'file_missing',
                'verified': False,
                'expected_path': str(file_path)
            }

        if not expected_hash:
            return {
                'status': 'no_hash',
                'verified': False,
                'message': 'No content hash stored for verification'
            }

        # Calculate actual file hash
        actual_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    actual_hash.update(chunk)

            actual_hash_str = actual_hash.hexdigest()

            if actual_hash_str == expected_hash:
                return {
                    'status': 'verified',
                    'verified': True,
                    'file_size': file_path.stat().st_size,
                    'hash_match': True
                }
            else:
                return {
                    'status': 'hash_mismatch',
                    'verified': False,
                    'expected_hash': expected_hash,
                    'actual_hash': actual_hash_str
                }

        except Exception as e:
            return {
                'status': 'verification_error',
                'verified': False,
                'error': str(e)
            }

    async def verify_message_against_live(self, client, channel, message_data):
        """Verify cached message against live Telegram data"""
        try:
            entity = await client.get_entity(channel)
            live_message = await client.get_messages(entity, ids=message_data['id'])

            if not live_message:
                return {
                    'status': 'not_found',
                    'verified': False,
                    'message': f"Message {message_data['id']} not found in live data"
                }

            # Compare basic metadata
            live_date = live_message.date.isoformat()
            cached_date = message_data['date_utc']

            # Normalize dates for comparison
            if cached_date.endswith('Z'):
                cached_date = cached_date[:-1] + '+00:00'

            date_match = live_date == cached_date

            # Compare content
            live_content = live_message.message or ''
            cached_content = message_data.get('text', '')

            # Remove media markers for content comparison
            for marker in ['📷 [Photo]', '📎 [File]', '📦 [Media]']:
                cached_content = cached_content.replace(marker, '').strip()

            content_match = live_content == cached_content

            # Compare views if available
            views_match = True
            if hasattr(live_message, 'views') and live_message.views is not None:
                views_match = live_message.views == message_data.get('views')

            verification_result = {
                'status': 'compared',
                'verified': date_match and content_match,
                'message_id': message_data['id'],
                'comparisons': {
                    'date_match': date_match,
                    'content_match': content_match,
                    'views_match': views_match
                },
                'live_data': {
                    'date': live_date,
                    'content': live_content[:100] + ('...' if len(live_content) > 100 else ''),
                    'views': getattr(live_message, 'views', None)
                },
                'cached_data': {
                    'date': cached_date,
                    'content': cached_content[:100] + ('...' if len(cached_content) > 100 else ''),
                    'views': message_data.get('views')
                }
            }

            if not verification_result['verified']:
                verification_result['discrepancies'] = []
                if not date_match:
                    verification_result['discrepancies'].append('date_mismatch')
                if not content_match:
                    verification_result['discrepancies'].append('content_mismatch')
                if not views_match:
                    verification_result['discrepancies'].append('views_mismatch')

            return verification_result

        except Exception as e:
            return {
                'status': 'error',
                'verified': False,
                'error': str(e)
            }

    async def verify_cache_file(self, cache_file, sample_size=10, verify_media=True):
        """Verify cache file against live Telegram data"""
        print(f"🔍 Verifying cache file: {cache_file}")

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            messages = cache_data.get('messages', [])
            channel = cache_data.get('meta', {}).get('channel', '@unknown')

            if not messages:
                return {
                    'status': 'empty_cache',
                    'verified': False,
                    'message': 'Cache file is empty'
                }

            print(f"📊 Cache contains {len(messages)} messages from {channel}")

            # Select sample messages for verification
            if len(messages) <= sample_size:
                sample_messages = messages
            else:
                # Take messages from beginning, middle, and end
                step = len(messages) // sample_size
                sample_messages = messages[::step][:sample_size]

            print(f"🧪 Verifying {len(sample_messages)} sample messages")

            # Load credentials and connect
            creds = self.load_credentials()
            client = TelegramClient(
                StringSession(creds['TELEGRAM_SESSION']),
                int(creds['TELEGRAM_API_ID']),
                creds['TELEGRAM_API_HASH']
            )

            await client.connect()

            verification_results = []

            try:
                for i, message in enumerate(sample_messages, 1):
                    print(f"🔍 Verifying message {i}/{len(sample_messages)}: ID {message['id']}")

                    # Verify against live data
                    live_verification = await self.verify_message_against_live(client, channel, message)

                    # Verify media if present and requested
                    media_verification = {'status': 'no_media', 'verified': True}
                    if verify_media and message.get('media_info'):
                        media_verification = self.verify_media_file(message['media_info'])

                    result = {
                        'message_id': message['id'],
                        'message_date': message['date_msk'],
                        'live_verification': live_verification,
                        'media_verification': media_verification,
                        'overall_verified': live_verification['verified'] and media_verification['verified']
                    }

                    verification_results.append(result)

                    status_emoji = "✅" if result['overall_verified'] else "❌"
                    print(f"  {status_emoji} Message {message['id']}: {'VERIFIED' if result['overall_verified'] else 'FAILED'}")

            finally:
                await client.disconnect()

            # Calculate summary statistics
            total_verified = sum(1 for r in verification_results if r['overall_verified'])
            verification_rate = total_verified / len(verification_results) if verification_results else 0.0

            summary = {
                'total_messages_in_cache': len(messages),
                'messages_verified': len(verification_results),
                'successful_verifications': total_verified,
                'failed_verifications': len(verification_results) - total_verified,
                'verification_rate': verification_rate,
                'sample_size': len(sample_messages)
            }

            verification_report = {
                'cache_file': str(cache_file),
                'channel': channel,
                'verification_timestamp': datetime.now(self.moscow_tz).isoformat(),
                'summary': summary,
                'detailed_results': verification_results,
                'status': 'completed' if verification_rate >= 0.9 else 'issues_detected',
                'verified': verification_rate >= 0.9
            }

            # Save verification report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.verification_dir / f"content_verification_{channel.replace('@', '')}_{timestamp}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(verification_report, f, indent=2, ensure_ascii=False)

            print(f"\n📊 VERIFICATION SUMMARY")
            print(f"✅ Verified: {total_verified}/{len(verification_results)} ({verification_rate:.1%})")
            print(f"📁 Report saved: {report_file}")

            return verification_report

        except Exception as e:
            return {
                'status': 'error',
                'verified': False,
                'error': str(e)
            }

    async def auto_correct_cache(self, cache_file, verification_report):
        """Attempt to auto-correct cache inconsistencies"""
        if verification_report['verified']:
            print("✅ Cache is already verified, no corrections needed")
            return {'status': 'no_corrections_needed'}

        print("🔧 Attempting to auto-correct cache inconsistencies...")

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            messages = cache_data.get('messages', [])
            channel = cache_data.get('meta', {}).get('channel', '@unknown')
            corrections_made = 0

            # Load credentials and connect
            creds = self.load_credentials()
            client = TelegramClient(
                StringSession(creds['TELEGRAM_SESSION']),
                int(creds['TELEGRAM_API_ID']),
                creds['TELEGRAM_API_HASH']
            )

            await client.connect()

            try:
                # Find messages that failed verification
                failed_verifications = [
                    r for r in verification_report['detailed_results']
                    if not r['overall_verified']
                ]

                for failed in failed_verifications:
                    message_id = failed['message_id']
                    print(f"🔧 Correcting message {message_id}")

                    # Find message in cache
                    message_index = None
                    for i, msg in enumerate(messages):
                        if msg['id'] == message_id:
                            message_index = i
                            break

                    if message_index is None:
                        continue

                    # Fetch fresh data from Telegram
                    entity = await client.get_entity(channel)
                    live_message = await client.get_messages(entity, ids=message_id)

                    if live_message:
                        # Update cached message with fresh data
                        msk_date = live_message.date.astimezone(self.moscow_tz)
                        msk_timestamp = msk_date.strftime('%Y-%m-%d %H:%M:%S')

                        messages[message_index].update({
                            'date_utc': live_message.date.isoformat(),
                            'date_msk': msk_timestamp,
                            'text': live_message.message or '',
                            'views': getattr(live_message, 'views', None),
                            'forwards': getattr(live_message, 'forwards', None)
                        })

                        corrections_made += 1
                        print(f"  ✅ Corrected message {message_id}")

            finally:
                await client.disconnect()

            if corrections_made > 0:
                # Save corrected cache
                corrected_cache_file = Path(cache_file).with_suffix('.corrected.json')

                # Update metadata
                cache_data['meta']['corrections_applied'] = corrections_made
                cache_data['meta']['corrected_at'] = datetime.now(self.moscow_tz).isoformat()
                cache_data['meta']['original_file'] = str(cache_file)

                with open(corrected_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Applied {corrections_made} corrections")
                print(f"📁 Corrected cache saved: {corrected_cache_file}")

                return {
                    'status': 'corrections_applied',
                    'corrections_made': corrections_made,
                    'corrected_file': str(corrected_cache_file)
                }
            else:
                return {
                    'status': 'no_corrections_possible',
                    'message': 'Could not correct any inconsistencies'
                }

        except Exception as e:
            return {
                'status': 'correction_error',
                'error': str(e)
            }

    def find_latest_cache_file(self, channel):
        """Find the latest cache file for a channel"""
        clean_channel = channel.replace('@', '')
        cache_files = list(self.cache_dir.glob(f"{clean_channel}_*.json"))

        if not cache_files:
            return None

        # Sort by modification time, newest first
        cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return cache_files[0]


async def main():
    """CLI interface for content verification"""
    if len(sys.argv) < 2:
        print("""
Content Verifier - Advanced Cache Verification System

Usage:
  python content_verifier.py <cache_file> [--sample-size N] [--no-media] [--auto-correct]
  python content_verifier.py --channel <channel> [--sample-size N] [--no-media] [--auto-correct]

Examples:
  python content_verifier.py cache.json
  python content_verifier.py cache.json --sample-size 20 --no-media
  python content_verifier.py --channel @aiclubsweggs --auto-correct
        """)
        sys.exit(1)

    verifier = ContentVerifier()

    # Parse arguments
    cache_file = None
    channel = None
    sample_size = 10
    verify_media = True
    auto_correct = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--channel':
            channel = sys.argv[i + 1]
            if not channel.startswith('@'):
                channel = f'@{channel}'
            i += 2
        elif arg == '--sample-size':
            sample_size = int(sys.argv[i + 1])
            i += 2
        elif arg == '--no-media':
            verify_media = False
            i += 1
        elif arg == '--auto-correct':
            auto_correct = True
            i += 1
        else:
            cache_file = arg
            i += 1

    # Determine cache file
    if channel and not cache_file:
        cache_file = verifier.find_latest_cache_file(channel)
        if not cache_file:
            print(f"❌ No cache files found for {channel}")
            sys.exit(1)
        print(f"📁 Using latest cache file: {cache_file}")

    if not cache_file:
        print("❌ No cache file specified")
        sys.exit(1)

    if not Path(cache_file).exists():
        print(f"❌ Cache file not found: {cache_file}")
        sys.exit(1)

    try:
        # Run verification
        verification_report = await verifier.verify_cache_file(
            cache_file, sample_size, verify_media
        )

        if verification_report['status'] == 'error':
            print(f"❌ Verification failed: {verification_report['error']}")
            sys.exit(1)

        # Auto-correct if requested and verification failed
        if auto_correct and not verification_report['verified']:
            correction_result = await verifier.auto_correct_cache(cache_file, verification_report)
            if correction_result['status'] == 'corrections_applied':
                print(f"🔧 Applied {correction_result['corrections_made']} corrections")
            else:
                print(f"⚠️  Auto-correction: {correction_result['status']}")

        # Determine exit code based on verification rate
        verification_rate = verification_report['summary']['verification_rate']

        if verification_rate >= 0.95:
            print("🏆 EXCELLENT - 10/10 verification confidence!")
            sys.exit(0)
        elif verification_rate >= 0.9:
            print("✅ GOOD - High verification confidence")
            sys.exit(0)
        elif verification_rate >= 0.8:
            print("⚠️  FAIR - Some verification issues detected")
            sys.exit(1)
        else:
            print("❌ POOR - Significant verification failures")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())