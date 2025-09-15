# Key Features and Use Cases

<cite>
**Referenced Files in This Document**   
- [telegram_manager.sh](file://telegram_manager.sh)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py)
</cite>

## Table of Contents
1. [Message Fetching with Configurable Limits](#message-fetching-with-configurable-limits)
2. [Intelligent Caching with Automatic Freshness Validation](#intelligent-caching-with-automatic-freshness-validation)
3. [Message Reading with Flexible Filtering](#message-reading-with-flexible-filtering)
4. [JSON Data Export for Analysis](#json-data-export-for-analysis)
5. [Message Delivery via Send Command](#message-delivery-via-send-command)
6. [Feature Interactions and Workflow Integration](#feature-interactions-and-workflow-integration)
7. [Real-World Use Cases](#real-world-use-cases)

## Message Fetching with Configurable Limits

The FALLBACK_SCRIPTS tool enables users to fetch messages from Telegram channels with customizable limits. Using the `fetch` command in `telegram_manager.sh`, users can specify a channel and an optional message limit (defaulting to 200). The core functionality is implemented in `telegram_fetch.py`, which retrieves messages via the Telethon library and stores them in JSON format with comprehensive metadata including message ID, timestamps in UTC and Moscow time, sender information, views, forwards, and reply context.

The fetch operation supports optional parameters such as offset ID and suffix for advanced use cases, allowing pagination and batch differentiation. Each fetch creates a timestamped cache file in the `telegram_cache` directory, preserving historical data while enabling version control of message snapshots.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L15-L22)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L147)

## Intelligent Caching with Automatic Freshness Validation

The tool implements a sophisticated caching system with automatic freshness validation based on time-sensitive TTL (Time To Live) rules. The `telegram_cache.py` module defines different TTL values depending on the recency of the requested data: 5 minutes for today's messages, 60 minutes for recent data (last 7 days), and 1440 minutes (24 hours) for archival content.

When reading messages, the system automatically checks cache validity using `is_cache_valid()`. If the cache is stale according to the TTL rules, it triggers a fresh fetch. Users can also force cache refresh using the `--clean` or `clean_cache` flags. The cache management includes automatic cleanup of old files, retaining only the most recent versions per channel to optimize disk usage.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L24-L58)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L179)

## Message Reading with Flexible Filtering

Users can read cached messages with flexible filtering options through the `read` command. Supported filters include `today`, `yesterday`, `last:N` (where N is a number of days), specific dates in YYYY-MM-DD format, and `all` for complete history. The filtering logic is implemented in `telegram_filter.py`, which processes the most recent cache file and applies date-based filtering.

The system includes intelligent border detection that validates the accuracy of date-based filtering by examining messages immediately preceding the filtered set. If insufficient data exists for proper border validation, the system automatically triggers additional message fetching to ensure accurate date boundary detection, particularly important for timezone-sensitive applications.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L24-L58)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)

## JSON Data Export for Analysis

For data analysis and integration purposes, the tool provides JSON export functionality through the `json` command. This feature, implemented in `telegram_json_export.py`, allows exporting filtered message sets in raw JSON format. Two output modes are available: `--summary` (default) provides a concise overview with first/last message details and time range, while `--full` exports the complete message set with all metadata.

The JSON export preserves all message attributes including text content, timestamps, sender information, engagement metrics (views, forwards), and reply relationships, making it suitable for external analysis tools, reporting systems, or database import operations.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L100-L106)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L125)

## Message Delivery via Send Command

The tool includes a `send` command for delivering messages to Telegram targets. Implemented as an inline Python script within `telegram_manager.sh`, this feature uses Telethon to establish a connection using credentials from a `.env` file (containing API ID, API hash, and session string). The send operation supports both user mentions (e.g., @username) and direct chat IDs as targets.

This functionality enables automated notifications, alerting systems, and message broadcasting capabilities, integrating seamlessly with the message retrieval features to create bidirectional Telegram interactions.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L59-L98)

## Feature Interactions and Workflow Integration

The various features of FALLBACK_SCRIPTS are designed to work together in a cohesive workflow. The filtering system depends entirely on cached data, creating a dependency chain where reading operations may trigger automatic fetching when cache freshness thresholds are exceeded. The cache status directly determines whether a fetch operation is necessary, implementing an intelligent lazy-loading pattern.

The smart caching strategy in `telegram_smart_cache.py` enhances this interaction by ensuring complete time range coverage during fetch operations, preventing truncation issues that could affect filtering accuracy. This is particularly important for daily monitoring use cases where complete message coverage for specific time periods is critical.

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L15-L106)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L179)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py#L1-L244)

## Real-World Use Cases

### Daily Message Monitoring
Organizations can use the tool to automatically monitor Telegram channels daily by fetching and filtering messages from the previous day. The intelligent caching ensures fresh data is retrieved each morning while minimizing unnecessary API calls during the day.

### Content Analysis
Researchers can export complete message histories in JSON format for linguistic analysis, sentiment tracking, or topic modeling. The rich metadata enables sophisticated analysis of engagement patterns, message propagation, and content evolution over time.

### Automated Reporting
The combination of filtering and JSON export enables automated report generation. For example, a daily report could be generated by fetching yesterday's messages, filtering for specific keywords, and exporting the results to a dashboard system.

### Practical Examples
- Fetch 100 messages: `./telegram_manager.sh fetch aiclubsweggs 100`
- Read yesterday's messages with auto-refresh: `./telegram_manager.sh read aiclubsweggs yesterday`
- Export full history: `./telegram_manager.sh json aiclubsweggs all --full`
- Send notification: `./telegram_manager.sh send @manager "Daily report ready"`

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L108-L146)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L147)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L239)
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L1-L125)