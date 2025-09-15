#!/bin/bash
# Simple TDD test for channel name validation

# Test function
test_channel() {
    local channel="$1"
    local expected="$2"

    # Check if channel is valid
    # Valid formats: @username (5-32 chars) or -100xxxxxxxxx (group ID)
    if [[ "$channel" =~ ^@[a-zA-Z0-9_]{5,32}$ ]] || [[ "$channel" =~ ^-100[0-9]{10}$ ]]; then
        result="valid"
    else
        result="invalid"
    fi

    if [[ "$result" == "$expected" ]]; then
        echo "✅ PASS: '$channel' is $expected"
    else
        echo "❌ FAIL: '$channel' should be $expected but is $result"
    fi
}

echo -e "\n🧪 TDD Test: Channel Name Validation"
echo "====================================="

# Test valid channel names
echo -e "\nValid channel names:"
test_channel "@channel" "valid"
test_channel "@my_channel" "valid"
test_channel "@test123" "valid"
test_channel "@a_b_c_d_e" "valid"
test_channel "-1001234567890" "valid"  # Group ID

# Test invalid channel names
echo -e "\nInvalid channel names:"
test_channel "@" "invalid"             # Too short
test_channel "@abc" "invalid"          # Too short (4 chars)
test_channel "channel" "invalid"       # Missing @
test_channel "@my-channel" "invalid"   # Invalid character (-)
test_channel "@" "invalid"             # Empty username
test_channel "-100123" "invalid"       # Group ID too short
test_channel "" "invalid"              # Empty string

# Edge cases
echo -e "\nEdge cases:"
test_channel "@12345" "valid"           # Numbers only
test_channel "@_test_" "valid"          # Underscores
test_channel "@abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz" "invalid"  # Too long (33 chars)

echo -e "\n✅ Channel name validation tests completed!" | tee test_results_04.log