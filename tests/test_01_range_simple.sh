#!/bin/bash
# Simple TDD test for range parameter

calculate_date_range() {
    local range="$1"
    local moscow_tz="Europe/Moscow"
    local now=$(TZ="$moscow_tz" date '+%Y-%m-%d')
    local today_start="$now 00:00:00"
    local today_end="$now 23:59:59"

    case "$range" in
        "today") echo "${today_start}|${today_end}"; return 0 ;;
        "yesterday") local yesterday=$(TZ="$moscow_tz" date -d "yesterday" '+%Y-%m-%d'); echo "${yesterday} 00:00:00|${yesterday} 23:59:59"; return 0 ;;
        "last:"[0-9]*) local days=$(echo "$range" | sed 's/last://'); local start_date=$(TZ="$moscow_tz" date -d "$days days ago" '+%Y-%m-%d'); echo "${start_date} 00:00:00|${today_end}"; return 0 ;;
        [0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]:[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]) local start_date=$(echo "$range" | cut -d':' -f1); local end_date=$(echo "$range" | cut -d':' -f2); echo "${start_date} 00:00:00|${end_date} 23:59:59"; return 0 ;;
        *) return 1 ;;
    esac
}

# Test runner
test_range() {
    local range="$1"
    local expected="$2"

    if calculate_date_range "$range" >/dev/null 2>&1; then
        if [[ "$expected" == "valid" ]]; then
            echo "✅ PASS: '$range' is valid"
            return 0
        else
            echo "❌ FAIL: '$range' should be invalid but passed"
            return 1
        fi
    else
        if [[ "$expected" == "invalid" ]]; then
            echo "✅ PASS: '$range' is correctly rejected"
            return 0
        else
            echo "❌ FAIL: '$range' should be valid but failed"
            return 1
        fi
    fi
}

echo -e "\n🧪 TDD Test: Range Parameter Validation"
echo "======================================="

# Test valid ranges
echo -e "\nValid ranges:"
test_range "today" "valid"
test_range "yesterday" "valid"
test_range "last:7" "valid"
test_range "2025-09-01:2025-09-10" "valid"

# Test invalid ranges
echo -e "\nInvalid ranges:"
test_range "" "invalid"
test_range "invalid" "invalid"
test_range "tomorrow" "invalid"
test_range "last:abc" "invalid"

echo -e "\n✅ Range parameter tests completed!" | tee test_results_01.log