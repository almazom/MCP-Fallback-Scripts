#!/bin/bash
# TDD Test for 'today' date range calculation

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
        *)
            return 1
            ;;
    esac
}

test_today_range() {
    echo -e "\n🧪 TDD Test: 'today' Date Range Calculation"
    echo "==========================================="

    # Get expected result
    local expected_start=$(TZ="Europe/Moscow" date '+%Y-%m-%d')" 00:00:00"
    local expected_end=$(TZ="Europe/Moscow" date '+%Y-%m-%d')" 23:59:59"
    local expected="$expected_start|$expected_end"

    echo "Expected: $expected"

    # Get actual result
    local actual=$(calculate_date_range "today")

    if [[ "$actual" == "$expected" ]]; then
        echo -e "✅ PASS: 'today' range calculation is correct"
        echo "  Start: $(echo $actual | cut -d'|' -f1)"
        echo "  End:   $(echo $actual | cut -d'|' -f2)"
        return 0
    else
        echo -e "❌ FAIL: 'today' range calculation is incorrect"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        return 1
    fi
}

# Verify timezone is Moscow
echo "Current Moscow time: $(TZ="Europe/Moscow" date)"
test_today_range

echo -e "\n✅ 'today' range test completed!" | tee test_results_05.log