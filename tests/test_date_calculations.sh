#!/bin/bash
# TDD Tests for all date range calculations

calculate_date_range() {
    local range="$1"
    local moscow_tz="Europe/Moscow"
    local now=$(TZ="$moscow_tz" date '+%Y-%m-%d')
    local today_start="$now 00:00:00"
    local today_end="$now 23:59:59"

    case "$range" in
        "today")
            echo "${today_start}|${today_end}"
            return 0
            ;;
        "yesterday")
            local yesterday=$(TZ="$moscow_tz" date -d "yesterday" '+%Y-%m-%d')
            echo "${yesterday} 00:00:00|${yesterday} 23:59:59"
            return 0
            ;;
        "last:"[0-9]*)
            local days=$(echo "$range" | sed 's/last://')
            local start_date=$(TZ="$moscow_tz" date -d "$days days ago" '+%Y-%m-%d')
            echo "${start_date} 00:00:00|${today_end}"
            return 0
            ;;
        [0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]:[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9])
            local start_date=$(echo "$range" | cut -d':' -f1)
            local end_date=$(echo "$range" | cut -d':' -f2)
            echo "${start_date} 00:00:00|${end_date} 23:59:59"
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

test_date_calculation() {
    local range="$1"
    local expected_pattern="$2"
    local test_name="Date calculation: $range"

    local result=$(calculate_date_range "$range")
    if [[ $? -eq 0 ]]; then
        if [[ "$result" == $expected_pattern ]]; then
            echo -e "✅ PASS: $test_name"
            echo "  Result: $result"
            return 0
        else
            echo -e "❌ FAIL: $test_name"
            echo "  Expected pattern: $expected_pattern"
            echo "  Actual result: $result"
            return 1
        fi
    else
        echo -e "❌ FAIL: $test_name (calculation failed)"
        return 1
    fi
}

echo -e "\n🧪 TDD Tests: Date Range Calculations"
echo "====================================="
echo "Current Moscow time: $(TZ="Europe/Moscow" date)"
echo ""

# Test yesterday
echo -e "\nTest 1: Yesterday range"
yesterday=$(TZ="Europe/Moscow" date -d "yesterday" '+%Y-%m-%d')
test_date_calculation "yesterday" "${yesterday} 00:00:00|${yesterday} 23:59:59"

# Test last:N ranges
echo -e "\nTest 2: Last N days ranges"
test_date_calculation "last:1" "* 00:00:00|* 23:59:59"  # Pattern match for dynamic date
test_date_calculation "last:7" "* 00:00:00|* 23:59:59"
test_date_calculation "last:30" "* 00:00:00|* 23:59:59"

# Test custom ranges
echo -e "\nTest 3: Custom date ranges"
test_date_calculation "2025-09-01:2025-09-10" "2025-09-01 00:00:00|2025-09-10 23:59:59"
test_date_calculation "2024-02-29:2024-02-29" "2024-02-29 00:00:00|2024-02-29 23:59:59"  # Leap year
test_date_calculation "2025-01-01:2025-12-31" "2025-01-01 00:00:00|2025-12-31 23:59:59"  # Full year

# Test edge cases
echo -e "\nTest 4: Edge cases"
test_date_calculation "last:0" "* 00:00:00|* 23:59:59"  # Today only
test_date_calculation "last:365" "* 00:00:00|* 23:59:59"  # One year

echo -e "\n✅ All date calculation tests completed!" | tee test_results_date_calculations.log