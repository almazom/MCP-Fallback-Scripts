#!/bin/bash
# Quick validation test for send_file command

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TELEGRAM_MANAGER="${SCRIPT_DIR}/../telegram_manager.sh"

echo "🎯 Quick Send File Command Validation"
echo "======================================"

# Test 1: Verify command exists in help
echo -e "\n1. Checking if send_file is in help text..."
if ${TELEGRAM_MANAGER} help 2>&1 | grep -q "send_file"; then
    echo "✅ send_file command found in help"
else
    echo "❌ send_file command NOT found in help"
    exit 1
fi

# Test 2: Check usage message
echo -e "\n2. Testing usage message..."
output=$(${TELEGRAM_MANAGER} send_file 2>&1 || true)
if echo "$output" | grep -q "Usage:.*send_file.*<target>.*<file_path>.*\[caption\]"; then
    echo "✅ Correct usage message displayed"
else
    echo "❌ Incorrect or missing usage message"
    echo "Got: $output"
    exit 1
fi

# Test 3: Test non-existent file handling
echo -e "\n3. Testing non-existent file handling..."
test_output=$(${TELEGRAM_MANAGER} send_file @almazom /tmp/does_not_exist_qa_test.txt 2>&1 || true)
if echo "$test_output" | grep -q "❌ File not found"; then
    echo "✅ Properly handles non-existent files"
else
    echo "❌ Failed to handle non-existent file properly"
    echo "Output: $test_output"
    exit 1
fi

# Test 4: Create and send a real test file
echo -e "\n4. Testing actual file sending..."
TEST_FILE="/tmp/telegram_qa_test_$(date +%s).txt"
echo "QA Test Content - $(date)" > "$TEST_FILE"

if output=$(${TELEGRAM_MANAGER} send_file @almazom "$TEST_FILE" "QA Test at $(date +%H:%M:%S)" 2>&1); then
    if echo "$output" | grep -q "✅ File sent successfully"; then
        echo "✅ File sent successfully"
        echo "   Output: $output"
    else
        echo "⚠️  Command succeeded but unexpected output"
        echo "   Output: $output"
    fi
else
    echo "❌ Failed to send file"
    echo "   Output: $output"
fi

# Cleanup
rm -f "$TEST_FILE"

echo -e "\n======================================"
echo "✅ Quick validation complete"