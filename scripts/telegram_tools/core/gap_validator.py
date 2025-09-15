#!/usr/bin/env python3
"""
Gap Validator - Validates message completeness and detects gaps
Implements RTM requirements FR-008, FR-009, TR-008, TR-009
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import pytz
from temporal_anchor import TemporalAnchor
from daily_persistence import DailyPersistence


class GapValidator:
    """Validates message completeness and detects gaps in message sequences"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent.parent / "telegram_cache"

        self.base_dir = Path(base_dir)
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.ta = TemporalAnchor(base_dir)
        self.dp = DailyPersistence(base_dir)

        # Configuration for gap detection
        self.deletion_threshold = 5  # Assume gaps > 5 are deletions, not system issues
        self.max_gap_size = 100      # Report gaps larger than this
        self.min_sequence_length = 10 # Minimum messages needed for reliable validation

    def validate_message_sequence(self, messages):
        """Validate message ID sequence for gaps"""
        if len(messages) < self.min_sequence_length:
            return {
                'valid': True,
                'reason': f'Insufficient messages for validation (need {self.min_sequence_length}, have {len(messages)})',
                'gaps': [],
                'total_gaps': 0,
                'largest_gap': 0
            }

        gaps = []
        message_ids = [msg['id'] for msg in messages]

        # Sort IDs in descending order (Telegram IDs are reverse chronological)
        message_ids.sort(reverse=True)

        for i in range(len(message_ids) - 1):
            current_id = message_ids[i]
            next_id = message_ids[i + 1]

            # Calculate gap size
            gap_size = current_id - next_id - 1

            if gap_size > 0:
                gap_info = {
                    'start_id': next_id,
                    'end_id': current_id,
                    'gap_size': gap_size,
                    'likely_deletions': gap_size <= self.deletion_threshold,
                    'index': i
                }

                # Only report significant gaps
                if gap_size > self.deletion_threshold:
                    gaps.append(gap_info)

        # Determine overall validity
        significant_gaps = [g for g in gaps if not g['likely_deletions']]
        largest_gap = max([g['gap_size'] for g in gaps], default=0)

        is_valid = len(significant_gaps) == 0 or largest_gap <= self.max_gap_size

        return {
            'valid': is_valid,
            'reason': self._get_validation_reason(gaps, significant_gaps, largest_gap),
            'gaps': gaps,
            'total_gaps': len(gaps),
            'largest_gap': largest_gap,
            'sequence_length': len(message_ids),
            'id_range': f"{message_ids[-1]} to {message_ids[0]}" if message_ids else "empty"
        }

    def _get_validation_reason(self, gaps, significant_gaps, largest_gap):
        """Generate human-readable reason for validation result"""
        if not gaps:
            return "No gaps detected in message sequence"

        if not significant_gaps:
            return f"Only minor gaps detected (likely deletions), largest: {largest_gap}"

        if largest_gap > self.max_gap_size:
            return f"Large gap detected ({largest_gap} messages), may indicate data loss"

        return f"{len(significant_gaps)} significant gaps detected, largest: {largest_gap}"

    def validate_daily_boundary(self, channel, messages, target_date):
        """Validate that messages represent complete daily boundary"""
        if not messages:
            return {
                'valid': False,
                'reason': 'No messages provided for boundary validation',
                'boundary_info': None
            }

        # Get messages from target date
        target_date_str = target_date.isoformat()
        daily_messages = [m for m in messages if m['date_msk'].startswith(target_date_str)]

        if not daily_messages:
            return {
                'valid': False,
                'reason': f'No messages found for target date {target_date_str}',
                'boundary_info': None
            }

        # Sort messages chronologically
        daily_messages.sort(key=lambda x: x['date_msk'])

        first_msg = daily_messages[0]
        last_msg = daily_messages[-1]

        # Parse times
        first_time = datetime.strptime(first_msg['date_msk'].split()[1], '%H:%M:%S').time()
        last_time = datetime.strptime(last_msg['date_msk'].split()[1], '%H:%M:%S').time()

        boundary_info = {
            'first_message': {
                'id': first_msg['id'],
                'time': str(first_time),
                'text_preview': first_msg['text'][:50] + '...' if len(first_msg['text']) > 50 else first_msg['text']
            },
            'last_message': {
                'id': last_msg['id'],
                'time': str(last_time),
                'text_preview': last_msg['text'][:50] + '...' if len(last_msg['text']) > 50 else last_msg['text']
            },
            'total_messages': len(daily_messages),
            'time_span': f"{first_time} to {last_time}"
        }

        # Check for anchor validation
        anchor_validation = self._validate_with_anchor(channel, first_msg, target_date)

        return {
            'valid': True,  # We found messages for the target date
            'reason': f'Found {len(daily_messages)} messages from {target_date_str}',
            'boundary_info': boundary_info,
            'anchor_validation': anchor_validation
        }

    def _validate_with_anchor(self, channel, first_message, target_date):
        """Validate first message against temporal anchor"""
        prev_anchor = self.ta.get_previous_day_anchor(channel, target_date)

        if not prev_anchor:
            return {
                'anchor_available': False,
                'validation': 'no_anchor',
                'reason': 'No previous day anchor available for validation'
            }

        # Check if first message is reasonable given the anchor
        anchor_msg_id = prev_anchor['message_id']
        first_msg_id = first_message['id']

        # Messages should have incrementing IDs (but Telegram uses decreasing IDs chronologically)
        # So first message of today should have higher ID than last message of yesterday
        if first_msg_id > anchor_msg_id:
            return {
                'anchor_available': True,
                'validation': 'valid',
                'reason': f'First message ID {first_msg_id} > anchor ID {anchor_msg_id} (correct sequence)',
                'anchor_data': prev_anchor
            }
        else:
            return {
                'anchor_available': True,
                'validation': 'suspicious',
                'reason': f'First message ID {first_msg_id} <= anchor ID {anchor_msg_id} (possible gap)',
                'anchor_data': prev_anchor
            }

    def validate_temporal_continuity(self, channel, messages, target_date):
        """Validate temporal continuity with previous day's data"""
        # Get previous day's cached data
        prev_date = target_date - timedelta(days=1)
        prev_cache = self.dp.get_daily_cache(channel, prev_date)

        if not prev_cache:
            return {
                'continuity_check': 'no_previous_data',
                'reason': f'No cached data available for {prev_date}',
                'gap_detected': False
            }

        prev_messages = prev_cache['messages']
        if not prev_messages:
            return {
                'continuity_check': 'empty_previous_data',
                'reason': f'Previous day cache is empty',
                'gap_detected': False
            }

        # Get last message from previous day
        prev_last_msg = prev_messages[0]  # Messages in reverse chronological order

        # Get first message from current day
        current_date_str = target_date.isoformat()
        current_messages = [m for m in messages if m['date_msk'].startswith(current_date_str)]

        if not current_messages:
            return {
                'continuity_check': 'no_current_data',
                'reason': f'No messages found for current date {current_date_str}',
                'gap_detected': True
            }

        current_messages.sort(key=lambda x: x['date_msk'])
        current_first_msg = current_messages[0]

        # Check ID continuity
        prev_id = prev_last_msg['id']
        current_id = current_first_msg['id']

        # Calculate gap between days
        id_gap = current_id - prev_id - 1

        if id_gap <= self.deletion_threshold:
            return {
                'continuity_check': 'good',
                'reason': f'Good continuity: gap of {id_gap} messages between days',
                'gap_detected': False,
                'gap_size': id_gap,
                'previous_last': prev_last_msg['id'],
                'current_first': current_first_msg['id']
            }
        else:
            return {
                'continuity_check': 'gap_detected',
                'reason': f'Large gap detected: {id_gap} messages between days',
                'gap_detected': True,
                'gap_size': id_gap,
                'previous_last': prev_last_msg['id'],
                'current_first': current_first_msg['id']
            }

    def comprehensive_validation(self, channel, messages, target_date=None):
        """Perform comprehensive validation of message completeness"""
        if target_date is None:
            target_date = datetime.now(self.moscow_tz).date()

        validation_results = {
            'channel': channel,
            'target_date': target_date.isoformat(),
            'validation_timestamp': datetime.now(self.moscow_tz).isoformat(),
            'total_messages': len(messages)
        }

        # 1. Message sequence validation
        sequence_validation = self.validate_message_sequence(messages)
        validation_results['sequence_validation'] = sequence_validation

        # 2. Daily boundary validation
        boundary_validation = self.validate_daily_boundary(channel, messages, target_date)
        validation_results['boundary_validation'] = boundary_validation

        # 3. Temporal continuity validation
        continuity_validation = self.validate_temporal_continuity(channel, messages, target_date)
        validation_results['continuity_validation'] = continuity_validation

        # 4. Overall assessment
        overall_valid = (
            sequence_validation['valid'] and
            boundary_validation['valid'] and
            not continuity_validation['gap_detected']
        )

        confidence_score = self._calculate_confidence_score(
            sequence_validation, boundary_validation, continuity_validation
        )

        validation_results['overall_assessment'] = {
            'valid': overall_valid,
            'confidence_score': confidence_score,
            'confidence_level': self._get_confidence_level(confidence_score),
            'summary': self._generate_summary(sequence_validation, boundary_validation, continuity_validation)
        }

        return validation_results

    def _calculate_confidence_score(self, sequence_val, boundary_val, continuity_val):
        """Calculate confidence score (0-100) for validation results"""
        score = 0

        # Sequence validation (40 points max)
        if sequence_val['valid']:
            if sequence_val['total_gaps'] == 0:
                score += 40
            else:
                # Deduct points based on gap severity
                gap_penalty = min(sequence_val['largest_gap'], 20)
                score += max(40 - gap_penalty, 10)

        # Boundary validation (30 points max)
        if boundary_val['valid']:
            score += 30
            # Bonus for anchor validation
            if boundary_val.get('anchor_validation', {}).get('validation') == 'valid':
                score += 10

        # Continuity validation (30 points max)
        if not continuity_val['gap_detected']:
            score += 30
        elif continuity_val['continuity_check'] == 'no_previous_data':
            score += 15  # Can't verify, but not necessarily bad

        return min(score, 100)

    def _get_confidence_level(self, score):
        """Convert confidence score to human-readable level"""
        if score >= 90:
            return "Very High"
        elif score >= 75:
            return "High"
        elif score >= 60:
            return "Medium"
        elif score >= 40:
            return "Low"
        else:
            return "Very Low"

    def _generate_summary(self, sequence_val, boundary_val, continuity_val):
        """Generate human-readable summary of validation results"""
        issues = []

        if not sequence_val['valid']:
            issues.append(f"Message sequence issues: {sequence_val['reason']}")

        if not boundary_val['valid']:
            issues.append(f"Boundary issues: {boundary_val['reason']}")

        if continuity_val['gap_detected']:
            issues.append(f"Continuity issues: {continuity_val['reason']}")

        if not issues:
            return "All validations passed - data appears complete and accurate"
        else:
            return f"Issues detected: {'; '.join(issues)}"


def main():
    """CLI interface for gap validation operations"""
    import sys

    if len(sys.argv) < 3:
        print("""
Gap Validator

Usage:
  python gap_validator.py validate <channel> [cache_file]
  python gap_validator.py sequence <cache_file>
  python gap_validator.py boundary <channel> <cache_file> [date]
  python gap_validator.py continuity <channel> [date]

Examples:
  python gap_validator.py validate @aiclubsweggs
  python gap_validator.py sequence telegram_cache/aiclubsweggs_latest.json
  python gap_validator.py boundary @aiclubsweggs cache_file.json 2025-09-15
  python gap_validator.py continuity @aiclubsweggs 2025-09-15
        """)
        sys.exit(1)

    gv = GapValidator()
    command = sys.argv[1]

    if command == "validate":
        channel = sys.argv[2]
        if not channel.startswith('@'):
            channel = f'@{channel}'

        # Find latest cache file if not specified
        if len(sys.argv) > 3:
            cache_file = sys.argv[3]
        else:
            # Find latest cache file
            clean_channel = channel.replace('@', '').replace('/', '_')
            cache_files = sorted(gv.base_dir.glob(f"{clean_channel}_*.json"))
            if not cache_files:
                print(f"❌ No cache files found for {channel}")
                sys.exit(1)
            cache_file = cache_files[-1]

        # Load messages
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            messages = cache_data['messages']
        except Exception as e:
            print(f"❌ Failed to load cache file: {e}")
            sys.exit(1)

        # Perform comprehensive validation
        results = gv.comprehensive_validation(channel, messages)

        # Display results
        print(f"Gap Validation Results for {channel}")
        print("=" * 50)
        print(f"Date: {results['target_date']}")
        print(f"Total Messages: {results['total_messages']}")
        print()

        overall = results['overall_assessment']
        print(f"Overall Assessment: {'✅ VALID' if overall['valid'] else '❌ ISSUES DETECTED'}")
        print(f"Confidence: {overall['confidence_score']}/100 ({overall['confidence_level']})")
        print(f"Summary: {overall['summary']}")
        print()

        # Detailed results
        seq = results['sequence_validation']
        print(f"Sequence Validation: {'✅' if seq['valid'] else '❌'}")
        print(f"  {seq['reason']}")
        if seq['gaps']:
            print(f"  Gaps: {seq['total_gaps']}, Largest: {seq['largest_gap']}")

        bound = results['boundary_validation']
        print(f"Boundary Validation: {'✅' if bound['valid'] else '❌'}")
        print(f"  {bound['reason']}")

        cont = results['continuity_validation']
        print(f"Continuity Validation: {'✅' if not cont['gap_detected'] else '❌'}")
        print(f"  {cont['reason']}")

        sys.exit(0 if overall['valid'] else 1)

    elif command == "sequence":
        cache_file = sys.argv[2]

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            messages = cache_data['messages']
        except Exception as e:
            print(f"❌ Failed to load cache file: {e}")
            sys.exit(1)

        results = gv.validate_message_sequence(messages)
        print(f"Sequence Validation: {'✅ Valid' if results['valid'] else '❌ Invalid'}")
        print(f"Reason: {results['reason']}")
        print(f"Message range: {results.get('id_range', 'N/A')}")
        print(f"Total gaps: {results['total_gaps']}")
        print(f"Largest gap: {results['largest_gap']}")

        if results['gaps']:
            print("\nDetected gaps:")
            for gap in results['gaps']:
                print(f"  Gap: {gap['gap_size']} messages between {gap['start_id']} and {gap['end_id']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()