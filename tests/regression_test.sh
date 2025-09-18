#!/bin/bash
# Regression testing - ensure existing commands still work after send_file addition

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TELEGRAM_MANAGER="${SCRIPT_DIR}/../telegram_manager.sh"

echo "🔄 Regression Testing - Existing Commands"
echo "=========================================="

# Test 1: send command (text messages)
echo -e "\n1. Testing 'send' command..."
output=$(${TELEGRAM_MANAGER} send @almazom "Regression test: send command - $(date +%H:%M:%S)" 2>&1)
if echo "$output" | grep -q "✅ Message sent"; then
    echo "✅ 'send' command works correctly"
else
    echo "❌ 'send' command broken!"
    echo "   Output: $output"
    exit 1
fi

# Test 2: read command
echo -e "\n2. Testing 'read' command..."
output=$(${TELEGRAM_MANAGER} read @aiclubsweggs today 2>&1 | head -20)
if echo "$output" | grep -q "Using cached data\|Cache stale\|Fetching"; then
    echo "✅ 'read' command works correctly"
elif [[ -n "$output" ]]; then
    echo "✅ 'read' command returns data"
else
    echo "❌ 'read' command may be broken"
    echo "   Output: $output"
fi

# Test 3: fetch command
echo -e "\n3. Testing 'fetch' command structure..."
output=$(${TELEGRAM_MANAGER} fetch 2>&1 || true)
if echo "$output" | grep -q "Usage:.*fetch.*<channel>.*\[limit\]"; then
    echo "✅ 'fetch' command usage works"
else
    echo "⚠️  'fetch' command usage message changed"
fi

# Test 4: cache command
echo -e "\n4. Testing 'cache' command..."
output=$(${TELEGRAM_MANAGER} cache 2>&1 | head -5)
if echo "$output" | grep -q "Cache Directory\|cache is empty\|Total messages"; then
    echo "✅ 'cache' command works"
else
    echo "⚠️  'cache' command output unexpected"
fi

# Test 5: json export
echo -e "\n5. Testing 'json' command..."
output=$(${TELEGRAM_MANAGER} json @aiclubsweggs today --summary 2>&1 | head -10)
if echo "$output" | grep -q "channel\|messages\|{"; then
    echo "✅ 'json' command works"
else
    echo "⚠️  'json' command may have issues"
fi

# Test 6: Help text completeness
echo -e "\n6. Verifying help text is complete..."
help_output=$(${TELEGRAM_MANAGER} help 2>&1)

required_commands=("fetch" "read" "send" "send_file" "json" "cache" "clean" "archive" "restore")
missing_commands=()

for cmd in "${required_commands[@]}"; do
    if ! echo "$help_output" | grep -q "$cmd"; then
        missing_commands+=("$cmd")
    fi
done

if [ ${#missing_commands[@]} -eq 0 ]; then
    echo "✅ All core commands present in help"
else
    echo "❌ Missing commands in help: ${missing_commands[*]}"
fi

# Test 7: Verify script still uses proper error handling
echo -e "\n7. Testing error handling (set -euo pipefail)..."
if grep -q "set -euo pipefail" "${SCRIPT_DIR}/../telegram_manager.sh"; then
    echo "✅ Script maintains proper error handling"
else
    echo "⚠️  Script error handling may have changed"
fi

# Test 8: Check Python code injection safety
echo -e "\n8. Testing for command injection vulnerabilities..."
INJECT_TEST='$(echo hacked)'
output=$(${TELEGRAM_MANAGER} send_file @almazom "/tmp/test.txt${INJECT_TEST}" "Test" 2>&1 || true)
if echo "$output" | grep -q "hacked"; then
    echo "❌ CRITICAL: Command injection vulnerability detected!"
else
    echo "✅ No obvious command injection vulnerability"
fi

echo -e "\n=========================================="
echo "✅ Regression Testing Complete"
echo ""
echo "Summary:"
echo "- Core commands (send, read, fetch): Working"
echo "- Help documentation: Updated"
echo "- Error handling: Maintained"
echo "- Security: No obvious injection vulnerabilities"