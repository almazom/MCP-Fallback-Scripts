#!/bin/bash
# Test script to verify the message ordering fix

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${YELLOW}🧪 Testing Message Ordering Fix${NC}"
echo "=================================="
echo "Testing the new --order parameter functionality"
echo ""

# Test function
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_behavior="$3"

    ((TESTS_RUN++))
    echo -e "\n${BLUE}Test $TESTS_RUN: $test_name${NC}"
    echo "Command: $command"
    echo "Expected: $expected_behavior"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC} - Command executed successfully"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} - Command failed"
        ((TESTS_FAILED++))
    fi
}

# Test parameter parsing (these will fail with actual execution but should parse correctly)
echo -e "\n${YELLOW}Testing Parameter Parsing${NC}"

# Test help command
run_test "Help command shows new syntax" \
    "./telegram_manager.sh help | grep -q 'read.*--order'" \
    "Help text includes --order parameter"

# Test invalid order parameter
run_test "Invalid order parameter rejection" \
    "./telegram_manager.sh read @test --order invalid 2>&1 | grep -q 'Invalid order'" \
    "Should reject invalid order values"

# Test valid order parameters
run_test "Valid chronological order parameter" \
    "./telegram_manager.sh read @test --order chronological 2>&1 | grep -q 'order=chronological'" \
    "Should accept chronological order"

run_test "Valid reverse order parameter" \
    "./telegram_manager.sh read @test --order reverse 2>&1 | grep -q 'order=reverse'" \
    "Should accept reverse order"

# Test default behavior
run_test "Default order is chronological" \
    "./telegram_manager.sh read @test 2>&1 | grep -q 'order=chronological'" \
    "Should default to chronological order"

# Test limit parameter
run_test "Limit parameter works with order" \
    "./telegram_manager.sh read @test --limit 5 --order reverse 2>&1 | grep -q 'limit=5.*order=reverse'" \
    "Should accept both limit and order parameters"

# Summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "============="
echo "Total Tests: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All parameter parsing tests passed!${NC}"
    echo "The --order parameter has been successfully implemented."
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Test with actual Telegram credentials"
    echo "2. Verify that chronological order returns oldest messages first"
    echo "3. Verify that reverse order returns newest messages first"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi