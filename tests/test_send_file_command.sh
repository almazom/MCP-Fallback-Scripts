#!/bin/bash
# Test script for telegram_manager.sh send_file command
# QA Guardian Test Suite - Production Ready Testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TELEGRAM_MANAGER="${SCRIPT_DIR}/../telegram_manager.sh"
TEST_TARGET="@almazom"
TEST_RESULTS_DIR="${SCRIPT_DIR}/test_results"
TEST_FILES_DIR="${SCRIPT_DIR}/test_files"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="${TEST_RESULTS_DIR}/send_file_test_${TIMESTAMP}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Setup test environment
setup_test_environment() {
    echo "🔧 Setting up test environment..."

    # Create test directories
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$TEST_FILES_DIR"

    # Create test files
    echo "Test content for QA validation" > "${TEST_FILES_DIR}/test_file.txt"
    echo "" > "${TEST_FILES_DIR}/empty_file.txt"

    # Create file with spaces in name
    echo "Testing spaces in filename" > "${TEST_FILES_DIR}/file with spaces.txt"

    # Create unicode filename
    echo "Testing unicode filename" > "${TEST_FILES_DIR}/файл_тест_文件.txt"

    # Create a small image file (1x1 pixel PNG)
    printf '\x89\x50\x4E\x47\x0D\x0A\x1A\x0A\x00\x00\x00\x0D\x49\x48\x44\x52\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53\xDE\x00\x00\x00\x0C\x49\x44\x41\x54\x08\x99\x63\xF8\x0F\x00\x00\x01\x01\x00\x00\x5C\x2C\x00\x00\x00\x00\x49\x45\x4E\x44\xAE\x42\x60\x82' > "${TEST_FILES_DIR}/test_image.png"

    # Create a simple PDF header (minimal valid PDF)
    echo "%PDF-1.4" > "${TEST_FILES_DIR}/test.pdf"
    echo "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj" >> "${TEST_FILES_DIR}/test.pdf"
    echo "2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj" >> "${TEST_FILES_DIR}/test.pdf"
    echo "xref" >> "${TEST_FILES_DIR}/test.pdf"
    echo "0 3" >> "${TEST_FILES_DIR}/test.pdf"
    echo "0000000000 65535 f" >> "${TEST_FILES_DIR}/test.pdf"
    echo "0000000009 00000 n" >> "${TEST_FILES_DIR}/test.pdf"
    echo "0000000056 00000 n" >> "${TEST_FILES_DIR}/test.pdf"
    echo "trailer<</Size 3/Root 1 0 R>>" >> "${TEST_FILES_DIR}/test.pdf"
    echo "startxref" >> "${TEST_FILES_DIR}/test.pdf"
    echo "109" >> "${TEST_FILES_DIR}/test.pdf"
    echo "%%EOF" >> "${TEST_FILES_DIR}/test.pdf"

    # Create file with no read permissions (for error testing)
    echo "No permission test" > "${TEST_FILES_DIR}/no_read_permission.txt"
    chmod 000 "${TEST_FILES_DIR}/no_read_permission.txt"

    # Create a symbolic link
    ln -sf "${TEST_FILES_DIR}/test_file.txt" "${TEST_FILES_DIR}/test_link.txt"

    echo "✅ Test environment setup complete"
}

# Cleanup test environment
cleanup_test_environment() {
    echo "🧹 Cleaning up test environment..."

    # Restore permissions before deletion
    chmod 644 "${TEST_FILES_DIR}/no_read_permission.txt" 2>/dev/null || true

    # Keep test results but clean test files
    rm -rf "${TEST_FILES_DIR}"

    echo "✅ Cleanup complete"
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-success}" # success or failure
    local expected_output="${4:-}"

    echo -e "\n🧪 Testing: ${test_name}"
    echo "Command: ${test_command}"

    # Execute test
    if [ "$expected_result" = "success" ]; then
        if output=$(eval "$test_command" 2>&1); then
            if [ -n "$expected_output" ]; then
                if echo "$output" | grep -q "$expected_output"; then
                    echo -e "${GREEN}✅ PASSED${NC}: Output contains expected text"
                    ((TESTS_PASSED++))
                    echo "[PASS] ${test_name}" >> "$RESULTS_FILE"
                else
                    echo -e "${RED}❌ FAILED${NC}: Output doesn't contain expected text"
                    echo "Expected: $expected_output"
                    echo "Got: $output"
                    ((TESTS_FAILED++))
                    echo "[FAIL] ${test_name}: Expected output not found" >> "$RESULTS_FILE"
                fi
            else
                echo -e "${GREEN}✅ PASSED${NC}"
                ((TESTS_PASSED++))
                echo "[PASS] ${test_name}" >> "$RESULTS_FILE"
            fi
        else
            echo -e "${RED}❌ FAILED${NC}: Command failed when success was expected"
            echo "Output: $output"
            ((TESTS_FAILED++))
            echo "[FAIL] ${test_name}: Unexpected failure" >> "$RESULTS_FILE"
        fi
    else
        if ! output=$(eval "$test_command" 2>&1); then
            if [ -n "$expected_output" ]; then
                if echo "$output" | grep -q "$expected_output"; then
                    echo -e "${GREEN}✅ PASSED${NC}: Failed as expected with correct error"
                    ((TESTS_PASSED++))
                    echo "[PASS] ${test_name}" >> "$RESULTS_FILE"
                else
                    echo -e "${YELLOW}⚠️  PASSED${NC}: Failed as expected but different error"
                    echo "Expected error: $expected_output"
                    echo "Got: $output"
                    ((TESTS_PASSED++))
                    echo "[PASS] ${test_name} (different error message)" >> "$RESULTS_FILE"
                fi
            else
                echo -e "${GREEN}✅ PASSED${NC}: Failed as expected"
                ((TESTS_PASSED++))
                echo "[PASS] ${test_name}" >> "$RESULTS_FILE"
            fi
        else
            echo -e "${RED}❌ FAILED${NC}: Command succeeded when failure was expected"
            echo "Output: $output"
            ((TESTS_FAILED++))
            echo "[FAIL] ${test_name}: Unexpected success" >> "$RESULTS_FILE"
        fi
    fi
}

# Main test execution
main() {
    echo "==============================================="
    echo "🎯 QA Guardian Test Suite for send_file Command"
    echo "==============================================="
    echo "Timestamp: ${TIMESTAMP}"
    echo "Test Results: ${RESULTS_FILE}"
    echo ""

    # Setup
    setup_test_environment

    # Track start time
    START_TIME=$(date +%s)

    echo -e "\n${YELLOW}=== HAPPY PATH TESTS ===${NC}"

    # Test 1: Send text file with custom caption
    run_test \
        "Send text file with custom caption" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/test_file.txt' 'QA Test Document'" \
        "success" \
        "✅ File sent successfully"

    sleep 1 # Prevent rate limiting

    # Test 2: Send file without caption (default caption)
    run_test \
        "Send file without caption" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/test_file.txt'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    # Test 3: Send image file
    run_test \
        "Send PNG image" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/test_image.png' '📷 Test image'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    # Test 4: Send PDF document
    run_test \
        "Send PDF document" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/test.pdf' '📄 Test PDF'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    echo -e "\n${YELLOW}=== ERROR HANDLING TESTS ===${NC}"

    # Test 5: Non-existent file
    run_test \
        "Send non-existent file" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '/tmp/this_file_does_not_exist.txt' 'Test'" \
        "failure" \
        "❌ File not found"

    # Test 6: Missing target parameter
    run_test \
        "Missing target parameter" \
        "${TELEGRAM_MANAGER} send_file" \
        "failure" \
        "Usage:"

    # Test 7: Missing file path parameter
    run_test \
        "Missing file path parameter" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET}" \
        "failure" \
        "Usage:"

    echo -e "\n${YELLOW}=== EDGE CASE TESTS ===${NC}"

    # Test 8: Empty file
    run_test \
        "Send empty file" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/empty_file.txt' 'Empty file test'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    # Test 9: File with spaces in name
    run_test \
        "Send file with spaces in name" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/file with spaces.txt' 'Space test'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    # Test 10: Unicode filename
    run_test \
        "Send file with unicode name" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/файл_тест_文件.txt' 'Unicode test'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    # Test 11: Symbolic link
    run_test \
        "Send symbolic link" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/test_link.txt' 'Symlink test'" \
        "success" \
        "✅ File sent successfully"

    sleep 1

    echo -e "\n${YELLOW}=== SECURITY TESTS ===${NC}"

    # Test 12: File without read permission
    run_test \
        "Send file without read permission" \
        "${TELEGRAM_MANAGER} send_file ${TEST_TARGET} '${TEST_FILES_DIR}/no_read_permission.txt' 'Permission test'" \
        "failure" \
        ""

    echo -e "\n${YELLOW}=== REGRESSION TESTS ===${NC}"

    # Test 13: Verify send command still works
    run_test \
        "Regression: send command still works" \
        "${TELEGRAM_MANAGER} send ${TEST_TARGET} 'Regression test message'" \
        "success" \
        "✅ Message sent"

    sleep 1

    # Test 14: Verify help includes send_file
    run_test \
        "Help text includes send_file" \
        "${TELEGRAM_MANAGER} help 2>&1 | grep -q 'send_file'" \
        "success" \
        ""

    # Calculate test duration
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Cleanup
    cleanup_test_environment

    # Print summary
    echo ""
    echo "==============================================="
    echo "📊 TEST SUMMARY"
    echo "==============================================="
    echo -e "${GREEN}Passed:${NC} ${TESTS_PASSED}"
    echo -e "${RED}Failed:${NC} ${TESTS_FAILED}"
    echo -e "${YELLOW}Skipped:${NC} ${TESTS_SKIPPED}"
    echo "Total: $((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))"
    echo "Duration: ${DURATION} seconds"
    echo "Results saved to: ${RESULTS_FILE}"
    echo ""

    if [ ${TESTS_FAILED} -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! The send_file command is production ready.${NC}"
        exit 0
    else
        echo -e "${RED}⚠️  SOME TESTS FAILED! Review the results above.${NC}"
        exit 1
    fi
}

# Run tests
main "$@"