#!/bin/bash

# Integration test for message ordering in telegram_manager.sh
# This test verifies the actual behavior and documents the bug

set -e  # Exit on error

SCRIPT_DIR="/home/almaz/MCP/FALLBACK_SCRIPTS"
TELEGRAM_MANAGER="$SCRIPT_DIR/telegram_manager.sh"
TEST_CHANNEL="@ClavaFamily"
TEST_OUTPUT_DIR="$SCRIPT_DIR/telegram_manager_tests/test_outputs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$TEST_OUTPUT_DIR"

echo "=========================================="
echo "Integration Test: Message Ordering Bug"
echo "=========================================="
echo ""

# Function to extract message ID from output
extract_message_id() {
    grep -oP 'ID: \K\d+' | head -1
}

# Function to extract timestamp from output
extract_timestamp() {
    grep -oP 'Date: \K[\d-]+ [\d:]+' | head -1
}

run_test() {
    local test_name="$1"
    local command="$2"
    local expected_behavior="$3"

    echo -e "${YELLOW}TEST: $test_name${NC}"
    echo "Command: $command"
    echo "Expected: $expected_behavior"
    echo "---"

    # Run command and capture output
    output_file="$TEST_OUTPUT_DIR/${test_name// /_}.txt"
    if eval "$command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✓ Command executed successfully${NC}"

        # Extract and display key information
        if grep -q "ID:" "$output_file"; then
            msg_id=$(cat "$output_file" | extract_message_id)
            timestamp=$(cat "$output_file" | extract_timestamp)
            echo "  Message ID: $msg_id"
            echo "  Timestamp: $timestamp"
        fi

        # Save first 10 lines for inspection
        echo "  Output preview:"
        head -10 "$output_file" | sed 's/^/    /'
    else
        echo -e "${RED}✗ Command failed${NC}"
        echo "  Error output:"
        head -10 "$output_file" | sed 's/^/    /'
    fi

    echo ""
}

# Test 1: Simple read command behavior
run_test "Simple Read - Single Message" \
    "$TELEGRAM_MANAGER read $TEST_CHANNEL 1" \
    "Should return the LATEST (most recent) message"

# Test 2: Read multiple messages
run_test "Simple Read - Multiple Messages" \
    "$TELEGRAM_MANAGER read $TEST_CHANNEL 3" \
    "Should return 3 messages in reverse chronological order (newest first)"

# Test 3: Read channel with today range
run_test "Read Channel - Today Single Message" \
    "$TELEGRAM_MANAGER read_channel $TEST_CHANNEL --range today --limit 1" \
    "Should return the FIRST (oldest) message of today"

# Test 4: Read channel with today range, multiple messages
run_test "Read Channel - Today Multiple Messages" \
    "$TELEGRAM_MANAGER read_channel $TEST_CHANNEL --range today --limit 3" \
    "Should return 3 messages in chronological order (oldest first)"

# Test 5: Compare outputs to demonstrate inconsistency
echo "=========================================="
echo "CONSISTENCY CHECK"
echo "=========================================="
echo ""

# Get message IDs from both commands
echo "Comparing first message from both commands..."

# Run read command
read_output="$TEST_OUTPUT_DIR/read_single.txt"
$TELEGRAM_MANAGER read $TEST_CHANNEL 1 > "$read_output" 2>&1
read_msg_id=$(cat "$read_output" | extract_message_id)
read_timestamp=$(cat "$read_output" | extract_timestamp)

# Run read_channel command
channel_output="$TEST_OUTPUT_DIR/read_channel_single.txt"
$TELEGRAM_MANAGER read_channel $TEST_CHANNEL --range today --limit 1 > "$channel_output" 2>&1
channel_msg_id=$(cat "$channel_output" | extract_message_id || echo "N/A")
channel_timestamp=$(cat "$channel_output" | extract_timestamp || echo "N/A")

echo "Results:"
echo "  read command:         Message ID=$read_msg_id, Time=$read_timestamp"
echo "  read_channel command: Message ID=$channel_msg_id, Time=$channel_timestamp"
echo ""

if [[ "$read_msg_id" == "$channel_msg_id" ]]; then
    echo -e "${GREEN}✓ CONSISTENT: Both commands returned the same message${NC}"
else
    echo -e "${RED}✗ INCONSISTENT: Commands returned different messages!${NC}"
    echo ""
    echo "This demonstrates the bug:"
    echo "  - 'read' returns the LATEST message (ID: $read_msg_id)"
    echo "  - 'read_channel' returns the EARLIEST message of today (ID: $channel_msg_id)"
fi

echo ""
echo "=========================================="
echo "BEHAVIOR DOCUMENTATION"
echo "=========================================="
echo ""
echo "Current Behavior Summary:"
echo "1. 'read' command:"
echo "   - Uses iter_messages() without reverse parameter"
echo "   - Returns messages newest-first (reverse chronological)"
echo "   - No post-processing or sorting"
echo ""
echo "2. 'read_channel' command:"
echo "   - Uses iter_messages() with reverse=False (also newest-first)"
echo "   - BUT then sorts messages by date (oldest-first)"
echo "   - Results in chronological order display"
echo ""
echo "3. User Confusion:"
echo "   - Same conceptual request ('get 1 message') returns opposite results"
echo "   - 'First message' ambiguity: temporal first vs. retrieval first"
echo ""

# Generate test report
REPORT_FILE="$TEST_OUTPUT_DIR/test_report_$(date +%Y%m%d_%H%M%S).md"
cat > "$REPORT_FILE" << EOF
# Message Ordering Test Report
Generated: $(date)

## Test Results

### Test 1: Simple Read
- Command: \`$TELEGRAM_MANAGER read $TEST_CHANNEL 1\`
- Message ID: $read_msg_id
- Timestamp: $read_timestamp
- Behavior: Returns LATEST message (newest)

### Test 2: Read Channel with Range
- Command: \`$TELEGRAM_MANAGER read_channel $TEST_CHANNEL --range today --limit 1\`
- Message ID: $channel_msg_id
- Timestamp: $channel_timestamp
- Behavior: Returns FIRST message of range (oldest)

## Consistency Check
$(if [[ "$read_msg_id" == "$channel_msg_id" ]]; then
    echo "✓ PASS: Commands are consistent"
else
    echo "✗ FAIL: Commands are inconsistent - BUG CONFIRMED"
fi)

## Recommendation
Implement explicit ordering parameter for both commands to eliminate ambiguity.
EOF

echo "Test report saved to: $REPORT_FILE"
echo ""
echo "=========================================="
echo "Test completed. Check $TEST_OUTPUT_DIR for detailed outputs."