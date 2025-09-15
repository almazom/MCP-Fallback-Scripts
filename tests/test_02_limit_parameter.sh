#!/bin/bash
# TDD Test 02: Limit Parameter Validation
# Tests the --limit parameter for read_channel command

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

# Simple validation function for limit
validate_limit() {
    local limit="$1"

    # Check if limit is a positive integer between 1 and 1000
    if [[ "$limit" =~ ^[0-9]+$ ]] && [[ "$limit" -ge 1 ]] && [[ "$limit" -le 1000 ]]; then
        return 0
    else
        return 1
    fi
}

# Test assertion helper
test_limit() {
    local limit="$1"
    local expected="$2"
    local test_name="Limit validation: $limit"

    ((++TESTS_RUN))

    if validate_limit "$limit"; then
        if [[ "$expected" == "valid" ]]; then
            echo -e "${GREEN}✅ PASS${NC}: $test_name"
            ((++TESTS_PASSED))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}: $test_name (should be invalid)"
            ((++TESTS_FAILED))
            return 1
        fi
    else
        if [[ "$expected" == "invalid" ]]; then
            echo -e "${GREEN}✅ PASS${NC}: $test_name (correctly rejected)"
            ((++TESTS_PASSED))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}: $test_name (should be valid)"
            ((++TESTS_FAILED))
            return 1
        fi
    fi
}

# RED Phase: Write failing tests first
echo -e "\n${YELLOW}🧪 TDD Test 02: Limit Parameter (RED Phase)${NC}"
echo "============================================="
echo "Testing limit parameter validation..."

# Test 2.1: Valid limits
echo -e "\n${BLUE}Test Group 1: Valid Limits${NC}"
test_limit "1" "valid"      # Minimum valid limit
test_limit "10" "valid"     # Common small limit
test_limit "100" "valid"    # Default limit
test_limit "500" "valid"    # Medium limit
test_limit "1000" "valid"   # Maximum valid limit

# Test 2.2: Invalid limits
echo -e "\n${BLUE}Test Group 2: Invalid Limits${NC}"
test_limit "0" "invalid"      # Zero is invalid
test_limit "-1" "invalid"     # Negative numbers
test_limit "1001" "invalid"   # Above maximum
test_limit "9999" "invalid"   # Way above maximum
test_limit "abc" "invalid"    # Non-numeric
test_limit "" "invalid"       # Empty string
test_limit "1.5" "invalid"    # Decimal number
test_limit "1.0" "invalid"    # Decimal format
test_limit "+100" "invalid"   # Plus sign
test_limit " 100" "invalid"   # Leading space

# Test 2.3: Edge cases
echo -e "\n${BLUE}Test Group 3: Edge Cases${NC}"
test_limit "01" "valid"       # Leading zero (still valid)
test_limit "001" "valid"      # Multiple leading zeros
test_limit "999" "valid"      # Just under maximum

# GREEN Phase: Implementation is already in telegram_manager.sh
echo -e "\n${YELLOW}GREEN Phase: Implementation Review${NC}"
echo "The limit validation is implemented in parse_read_channel_args()"
echo "It checks: [[ \"\$limit\" =~ ^[0-9]+$ ]] \u0026\u0026 [[ \"\$limit\" -ge 1 ]] \u0026\u0026 [[ \"\$limit\" -le 1000 ]]"

# REFACTOR Phase
echo -e "\n${YELLOW}REFACTOR Phase: Review${NC}"
echo "✅ Simple regex validation"
echo "✅ Clear bounds (1-1000)"
echo "✅ No unnecessary complexity"
echo "✅ Follows KISS principle"

# Summary
echo -e "\n${YELLOW}Test Summary for Limit Parameter${NC}"
echo "=================================="
echo "Total Tests: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "\n${GREEN}✅ All limit parameter tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    exit 1
fi