Feature: Telegram Message Ordering
  As a user of telegram_manager.sh
  I want consistent message ordering across different commands
  So that I can reliably retrieve messages in expected order

  Background:
    Given the telegram_manager.sh script is available
    And there are multiple messages in the @ClavaFamily channel from today
    And messages have timestamps spanning throughout the day

  # Current ACTUAL behavior (not expected)
  Scenario: Simple read command returns latest message
    When I run "./telegram_manager.sh read @ClavaFamily 1"
    Then the command should return the MOST RECENT message
    And the message should be from the END of today
    And the output should show message details with timestamp

  Scenario: Read channel with today range and limit 1
    When I run "./telegram_manager.sh read_channel @ClavaFamily --range today --limit 1"
    Then the command should return the FIRST message of today
    And the message should be from the BEGINNING of today
    And messages should be displayed in chronological order (oldest first)

  # This scenario shows the inconsistency
  Scenario: Inconsistent behavior between read and read_channel
    Given I want to get "the first message of today"
    When I run "./telegram_manager.sh read @ClavaFamily 1"
    Then I get the LATEST message (unexpected)
    When I run "./telegram_manager.sh read_channel @ClavaFamily --range today --limit 1"
    Then I get the EARLIEST message of today (expected)
    And this creates confusion for users

  # Edge cases
  Scenario: Read multiple messages shows reverse chronological order
    When I run "./telegram_manager.sh read @ClavaFamily 5"
    Then messages should be displayed newest to oldest
    And message 1 should be the most recent
    And message 5 should be the oldest of the batch

  Scenario: Read channel with range shows chronological order
    When I run "./telegram_manager.sh read_channel @ClavaFamily --range today --limit 5"
    Then messages should be displayed oldest to newest
    And message 1 should be from early in the day
    And message 5 should be more recent
    And messages are grouped by day with headers

  # Expected behavior after fix
  Scenario: Consistent ordering with explicit parameter
    When I run "./telegram_manager.sh read @ClavaFamily 1 --order oldest-first"
    Then the command should return the OLDEST available message
    When I run "./telegram_manager.sh read @ClavaFamily 1 --order newest-first"
    Then the command should return the NEWEST available message
    And both commands should be explicit about ordering