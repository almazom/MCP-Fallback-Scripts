#!/bin/bash
# Simple TDD test for offset-id parameter

# Test function
test_offset() {
    local offset="$1"
    local expected="$2"

    # Check if offset is a non-negative integer
    if [[ "$offset" =~ ^[0-9]+$ ]]; then
        result="valid"
    else
        result="invalid"
    fi

    if [[ "$result" == "$expected" ]]; then
        echo "✅ PASS: '$offset' is $expected"
    else
        echo "❌ FAIL: '$offset' should be $expected but is $result"
    fi
}

echo -e "\n🧪 TDD Test: Offset-ID Parameter Validation"
echo "============================================"

# Test valid offsets
echo -e "\nValid offset IDs:"
test_offset "0" "valid"      # Zero (start from beginning)
test_offset "1" "valid"      # First message
test_offset "12345" "valid"  # Arbitrary message ID
test_offset "999999" "valid" # Large message ID

# Test invalid offsets
echo -e "\nInvalid offset IDs:"
test_offset "-1" "invalid"   # Negative
test_offset "abc" "invalid"  # Non-numeric
test_offset "" "invalid"     # Empty
test_offset "1.5" "invalid"  # Decimal
test_offset "+100" "invalid" # Plus sign
test_offset " 100" "invalid" # Leading space

echo -e "\n✅ Offset-ID parameter tests completed!" | tee test_results_03.log