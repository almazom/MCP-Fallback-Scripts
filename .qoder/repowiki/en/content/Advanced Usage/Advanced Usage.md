# Advanced Usage

<cite>
**Referenced Files in This Document**   
- [telegram_manager.sh](file://telegram_manager.sh) - *Updated with new archive, restore, validate, and anchor commands*
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py) - *Enhanced with temporal anchoring and Moscow timezone support*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py) - *Updated border detection with auto-fetch capability*
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py) - *JSON export functionality*
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py) - *Cache management with TTL rules*
- [scripts/telegram_tools/core/daily_persistence.py](file://scripts/telegram_tools/core/daily_persistence.py) - *Added in recent commit for permanent daily storage*
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py) - *Added in recent commit for message boundary anchoring*
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py) - *Added in recent commit for message completeness validation*
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh) - *Comprehensive analysis script*
</cite>

## Update Summary
**Changes Made**   
- Updated all sections to reflect the new JSON-based architecture and advanced features
- Added new sections for Daily Persistence, Temporal Anchoring, and Gap Validation
- Enhanced existing sections with new command examples and integration patterns
- Updated section sources to include newly added Python modules
- Added performance optimization details for the new persistence and anchoring systems

## Table of Contents
1. [Scripting Patterns for Message Monitoring](#scripting-patterns-for-message-monitoring)
2. [Command Pipelines for Complex Operations](#command-pipelines-for-complex-operations)
3. [Advanced Filtering Techniques](#advanced-filtering-techniques)
4. [Integration with External Analysis Tools](#integration-with-external-analysis-tools)
5. [Direct Python Module Utilization](#direct-python-module-utilization)
6. [Performance Optimization](#performance-optimization)
7. [Extending the System](#extending-the-system)
8. [Notification Systems and Scheduled Tasks](#notification-systems-and-scheduled-tasks)
9. [Daily Persistence System](#daily-persistence-system)
10. [Temporal Anchoring System](#temporal-anchoring-system)
11. [Gap Validation System](#gap-validation-system)

## Scripting Patterns for Message Monitoring

The system provides robust scripting patterns for automating message monitoring workflows. The primary entry point is `telegram_manager.sh`, which orchestrates various Python modules for message retrieval, filtering, and analysis. For continuous monitoring, implement a polling pattern using the `read` command with appropriate cache behavior. Use `--clean` flag when real-time accuracy is critical, though this increases API load. For high-frequency monitoring, combine `cache check` with conditional fetching to minimize unnecessary API calls. The `fetch` command enables targeted retrieval of message batches, while `json` export supports structured data extraction for downstream processing. Implement boundary detection scripts like `comprehensive_message_analysis.sh` to handle edge cases around date transitions, particularly important for timezone-sensitive applications. The new temporal anchoring system ensures accurate message boundary detection by maintaining anchor points for daily message sequences.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L114)
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*

## Command Pipelines for Complex Operations

Complex operations can be achieved by combining multiple commands in pipelines. Chain `telegram_manager.sh` commands with standard Unix utilities to create powerful workflows. For example, pipe `read` output to `grep` for additional text filtering, or use `json` export with `jq` for sophisticated JSON processing. The `telegram_json_export.py` module's `--full` output can be piped to external analytics tools, while `--summary` provides concise metadata for monitoring dashboards. Combine `cache info` with `clean` in maintenance scripts to manage storage efficiently. Use process substitution to compare outputs from different filter types or channels simultaneously. The test scripts demonstrate advanced pipeline patterns, such as using `awk` for date-section filtering and `grep` with context flags for message context analysis. New commands like `validate` and `anchor` can be integrated into pipelines for comprehensive message validation workflows.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L124)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L114)

## Advanced Filtering Techniques

The system implements sophisticated filtering capabilities through `telegram_filter.py`. Beyond basic date filters (`today`, `yesterday`, `last:N`), the system supports pattern matching with regular expressions and message limiting. The filtering process includes intelligent border detection that validates date boundaries by examining adjacent messages, automatically triggering additional data fetching when validation cannot be completed with available cache. For timezone-aware filtering, use the temporal anchoring system which ensures complete time range coverage by scanning messages until the start of the requested period is confirmed. The fallback border detection mechanism checks 3-7 messages preceding the first filtered message to verify date transitions, enhancing accuracy in boundary cases. The system now automatically fetches additional messages when border validation cannot be completed with the current cache.

**Section sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*

## Integration with External Analysis Tools

The system facilitates integration with external analysis tools through structured JSON output. The `telegram_json_export.py` module provides raw JSON export capabilities suitable for ingestion by data analysis platforms. Use `--full` mode to obtain complete message datasets for machine learning applications or sentiment analysis. The `export_range_summary` function generates concise metadata summaries ideal for dashboard integration. For time-series analysis, combine the JSON output with tools like Pandas or Elasticsearch. The comprehensive test scripts demonstrate integration patterns with text processing tools (`awk`, `grep`, `sed`) for message context analysis and visualization. Export data can be piped directly to visualization tools or loaded into databases for long-term trend analysis. The new gap validation system provides comprehensive validation reports that can be integrated into monitoring dashboards.

**Section sources**
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L124)
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L1-L114)
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py#L1-L465) - *Added in recent commit*

## Direct Python Module Utilization

For specialized use cases, leverage the underlying Python modules directly. The core modules (`telegram_fetch.py`, `telegram_filter.py`, `telegram_cache.py`) expose their functionality through well-defined functions that can be imported into custom scripts. Import `fetch_and_cache` for programmatic message retrieval with custom parameters, or use `filter_messages` to integrate filtering logic into larger applications. The `is_cache_valid` function from `telegram_cache.py` enables custom cache management strategies. When extending functionality, follow the modular design pattern evident in the codebase, maintaining separation between data retrieval, processing, and presentation layers. Direct module usage bypasses the Bash wrapper, providing finer control over parameters and error handling. The new `TemporalAnchor`, `DailyPersistence`, and `GapValidator` classes provide advanced functionality for message boundary management and data validation.

**Section sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L193)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*
- [scripts/telegram_tools/core/daily_persistence.py](file://scripts/telegram_tools/core/daily_persistence.py#L1-L305) - *Added in recent commit*
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py#L1-L465) - *Added in recent commit*

## Performance Optimization

Optimize performance through cache tuning and batch operations. The system implements intelligent TTL rules in `telegram_cache.py`, with different expiration times for various filter types (`today`: 5 minutes, `recent`: 60 minutes, `archive`: 1440 minutes). Adjust these values based on your use case and API rate limits. Use `clean_old_caches` with appropriate `keep_latest` parameters to balance storage usage and retrieval speed. For large datasets, employ `telegram_fetch_large.py` (referenced in project structure) to handle pagination efficiently. The `limit` parameter in fetch operations prevents excessive memory usage. When processing large volumes, implement batch operations by processing cache files in chunks rather than loading entire datasets into memory. The smart caching strategy in `telegram_smart_cache.py` optimizes data retrieval by scanning only the necessary message range. The temporal anchoring system reduces unnecessary API calls by maintaining optimal fetch offsets.

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py#L1-L244)
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*

## Extending the System

Extend the system by adding new filter types or export formats. The modular architecture allows for straightforward extension of functionality. To add a new filter type, modify the `filter_messages` function in `telegram_filter.py` to handle additional filter specifications. For new export formats, create a companion script to `telegram_json_export.py` that transforms the message data structure into the desired format (CSV, XML, etc.). The system's design pattern of separating concerns—fetching, caching, filtering, and exporting—provides a clear template for new components. The test suite (`test_ordering_integration.sh`) demonstrates how to validate new functionality through integration testing. When adding features, maintain consistency with existing error handling and logging patterns. The new `DailyPersistence` and `GapValidator` classes demonstrate the extensible architecture that can be used as templates for additional functionality.

**Section sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L124)
- [tests/test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L183)
- [scripts/telegram_tools/core/daily_persistence.py](file://scripts/telegram_tools/core/daily_persistence.py#L1-L305) - *Added in recent commit*
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py#L1-L465) - *Added in recent commit*

## Notification Systems and Scheduled Tasks

Integrate with notification systems and schedule tasks using standard Unix tools. Configure cron jobs to run monitoring scripts at regular intervals, using the output to trigger notifications. The `send` command in `telegram_manager.sh` enables bidirectional communication, allowing the system to send alerts to specified targets. Combine cache status checks with message analysis in scheduled scripts to detect anomalies and send alerts when specific conditions are met. Use the exit codes from cache validation (`check` command) to trigger different notification levels—stale cache might generate a warning, while failed message detection could trigger a critical alert. The test scripts provide patterns for capturing and processing command output for notification content. The new `validate` command can be used in scheduled tasks to ensure message completeness and trigger alerts for detected gaps.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [tests/test_ordering_integration.sh](file://tests/test_ordering_integration.sh#L1-L183)
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py#L1-L465) - *Added in recent commit*

## Daily Persistence System

The Daily Persistence system provides permanent storage for complete daily message caches, ensuring data durability and enabling historical analysis. Implemented through `daily_persistence.py`, this system archives daily message caches to a dedicated storage location, separate from the temporary cache directory. The `archive` command stores the current cache as a permanent daily record, while the `restore` command retrieves archived data for analysis. This system supports retention policies through the `cleanup` command, which removes old archives based on configurable retention periods. The `list` and `stats` commands provide visibility into stored archives, including size, date ranges, and channel coverage. This functionality is essential for compliance, auditing, and long-term trend analysis.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [scripts/telegram_tools/core/daily_persistence.py](file://scripts/telegram_tools/core/daily_persistence.py#L1-L305) - *Added in recent commit*

## Temporal Anchoring System

The Temporal Anchoring system ensures accurate message boundary detection by maintaining anchor points for daily message sequences. Implemented through `temporal_anchor.py`, this system records the last message ID and timestamp for each day, enabling intelligent message fetching that respects date boundaries. The `anchor set` command establishes a new anchor point, while `anchor get` retrieves existing anchors. The `anchor offset` command calculates optimal fetch offsets based on anchor data, minimizing API calls while ensuring complete data retrieval. This system automatically updates anchors during message fetching, maintaining up-to-date boundary information. The anchoring system is particularly valuable for timezone-sensitive applications where message boundaries might otherwise be ambiguous.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L193)
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*

## Gap Validation System

The Gap Validation system ensures message completeness by detecting and reporting gaps in message sequences. Implemented through `gap_validator.py`, this system performs comprehensive validation of message data, checking for sequence gaps, boundary integrity, and temporal continuity. The `validate` command runs a complete assessment, providing a confidence score and detailed analysis of potential data issues. The system distinguishes between minor gaps (likely deletions) and significant gaps that may indicate data loss. It also validates message boundaries against temporal anchors and checks continuity between consecutive days. This functionality is critical for applications requiring high data integrity, providing early warning of potential message retrieval issues.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L165)
- [scripts/telegram_tools/core/gap_validator.py](file://scripts/telegram_tools/core/gap_validator.py#L1-L465) - *Added in recent commit*
- [scripts/telegram_tools/core/temporal_anchor.py](file://scripts/telegram_tools/core/temporal_anchor.py#L1-L481) - *Added in recent commit*
- [scripts/telegram_tools/core/daily_persistence.py](file://scripts/telegram_tools/core/daily_persistence.py#L1-L305) - *Added in recent commit*