#!/usr/bin/env python3
"""
Boundary Test Suite - Comprehensive testing for border detection accuracy
Tests multiple date boundaries and generates confidence reports
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Add core directory to path
sys.path.append(str(Path(__file__).parent / "core"))

from border_message_validator import BorderMessageValidator


class BoundaryTestSuite:
    """Comprehensive test suite for boundary detection"""

    def __init__(self, channel):
        self.channel = channel
        self.validator = BorderMessageValidator()
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.test_results = []

    def generate_test_dates(self, start_date, num_days=7):
        """Generate list of test dates"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        test_dates = []
        for i in range(num_days):
            test_date = start_date - timedelta(days=i)
            test_dates.append(test_date.strftime('%Y-%m-%d'))

        return test_dates

    async def test_boundary_detection(self, test_date):
        """Test boundary detection for a specific date"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing boundary detection for {test_date}")
        print(f"{'='*60}")

        test_result = {
            'date': test_date,
            'channel': self.channel,
            'test_start_time': datetime.now(self.moscow_tz).isoformat(),
            'status': 'pending',
            'confidence_score': 0.0,
            'verification_methods': 0,
            'media_downloaded': False,
            'content_verified': False,
            'errors': []
        }

        try:
            # Run boundary detection
            result = await self.validator.find_first_message_of_date(self.channel, test_date)

            if result['status'] == 'success':
                first_message = result['first_message']

                test_result.update({
                    'status': 'success',
                    'confidence_score': result['confidence_score'],
                    'verification_methods': first_message['verification']['methods_successful'],
                    'message_id': first_message['id'],
                    'message_time': first_message['date_msk'],
                    'message_content': first_message['text'][:100] + ('...' if len(first_message['text']) > 100 else ''),
                    'media_downloaded': first_message.get('media_info') is not None,
                    'content_verified': True,
                    'content_hash': first_message['verification']['content_hash']
                })

                print(f"✅ SUCCESS - Confidence: {result['confidence_score']:.1%}")
                print(f"📧 Message ID: {first_message['id']}")
                print(f"📅 Time: {first_message['date_msk']}")
                print(f"📝 Content: {test_result['message_content']}")

                if first_message.get('media_info'):
                    print(f"📎 Media: {first_message['media_info']['file_name']}")

            elif result['status'] == 'not_found':
                test_result.update({
                    'status': 'no_messages',
                    'reason': 'No messages found for this date'
                })
                print(f"ℹ️  No messages found for {test_date}")

            else:
                test_result.update({
                    'status': 'failed',
                    'reason': result.get('error', result['status']),
                    'errors': [result.get('error', result['status'])]
                })
                print(f"❌ Failed: {result.get('error', result['status'])}")

        except Exception as e:
            test_result.update({
                'status': 'exception',
                'reason': str(e),
                'errors': [str(e)]
            })
            print(f"💥 Exception: {e}")

        test_result['test_end_time'] = datetime.now(self.moscow_tz).isoformat()
        test_result['test_duration'] = (
            datetime.fromisoformat(test_result['test_end_time']) -
            datetime.fromisoformat(test_result['test_start_time'])
        ).total_seconds()

        self.test_results.append(test_result)
        return test_result

    async def run_cache_validation_tests(self, cache_file):
        """Test validation against existing cache"""
        print(f"\n{'='*60}")
        print(f"🔍 Running cache validation tests")
        print(f"📁 Cache file: {cache_file}")
        print(f"{'='*60}")

        validation_results = []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            messages = cache_data.get('messages', [])
            if not messages:
                return {'status': 'empty_cache', 'results': []}

            # Group messages by date
            messages_by_date = {}
            for msg in messages:
                msg_time_utc = datetime.fromisoformat(msg['date_utc'].replace('Z', '+00:00'))
                msg_time_moscow = msg_time_utc.astimezone(self.moscow_tz)
                date_str = msg_time_moscow.date().strftime('%Y-%m-%d')

                if date_str not in messages_by_date:
                    messages_by_date[date_str] = []
                messages_by_date[date_str].append(msg)

            # Sort messages within each date
            for date_str in messages_by_date:
                messages_by_date[date_str].sort(key=lambda x: datetime.fromisoformat(x['date_utc']))

            print(f"📊 Found messages across {len(messages_by_date)} different dates")

            # Test each date
            for date_str, date_messages in messages_by_date.items():
                print(f"\n🧪 Testing {date_str} ({len(date_messages)} messages)")

                cached_first = date_messages[0]
                print(f"📋 Cached first message: ID {cached_first['id']} at {cached_first['date_msk']}")

                # Validate against live detection
                live_result = await self.validator.find_first_message_of_date(self.channel, date_str)

                validation_result = {
                    'date': date_str,
                    'cached_message_id': cached_first['id'],
                    'cached_message_time': cached_first['date_msk'],
                    'total_cached_messages': len(date_messages),
                    'validation_status': 'pending'
                }

                if live_result['status'] == 'success':
                    live_first = live_result['first_message']
                    validation_result.update({
                        'live_message_id': live_first['id'],
                        'live_message_time': live_first['date_msk'],
                        'live_confidence': live_result['confidence_score']
                    })

                    if cached_first['id'] == live_first['id']:
                        validation_result['validation_status'] = 'match'
                        print(f"✅ MATCH - Cached and live first messages are identical")
                    else:
                        validation_result['validation_status'] = 'mismatch'
                        print(f"❌ MISMATCH - Cached: {cached_first['id']}, Live: {live_first['id']}")
                else:
                    validation_result.update({
                        'validation_status': 'live_failed',
                        'live_error': live_result.get('error', live_result['status'])
                    })
                    print(f"⚠️  Live validation failed: {live_result.get('error', live_result['status'])}")

                validation_results.append(validation_result)

            return {
                'status': 'completed',
                'total_dates_tested': len(messages_by_date),
                'results': validation_results
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'results': validation_results
            }

    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            'test_suite_info': {
                'channel': self.channel,
                'total_tests': len(self.test_results),
                'generated_at': datetime.now(self.moscow_tz).isoformat(),
                'test_suite_version': '1.0'
            },
            'summary': {
                'successful_tests': 0,
                'failed_tests': 0,
                'no_message_tests': 0,
                'average_confidence': 0.0,
                'total_media_downloaded': 0,
                'total_verification_methods': 0
            },
            'detailed_results': self.test_results
        }

        # Calculate summary statistics
        successful_tests = [t for t in self.test_results if t['status'] == 'success']
        failed_tests = [t for t in self.test_results if t['status'] in ['failed', 'exception']]
        no_message_tests = [t for t in self.test_results if t['status'] == 'no_messages']

        report['summary'].update({
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'no_message_tests': len(no_message_tests),
            'average_confidence': sum(t['confidence_score'] for t in successful_tests) / len(successful_tests) if successful_tests else 0.0,
            'total_media_downloaded': sum(1 for t in self.test_results if t.get('media_downloaded', False)),
            'total_verification_methods': sum(t.get('verification_methods', 0) for t in self.test_results)
        })

        return report

    def save_test_report(self, report):
        """Save test report to file"""
        report_dir = Path(__file__).parent.parent / "telegram_verification"
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"{self.channel.replace('@', '')}_boundary_test_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report_file

    async def run_comprehensive_test(self, start_date=None, num_days=7, cache_file=None):
        """Run comprehensive boundary detection tests"""
        print(f"🧪 Starting comprehensive boundary test for {self.channel}")
        print(f"📅 Testing {num_days} days starting from {start_date or 'today'}")

        if start_date is None:
            start_date = datetime.now(self.moscow_tz).date()

        # Generate test dates
        test_dates = self.generate_test_dates(start_date, num_days)
        print(f"📋 Test dates: {', '.join(test_dates)}")

        # Run boundary detection tests
        for test_date in test_dates:
            await self.test_boundary_detection(test_date)

        # Run cache validation if cache file provided
        cache_validation_results = None
        if cache_file and Path(cache_file).exists():
            cache_validation_results = await self.run_cache_validation_tests(cache_file)

        # Generate report
        report = self.generate_test_report()
        if cache_validation_results:
            report['cache_validation'] = cache_validation_results

        # Save report
        report_file = self.save_test_report(report)

        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Successful tests: {report['summary']['successful_tests']}")
        print(f"❌ Failed tests: {report['summary']['failed_tests']}")
        print(f"ℹ️  No messages: {report['summary']['no_message_tests']}")
        print(f"📈 Average confidence: {report['summary']['average_confidence']:.1%}")
        print(f"📎 Media downloaded: {report['summary']['total_media_downloaded']}")
        print(f"🔍 Total verification methods: {report['summary']['total_verification_methods']}")
        print(f"📁 Report saved: {report_file}")

        if cache_validation_results and cache_validation_results['status'] == 'completed':
            matches = sum(1 for r in cache_validation_results['results'] if r['validation_status'] == 'match')
            total = len(cache_validation_results['results'])
            print(f"🔄 Cache validation: {matches}/{total} matches ({matches/total:.1%})")

        return report


async def main():
    """CLI interface for boundary testing"""
    if len(sys.argv) < 2:
        print("""
Boundary Test Suite - Comprehensive Boundary Detection Testing

Usage:
  python test_boundaries.py <channel> [start_date] [num_days] [--cache <file>]

Examples:
  python test_boundaries.py @aiclubsweggs
  python test_boundaries.py @aiclubsweggs 2025-09-14 7
  python test_boundaries.py @aiclubsweggs 2025-09-14 7 --cache cache.json
        """)
        sys.exit(1)

    channel = sys.argv[1]
    if not channel.startswith('@'):
        channel = f'@{channel}'

    start_date = sys.argv[2] if len(sys.argv) > 2 else None
    num_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

    cache_file = None
    if "--cache" in sys.argv:
        cache_index = sys.argv.index("--cache")
        if cache_index + 1 < len(sys.argv):
            cache_file = sys.argv[cache_index + 1]

    try:
        test_suite = BoundaryTestSuite(channel)
        report = await test_suite.run_comprehensive_test(start_date, num_days, cache_file)

        # Calculate overall success rate
        total_tests = report['summary']['successful_tests'] + report['summary']['failed_tests']
        success_rate = report['summary']['successful_tests'] / total_tests if total_tests > 0 else 0.0

        print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.1%}")

        if success_rate >= 0.9:
            print("🏆 EXCELLENT - 10/10 confidence achieved!")
            sys.exit(0)
        elif success_rate >= 0.8:
            print("👍 GOOD - High confidence boundary detection")
            sys.exit(0)
        elif success_rate >= 0.6:
            print("⚠️  FAIR - Some issues detected, review needed")
            sys.exit(1)
        else:
            print("❌ POOR - Significant boundary detection issues")
            sys.exit(1)

    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())