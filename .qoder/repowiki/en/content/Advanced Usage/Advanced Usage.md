# Advanced Usage

<cite>
**Referenced Files in This Document**   
- [telegram_manager.sh](file://telegram_manager.sh)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh)
- [tests/test_ordering_integration.sh](file://tests/test_ordering_integration.sh)
</cite>

## Table of Contents
1. [Scripting Patterns for Message Monitoring](#scripting-patterns-for-message-monitoring)
2. [Command Pipelines for Complex Operations](#command-pipelines-for-complex-operations)
3. [Advanced Filtering Techniques](#advanced-filtering-techniques)
4. [Integration with External Analysis Tools](#integration-with-external-analysis-tools)
5. [Direct Python Module Utilization](#direct-python-module-utilization)
6. [Performance Optimization](#performance-optimization)
7. [Extending the System](#extending-the-system)
8. [Notification Systems and Scheduled Tasks](#notification-systems-and-scheduled-tasks)

## Scripting Patterns for Message Monitoring

The system provides robust scripting patterns for automating message monitoring workflows. The primary entry point is `telegram_manager.sh`, which orchestrates various Python modules for message retrieval, filtering, and analysis. For continuous monitoring, implement a polling pattern using the `read` command with appropriate cache behavior. Use `--clean` flag when real-time accuracy is critical, though this increases API load. For high-frequency monitoring, combine `cache check` with conditional fetching to minimize unnecessary API calls. The `fetch` command enables targeted retrieval of message batches, while `json` export supports structured data extraction for downstream processing. Implement boundary detection scripts like `comprehensive_message_analysis.sh` to handle edge cases around date transitions, particularly important for timezone-sensitive applications.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L115)

## Command Pipelines for Complex Operations

Complex operations can be achieved by combining multiple commands in pipelines. Chain `telegram_manager.sh` commands with standard Unix utilities to create powerful workflows. For example, pipe `read` output to `grep` for additional text filtering, or use `json` export with `jq` for sophisticated JSON processing. The `telegram_json_export.py` module's `--full` output can be piped to external analytics tools, while `--summary` provides concise metadata for monitoring dashboards. Combine `cache info` with `clean` in maintenance scripts to manage storage efficiently. Use process substitution to compare outputs from different filter types or channels simultaneously. The test scripts demonstrate advanced pipeline patterns, such as using `awk` for date-section filtering and `grep` with context flags for message context analysis.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L125)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L115)

## Advanced Filtering Techniques

The system implements sophisticated filtering capabilities through `telegram_filter.py`. Beyond basic date filters (`today`, `yesterday`, `last:N`), the system supports pattern matching with regular expressions and message limiting. The filtering process includes intelligent border detection that validates date boundaries by examining adjacent messages, automatically triggering additional data fetching when validation cannot be completed with available cache. For timezone-aware filtering, use the `telegram_smart_cache.py` script which ensures complete time range coverage by scanning messages until the start of the requested period is confirmed. The fallback border detection mechanism checks 3-7 messages preceding the first filtered message to verify date transitions, enhancing accuracy in boundary cases.

**Section sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py#L1-L244)

## Integration with External Analysis Tools

The system facilitates integration with external analysis tools through structured JSON output. The `telegram_json_export.py` module provides raw JSON export capabilities suitable for ingestion by data analysis platforms. Use `--full` mode to obtain complete message datasets for machine learning applications or sentiment analysis. The `export_range_summary` function generates concise metadata summaries ideal for dashboard integration. For time-series analysis, combine the JSON output with tools like Pandas or Elasticsearch. The comprehensive test scripts demonstrate integration patterns with text processing tools (`awk`, `grep`, `sed`) for message context analysis and visualization. Export data can be piped directly to visualization tools or loaded into databases for long-term trend analysis.

**Section sources**
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L125)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L115)

## Direct Python Module Utilization

For specialized use cases, leverage the underlying Python modules directly. The core modules (`telegram_fetch.py`, `telegram_filter.py`, `telegram_cache.py`) expose their functionality through well-defined functions that can be imported into custom scripts. Import `fetch_and_cache` for programmatic message retrieval with custom parameters, or use `filter_messages` to integrate filtering logic into larger applications. The `is_cache_valid` function from `telegram_cache.py` enables custom cache management strategies. When extending functionality, follow the modular design pattern evident in the codebase, maintaining separation between data retrieval, processing, and presentation layers. Direct module usage bypasses the Bash wrapper, providing finer control over parameters and error handling.

**Section sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L147)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L179)

## Performance Optimization

Optimize performance through cache tuning and batch operations. The system implements intelligent TTL rules in `telegram_cache.py`, with different expiration times for various filter types (`today`: 5 minutes, `recent`: 60 minutes, `archive`: 1440 minutes). Adjust these values based on your use case and API rate limits. Use `clean_old_caches` with appropriate `keep_latest` parameters to balance storage usage and retrieval speed. For large datasets, employ `telegram_fetch_large.py` (referenced in project structure) to handle pagination efficiently. The `limit` parameter in fetch operations prevents excessive memory usage. When processing large volumes, implement batch operations by processing cache files in chunks rather than loading entire datasets into memory. The smart caching strategy in `telegram_smart_cache.py` optimizes data retrieval by scanning only the necessary message range.

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L179)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py#L1-L244)

## Extending the System

Extend the system by adding new filter types or export formats. The modular architecture allows for straightforward extension of functionality. To add a new filter type, modify the `filter_messages` function in `telegram_filter.py` to handle additional filter specifications. For new export formats, create a companion script to `telegram_json_export.py` that transforms the message data structure into the desired format (CSV, XML, etc.). The system's design pattern of separating concerns—fetching, caching, filtering, and exporting—provides a clear template for new components. The test suite (`test_ordering_integration.sh`) demonstrates how to validate new functionality through integration testing. When adding features, maintain consistency with existing error handling and logging patterns.

**Section sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L125)
- [tests/test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L183)

## Notification Systems and Scheduled Tasks

Integrate with notification systems and schedule tasks using standard Unix tools. Configure cron jobs to run monitoring scripts at regular intervals, using the output to trigger notifications. The `send` command in `telegram_manager.sh` enables bidirectional communication, allowing the system to send alerts to specified targets. Combine cache status checks with message analysis in scheduled scripts to detect anomalies and send alerts when specific conditions are met. Use the exit codes from cache validation (`check` command) to trigger different notification levels—stale cache might generate a warning, while failed message detection could trigger a critical alert. The test scripts provide patterns for capturing and processing command output for notification content.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)
- [tests/test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L183)