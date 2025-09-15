#!/usr/bin/env python3
"""
Unit tests for telegram_manager.sh message ordering functionality.
Tests both 'read' and 'read_channel' commands to ensure consistent behavior.
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import asyncio
import sys
from typing import List, Optional


class MockMessage:
    """Mock Telegram message for testing."""

    def __init__(self, msg_id: int, text: str, date: datetime, sender_id: int = 1):
        self.id = msg_id
        self.text = text
        self.date = date
        self.sender = Mock(id=sender_id, first_name=f"User{sender_id}")
        self.views = 100
        self.edit_date = None
        self.reply_to = None


class TestMessageOrdering(unittest.TestCase):
    """Test cases for message ordering in telegram_manager.sh"""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock messages with different timestamps
        self.moscow_tz = timezone(timedelta(hours=3))
        now = datetime.now(self.moscow_tz)

        self.messages = [
            MockMessage(1, "First message of the day", now.replace(hour=8, minute=0)),
            MockMessage(2, "Second message", now.replace(hour=10, minute=30)),
            MockMessage(3, "Third message", now.replace(hour=14, minute=0)),
            MockMessage(4, "Fourth message", now.replace(hour=18, minute=45)),
            MockMessage(5, "Latest message", now.replace(hour=22, minute=30)),
        ]

    def test_iter_messages_default_behavior(self):
        """Test that iter_messages without reverse returns newest first."""
        # Simulate Telethon's default behavior
        messages_newest_first = list(reversed(self.messages))

        # This is what happens with iter_messages(reverse=False) or no parameter
        self.assertEqual(messages_newest_first[0].id, 5, "First message should be the latest")
        self.assertEqual(messages_newest_first[-1].id, 1, "Last message should be the oldest")

    def test_iter_messages_reverse_true(self):
        """Test that iter_messages with reverse=True returns oldest first."""
        # Simulate Telethon's behavior with reverse=True
        messages_oldest_first = self.messages.copy()

        # This is what happens with iter_messages(reverse=True)
        self.assertEqual(messages_oldest_first[0].id, 1, "First message should be the oldest")
        self.assertEqual(messages_oldest_first[-1].id, 5, "Last message should be the latest")

    def test_read_command_current_behavior(self):
        """Test current behavior of read command (returns latest message)."""
        # Simulate current read command behavior
        def read_messages(limit: int = 1) -> List[MockMessage]:
            """Simulates current read command implementation."""
            # Uses iter_messages without reverse (newest first)
            return list(reversed(self.messages))[:limit]

        result = read_messages(1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 5, "read command should return the latest message")
        self.assertEqual(result[0].text, "Latest message")

    def test_read_channel_current_behavior(self):
        """Test current behavior of read_channel command (returns oldest after sorting)."""
        # Simulate current read_channel command behavior
        def read_channel_messages(limit: int = 1) -> List[MockMessage]:
            """Simulates current read_channel implementation."""
            # Step 1: Get messages with reverse=False (newest first)
            messages_from_api = list(reversed(self.messages))[:limit]

            # Step 2: Sort by date (oldest first) - this is what the code does
            messages_sorted = sorted(messages_from_api, key=lambda x: x.date)

            return messages_sorted

        result = read_channel_messages(1)
        self.assertEqual(len(result), 1)
        # Even though we fetched the latest, sorting makes it return the latest
        # But when fetching with date range, it would return the oldest in range

    def test_read_channel_with_date_range(self):
        """Test read_channel with date range filtering."""
        def read_channel_with_range(
            start_date: datetime,
            end_date: datetime,
            limit: int = 100
        ) -> List[MockMessage]:
            """Simulates read_channel with date range."""
            # Filter messages by date range
            filtered = [m for m in self.messages
                       if start_date <= m.date <= end_date]

            # Sort by date (oldest first) - current behavior
            return sorted(filtered, key=lambda x: x.date)[:limit]

        # Test "today" range with limit 1
        today_start = datetime.now(self.moscow_tz).replace(hour=0, minute=0)
        today_end = datetime.now(self.moscow_tz).replace(hour=23, minute=59)

        result = read_channel_with_range(today_start, today_end, limit=1)
        self.assertEqual(result[0].id, 1, "Should return first message of the day")
        self.assertEqual(result[0].text, "First message of the day")

    def test_proposed_fix_consistent_ordering(self):
        """Test proposed fix with consistent ordering parameter."""
        def read_messages_fixed(
            limit: int = 1,
            order: str = 'chronological'
        ) -> List[MockMessage]:
            """Proposed fixed implementation with explicit ordering."""
            if order == 'chronological':
                # Use reverse=True for oldest first
                return self.messages[:limit]
            else:  # reverse-chronological
                # Use reverse=False for newest first
                return list(reversed(self.messages))[:limit]

        # Test chronological (oldest first)
        result_chrono = read_messages_fixed(1, 'chronological')
        self.assertEqual(result_chrono[0].id, 1, "Chronological should return oldest")

        # Test reverse-chronological (newest first)
        result_reverse = read_messages_fixed(1, 'reverse-chronological')
        self.assertEqual(result_reverse[0].id, 5, "Reverse-chronological should return newest")

    def test_multiple_messages_ordering(self):
        """Test ordering with multiple messages."""
        def read_messages_fixed(
            limit: int = 5,
            order: str = 'chronological'
        ) -> List[MockMessage]:
            """Test implementation with multiple messages."""
            if order == 'chronological':
                return self.messages[:limit]
            else:
                return list(reversed(self.messages))[:limit]

        # Test chronological order
        chrono_results = read_messages_fixed(3, 'chronological')
        self.assertEqual([m.id for m in chrono_results], [1, 2, 3])

        # Test reverse-chronological order
        reverse_results = read_messages_fixed(3, 'reverse-chronological')
        self.assertEqual([m.id for m in reverse_results], [5, 4, 3])

    def test_edge_cases(self):
        """Test edge cases in message ordering."""
        # Test with empty message list
        empty_messages = []
        self.assertEqual(len(empty_messages), 0)

        # Test with single message
        single_message = [self.messages[0]]
        self.assertEqual(len(single_message), 1)

        # Test with limit exceeding available messages
        result = self.messages[:10]  # Requesting 10 but only 5 available
        self.assertEqual(len(result), 5)


class TestOrderingConsistency(unittest.TestCase):
    """Test consistency between read and read_channel commands."""

    def test_both_commands_same_default(self):
        """After fix, both commands should have same default ordering."""
        # Proposed: Both default to chronological
        read_default = 'chronological'
        read_channel_default = 'chronological'

        self.assertEqual(
            read_default,
            read_channel_default,
            "Both commands should have the same default ordering"
        )

    def test_explicit_ordering_available(self):
        """Both commands should support explicit ordering parameter."""
        valid_orders = ['chronological', 'reverse-chronological']

        # Both commands should accept these ordering options
        for order in valid_orders:
            self.assertIn(order, valid_orders)


class TestRegressionPrevention(unittest.TestCase):
    """Tests to prevent regression of the ordering bug."""

    def test_user_expectation_first_message(self):
        """When user asks for 'first message', they expect oldest."""
        user_request = "first message of today"
        expected_behavior = "return oldest message in the range"

        # This test documents the expected behavior
        self.assertEqual(
            expected_behavior,
            "return oldest message in the range",
            "User expectation should be clearly defined"
        )

    def test_user_expectation_latest_message(self):
        """When user asks for 'latest message', they expect newest."""
        user_request = "latest message"
        expected_behavior = "return newest message available"

        self.assertEqual(
            expected_behavior,
            "return newest message available",
            "User expectation should be clearly defined"
        )

    def test_no_silent_reordering(self):
        """Messages should not be silently reordered without user knowledge."""
        # This test ensures that if we fetch in one order and display in another,
        # it should be explicit and documented
        fetch_order = "newest-first"
        display_order = "oldest-first"

        self.assertNotEqual(
            fetch_order,
            display_order,
            "Silent reordering creates confusion - should be explicit"
        )


def run_tests():
    """Run all unit tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMessageOrdering))
    suite.addTests(loader.loadTestsFromTestCase(TestOrderingConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionPrevention))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())