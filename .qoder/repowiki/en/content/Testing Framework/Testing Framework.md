# Testing Framework

<cite>
**Referenced Files in This Document**   
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh)
- [test_10_error_handling.sh](file://tests/test_10_error_handling.sh)
- [boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh)
- [test_09_integration.sh](file://tests/test_09_integration.sh)
- [test_ordering_integration.sh](file://tests/test_ordering_integration.sh)
- [BUG_REPORT_message_ordering.md](file://tests/BUG_REPORT_message_ordering.md)
- [PROPOSED_FIX_message_ordering.md](file://tests/PROPOSED_FIX_message_ordering.md)
- [test_first_message_border_detection.sh](file://tests/test_first_message_border_detection.sh)
- [test_date_calculations.sh](file://tests/test_date_calculations.sh)
</cite>

## Table of Contents
1. [Testing Framework](#testing-framework)
2. [Test Organization and Structure](#test-organization-and-structure)
3. [Test Categories and Coverage](#test-categories-and-coverage)
4. [Key Test Scripts Analysis](#key-test-scripts-analysis)
5. [System Behavior Validation](#system-behavior-validation)
6. [Issue Resolution and Test-Driven Development](#issue-resolution-and-test-driven-development)
7. [Test Execution and Result Interpretation](#test-execution-and-result-interpretation)
8. [Development and Debugging Support](#development-and-debugging-support)

## Test Organization and Structure

The testing infrastructure is organized in the `tests` directory, with a systematic naming convention that reflects both the test's functional category and its complexity level. Test scripts follow a numerical prefix pattern (e.g., `test_01_range_parameter.sh`, `test_02_limit_parameter.sh`) which indicates the test's priority and sequence in the testing workflow. This organization enables developers to understand the testing hierarchy and execute tests in a logical order.

The test suite is structured to support Test-Driven Development (TDD) principles, with clear RED-GREEN-REFACTOR phases evident in scripts like `test_01_range_parameter.sh`. Tests are categorized by functionality, including parameter validation, error handling, integration scenarios, and boundary detection. This modular approach allows for targeted testing of specific system components while maintaining the ability to execute comprehensive test suites.

**Section sources**
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh#L1-L158)
- [test_02_limit_parameter.sh](file://tests/test_02_limit_parameter.sh#L1-L158)
- [test_03_offset_simple.sh](file://tests/test_03_offset_simple.sh#L1-L158)

## Test Categories and Coverage

The test suite encompasses multiple categories that validate different aspects of the system's functionality and reliability. These categories include unit tests for individual parameter validation, integration tests for command parsing workflows, error handling scenarios for robustness verification, and specialized boundary detection tests for complex temporal logic.

Unit tests such as `test_01_range_parameter.sh` focus on validating individual parameters like the `--range` option, ensuring correct parsing and processing of values like "today", "yesterday", "last:N", and custom date ranges. Integration tests like `test_09_integration.sh` verify the complete command parsing workflow, testing how multiple parameters interact within the `read_channel` command. Error handling tests including `test_10_error_handling.sh` validate the system's response to invalid inputs, missing parameters, and edge cases, ensuring graceful degradation and informative error messages.

Boundary detection tests such as `test_first_message_border_detection.sh` address complex temporal scenarios where timezone boundaries affect message ordering and date categorization. These tests are critical for ensuring accurate identification of the "first message of today" across different timezone contexts.

**Section sources**
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh#L1-L158)
- [test_09_integration.sh](file://tests/test_09_integration.sh#L1-L277)
- [test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L1-L244)
- [test_first_message_border_detection.sh](file://tests/test_first_message_border_detection.sh#L1-L56)

## Key Test Scripts Analysis

### test_01_range_parameter.sh

This test script validates the `--range` parameter functionality for the `read_channel` command. It implements a comprehensive test suite that verifies both valid and invalid range formats, including "today", "yesterday", "last:N" days, and custom date ranges in the format "YYYY-MM-DD:YYYY-MM-DD". The test uses a mock implementation of the `calculate_date_range` function to isolate and test the parameter validation logic independently of the main application.

The script follows TDD methodology with explicit RED-GREEN-REFACTOR phases, first writing failing tests for various range formats, then verifying that the implementation passes all tests. It includes extensive edge case testing for leap years, invalid months/days, and malformed date strings, ensuring robust date parsing capabilities.

**Section sources**
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh#L1-L158)

### test_10_error_handling.sh

This comprehensive error handling test validates the system's resilience to various error conditions and invalid inputs. The script tests authentication errors, channel access issues, parameter validation failures, date calculation errors, input sanitization vulnerabilities, and resource limit enforcement. It specifically checks for protection against command injection attempts and proper handling of special characters in channel names.

The test uses a systematic approach to verify that the system returns appropriate error messages and exit codes for different failure scenarios. It includes tests for edge cases such as empty parameters, whitespace inputs, and Unicode characters, ensuring the system handles diverse input conditions gracefully.

**Section sources**
- [test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L1-L244)

### boundary_aware_first_message_detector.sh

This sophisticated test script addresses the complex problem of accurately identifying the first message of a given day when timezone boundaries affect message categorization. The script implements a boundary-aware algorithm that examines messages from both the target day and the previous day to detect messages that may have been categorized under the wrong date due to timezone differences.

The detector works by retrieving a large set of messages in reverse chronological order, then analyzing the boundary between consecutive days. It specifically looks for early morning messages (00:00-06:00) in the previous day's section that might actually belong to the target day. By comparing timestamps across the boundary, the script can accurately identify the true first message of the day, even when it appears under the previous day's header due to timezone effects.

**Section sources**
- [boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh#L1-L156)

## System Behavior Validation

The test suite validates several critical system behaviors that are essential for reliable operation. Message ordering consistency is tested through integration scripts like `test_ordering_integration.sh`, which compares the output of different commands to ensure they return messages in the expected order. Cache invalidation is implicitly tested through repeated executions of the same commands, verifying that fresh data is retrieved rather than stale cached results.

Date-based filtering is extensively validated through multiple test scripts that verify the correct interpretation of various date range specifications. The tests ensure that "today", "yesterday", and "last:N" ranges are calculated correctly using Moscow timezone as the reference point. Custom date ranges are validated for proper start and end date parsing, with appropriate error handling for invalid formats.

The test suite also validates the system's handling of message boundaries across days, ensuring that the "first message of today" is correctly identified even when timezone differences cause messages to appear under the wrong date header. This is particularly important for applications that rely on accurate temporal analysis of message sequences.

**Section sources**
- [test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L182)
- [test_date_calculations.sh](file://tests/test_date_calculations.sh#L1-L88)
- [boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh#L1-L156)

## Issue Resolution and Test-Driven Development

The testing infrastructure directly supports issue resolution through documented bug reports and proposed fixes. The `BUG_REPORT_message_ordering.md` file details a critical inconsistency in message ordering between the `read` and `read_channel` commands, where identical requests return messages in different orders. This bug causes user confusion when requesting "the first message of today," as the two commands return opposite results (latest vs. earliest message).

The `PROPOSED_FIX_message_ordering.md` document outlines a comprehensive solution that introduces an explicit `--order` parameter to both commands, with clear values of "chronological" and "reverse-chronological." This fix aligns the default behaviors of both commands while providing flexibility for users who need specific ordering. The proposed solution includes a phased migration path to maintain backward compatibility while transitioning to the new consistent behavior.

The test suite supports this fix through dedicated tests that verify ordering consistency, such as `test_ordering_integration.sh`, which compares outputs from both commands to detect inconsistencies. These tests serve as regression protection, ensuring that the fix resolves the issue without introducing new problems.

**Section sources**
- [BUG_REPORT_message_ordering.md](file://tests/BUG_REPORT_message_ordering.md#L1-L122)
- [PROPOSED_FIX_message_ordering.md](file://tests/PROPOSED_FIX_message_ordering.md#L1-L206)
- [test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L182)

## Test Execution and Result Interpretation

To execute the tests, navigate to the `tests` directory and run individual test scripts using bash. Most test scripts are self-contained and will output color-coded results indicating pass (green) or fail (red) status for each test case. For example:

```bash
cd tests
./test_01_range_parameter.sh
./test_10_error_handling.sh
```

Test results are interpreted based on the summary output at the end of each test run. Successful tests will display a "All tests passed!" message with green checkmarks, while failed tests will show red X marks indicating which specific test cases failed. Some tests generate detailed log files (e.g., `test_results_10.log`) that provide additional context for debugging.

Integration tests like `test_09_integration.sh` and `test_ordering_integration.sh` require the main `telegram_manager.sh` script to be properly configured with API credentials to execute fully. The test scripts include provisions for both mocked testing (for parameter validation) and real API testing (for integration scenarios).

**Section sources**
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh#L1-L158)
- [test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L1-L244)
- [test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L182)

## Development and Debugging Support

The test suite significantly enhances development and debugging workflows by providing immediate feedback on code changes and serving as living documentation of expected system behavior. The TDD approach embodied in scripts like `test_01_range_parameter.sh` encourages developers to write tests before implementing features, ensuring comprehensive test coverage from the outset.

For debugging, the test scripts provide isolated environments to reproduce and analyze issues. The `BUG_REPORT_message_ordering.md` and `PROPOSED_FIX_message_ordering.md` files demonstrate how the test infrastructure supports the complete issue resolution lifecycle, from bug identification through fix proposal and validation.

The boundary detection tests, particularly `boundary_aware_first_message_detector.sh`, serve as valuable debugging tools for investigating temporal anomalies in message sequences. These scripts can be adapted to analyze specific channels and dates, helping developers understand and resolve complex timezone-related issues.

The comprehensive error handling tests ensure that the system fails gracefully and provides informative error messages, making it easier to diagnose configuration issues and invalid inputs during development.

**Section sources**
- [test_01_range_parameter.sh](file://tests/test_01_range_parameter.sh#L1-L158)
- [test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L1-L244)
- [boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh#L1-L156)
- [BUG_REPORT_message_ordering.md](file://tests/BUG_REPORT_message_ordering.md#L1-L122)
- [PROPOSED_FIX_message_ordering.md](file://tests/PROPOSED_FIX_message_ordering.md#L1-L206)