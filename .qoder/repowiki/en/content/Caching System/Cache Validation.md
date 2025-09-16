# Cache Validation

<cite>
**Referenced Files in This Document**  
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py) - *Updated in recent commit*
- [telegram_manager.sh](file://telegram_manager.sh) - *Modified in recent commit*
- [boundary_detector.py](file://scripts/telegram_tools/boundary_detector.py) - *Added in recent commit*
- [simple_boundary_check.py](file://scripts/telegram_tools/simple_boundary_check.py) - *Added in recent commit*
- [test_05_date_today.sh](file://tests/test_05_date_today.sh)
</cite>

## Update Summary
**Changes Made**  
- Updated cache validation mechanism to include boundary detection integration
- Added new section on boundary detection system and its role in cache validation
- Enhanced TTL rules explanation with integration context
- Updated integration section to reflect boundary detection workflow
- Added troubleshooting steps for boundary-related cache issues
- Updated recovery procedures to include boundary verification commands
- Added new diagram showing boundary detection integration
- Removed outdated references and ensured all examples match current code

## Table of Contents
1. [Introduction](#introduction)
2. [Cache Validation Mechanism](#cache-validation-mechanism)
3. [TTL Rules and Filter Types](#ttl-rules-and-filter-types)
4. [Timestamp Extraction and Age Calculation](#timestamp-extraction-and-age-calculation)
5. [Integration with Telegram Manager](#integration-with-telegram-manager)
6. [Boundary Detection System](#boundary-detection-system)
7. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
8. [Recovery Procedures](#recovery-procedures)
9. [Conclusion](#conclusion)

## Introduction

The cache validation system in this Telegram message processing framework ensures optimal performance by preventing unnecessary API calls while maintaining data freshness. This document explains the intelligent cache validation mechanism that uses time-to-live (TTL) rules based on message recency and filter types. The system balances efficiency with accuracy by determining when cached data remains valid versus when fresh data must be retrieved from the Telegram API.

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L10)
- [telegram_manager.sh](file://telegram_manager.sh#L1-L10)

## Cache Validation Mechanism

The core of the caching system is the `is_cache_valid` function, which determines whether existing cached data can be used or if a fresh fetch from the Telegram API is required. This decision is based on comparing the age of the cache file against predefined TTL thresholds that vary according to the requested data filter type.

The validation process follows these steps:
1. Locate the most recent cache file for the specified channel
2. Calculate the age of the cache file in minutes using `get_cache_age_minutes`
3. Determine the appropriate TTL threshold based on the filter type
4. Compare cache age against TTL to determine validity

This mechanism prevents redundant API calls when data is still fresh, significantly reducing bandwidth usage and improving response times.

```mermaid
flowchart TD
Start([Cache Validation Start]) --> FindCache["Locate Latest Cache File"]
FindCache --> CacheExists{"Cache Exists?"}
CacheExists --> |No| Invalid["Cache Invalid: No File"]
CacheExists --> |Yes| ExtractTime["Extract Timestamp from Filename"]
ExtractTime --> CalculateAge["Calculate Age in Minutes"]
CalculateAge --> DetermineTTL["Determine TTL Based on Filter Type"]
DetermineTTL --> Compare["Compare Age vs TTL"]
Compare --> Valid{"Age < TTL?"}
Valid --> |Yes| CacheValid["Cache Valid: Use Cached Data"]
Valid --> |No| CacheStale["Cache Stale: Fetch Fresh Data"]
CacheStale --> End([Validation Complete])
CacheValid --> End
Invalid --> End
```

**Diagram sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)

## TTL Rules and Filter Types

The cache system implements different TTL values based on the recency and importance of the requested data. The `CACHE_TTL` configuration defines three distinct thresholds:

| Filter Type | Description | TTL (Minutes) | Use Case |
|-----------|-------------|---------------|---------|
| "today" | Messages from the current day | 5 | High-frequency updates, real-time monitoring |
| "recent" | Messages from the last 7 days | 60 | Recent activity, daily summaries |
| "archive" | Messages older than 7 days | 1440 | Historical data, infrequent access |

The `is_cache_valid` function maps various filter types to these TTL categories:
- **"today"**: Directly uses the 5-minute TTL for maximum freshness
- **"last:N"**: Uses "recent" TTL (60 minutes) if N ≤ 7, otherwise "archive" TTL (1440 minutes)
- **"yesterday" and "all"**: Use "recent" TTL (60 minutes)
- **Specific dates**: Default to "archive" TTL (1440 minutes)

This tiered approach ensures that frequently changing data is refreshed more often while stable historical data uses longer cache durations.

```mermaid
graph TD
FilterType[Filter Type] --> Today{"today?"}
Today --> |Yes| TTL5["TTL = 5 min"]
Today --> |No| LastN{"last:N?"}
LastN --> |Yes| DaysCheck{"N ≤ 7?"}
DaysCheck --> |Yes| TTL60["TTL = 60 min"]
DaysCheck --> |No| TTL1440["TTL = 1440 min"]
LastN --> |No| YesterdayAll{"yesterday or all?"}
YesterdayAll --> |Yes| TTL60
YesterdayAll --> |No| SpecificDate["Specific Date"]
SpecificDate --> TTL1440
```

**Diagram sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L13-L17)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L13-L17)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)

## Timestamp Extraction and Age Calculation

The system determines cache age by extracting timestamps from cache filenames using the `get_cache_age_minutes` function. Cache files follow a consistent naming convention: `channel_YYYYMMDD_HHMMSS.json`, where the timestamp portion (YYYYMMDD_HHMMSS) indicates when the cache was created.

The timestamp extraction process:
1. Parse the filename stem (without extension)
2. Extract the last two underscore-separated components as the timestamp
3. Combine them into YYYYMMDD_HHMMSS format
4. Convert to a datetime object
5. Calculate the difference from the current time in minutes

If the timestamp cannot be parsed (due to filename corruption or format changes), the function returns infinity, which automatically invalidates the cache and triggers a fresh data fetch.

```mermaid
sequenceDiagram
participant User as "User Request"
participant Manager as "telegram_manager.sh"
participant Cache as "telegram_cache.py"
participant System as "File System"
User->>Manager : Request with filter type
Manager->>Cache : check <channel> <filter_type>
Cache->>System : Find latest cache file
System-->>Cache : Return file path
Cache->>Cache : Extract timestamp from filename
Cache->>Cache : Calculate age in minutes
Cache->>Cache : Determine TTL based on filter
Cache->>Manager : Return validity status
Manager->>User : Proceed with cached or fresh data
```

**Diagram sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L19-L30)
- [telegram_manager.sh](file://telegram_manager.sh#L33-L38)

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L19-L30)

## Integration with Telegram Manager

The cache validation system integrates seamlessly with the main `telegram_manager.sh` script, which serves as the primary interface for users. When a user requests messages with a specific filter, the manager script first checks cache validity before deciding whether to use cached data or fetch fresh messages.

The integration workflow:
1. User issues a read command with a filter type
2. The manager script calls `telegram_cache.py check` with the channel and filter
3. If the cache is valid, it uses the cached data
4. If the cache is stale, it triggers a fresh fetch via `telegram_fetch.py`

This integration significantly reduces API calls and improves response times, especially for frequently accessed recent data.

```mermaid
graph TB
subgraph UserInterface["User Interface"]
CLI[Command Line]
end
subgraph Manager["telegram_manager.sh"]
ReadCmd["read command"]
CacheCheck["Cache Validation Check"]
UseCache["Use Cached Data"]
FetchNew["Fetch Fresh Data"]
end
subgraph CacheSystem["Cache System"]
CacheScript[telegram_cache.py]
CacheFiles[(Cache Files)]
end
subgraph TelegramAPI["Telegram API"]
FetchScript[telegram_fetch.py]
API[Telegram API]
end
CLI --> ReadCmd
ReadCmd --> CacheCheck
CacheCheck --> CacheScript
CacheScript --> CacheFiles
CacheScript --> CacheCheck
CacheCheck --> |Valid| UseCache
CacheCheck --> |Stale| FetchNew
FetchNew --> FetchScript
FetchScript --> API
FetchScript --> CacheFiles
UseCache --> CLI
FetchNew --> CLI
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L27-L42)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L27-L42)

## Boundary Detection System

The recent enhancement integrates boundary detection into the cache validation logic to improve accuracy and prevent data truncation. The system now includes a sophisticated boundary detection mechanism that verifies cache completeness and freshness beyond simple TTL checks.

The boundary detection system consists of:
- **Simple boundary check**: Basic staleness verification using `simple_boundary_check.py`
- **Sophisticated boundary detection**: Advanced analysis using `boundary_detector.py` that checks both temporal boundaries and message completeness
- **Triple verification**: Uses three different Telegram API methods to ensure 100% confidence in boundary detection

Key features of the boundary detection system:
- Checks if the latest message in cache is still current
- Verifies if there are messages before the earliest cached message
- Performs expansion when boundaries are found to be stale
- Generates detailed verification reports with confidence scoring
- Integrates with Moscow timezone-aware date handling

The system is accessible through the `telegram_manager.sh` script with commands:
- `verify-boundaries`: Ultimate boundary detection with triple verification
- `test-boundaries`: Comprehensive multi-day boundary testing
- `verify-content`: Verify cache against live data with auto-correction

```mermaid
graph TD
A[User Request] --> B[Cache Validation]
B --> C{Cache Valid?}
C --> |Yes| D[Use Cached Data]
C --> |No| E[Boundary Detection]
E --> F[Check Live Boundaries]
F --> G{Boundaries Fresh?}
G --> |Yes| H[Update Cache]
G --> |No| I[Smart Cache Expansion]
I --> J[Save Expanded Cache]
J --> K[Return Data]
H --> K
D --> K
```

**Diagram sources**
- [boundary_detector.py](file://scripts/telegram_tools/boundary_detector.py#L1-L50)
- [telegram_manager.sh](file://telegram_manager.sh#L27-L42)

**Section sources**
- [boundary_detector.py](file://scripts/telegram_tools/boundary_detector.py#L1-L50)
- [simple_boundary_check.py](file://scripts/telegram_tools/simple_boundary_check.py#L1-L10)

## Common Issues and Troubleshooting

Several common issues can affect cache validation, along with their troubleshooting steps:

### 1. Incorrect Timestamp Parsing
**Symptoms**: Cache files are consistently invalidated even when recently created  
**Causes**: 
- Filename format changes or corruption
- System clock synchronization issues
- Incorrect timestamp extraction logic

**Troubleshooting**:
- Verify cache filenames follow the `channel_YYYYMMDD_HHMMSS.json` pattern
- Check system time and timezone settings
- Test the `get_cache_age_minutes` function with sample filenames

### 2. Unexpected Cache Invalidation
**Symptoms**: Frequent fresh data fetches despite recent cache updates  
**Causes**:
- TTL values too short for the use case
- Clock drift between systems
- Filter type misclassification

**Troubleshooting**:
- Review the TTL mapping logic in `is_cache_valid`
- Check that filter types are correctly passed to the validation function
- Verify the cache file creation timestamp matches system time

### 3. Stale Data Usage
**Symptoms**: Outdated information displayed despite changes in the source  
**Causes**:
- TTL values too long for dynamic content
- Cache validation bypassed in the workflow
- Incorrect age calculation

**Troubleshooting**:
- Verify the age calculation in `get_cache_age_minutes`
- Check that the most recent cache file is being selected
- Confirm the validation result is properly interpreted by the manager script

### 4. Boundary Detection Issues
**Symptoms**: Cache appears valid but missing recent messages  
**Causes**:
- Boundary detection not properly configured
- Telegram API connectivity issues
- Message ID gaps in the sequence

**Troubleshooting**:
- Run `./telegram_manager.sh verify-boundaries <channel> <date>` to check boundaries
- Verify Telegram API credentials in `.env` file
- Check network connectivity to Telegram servers
- Review boundary detection logs in `./telegram_verification/`

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L19-L30)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L32-L57)
- [telegram_manager.sh](file://telegram_manager.sh#L33-L38)
- [boundary_detector.py](file://scripts/telegram_tools/boundary_detector.py#L1-L50)

## Recovery Procedures

When cache validation issues occur, follow these recovery procedures:

### 1. Manual Cache Cleanup
Force removal of old cache files and refresh data:
```bash
# Clean cache for specific channel
./telegram_manager.sh clean aiclubsweggs

# Or use direct cache script
python3 scripts/telegram_tools/core/telegram_cache.py clean aiclubsweggs
```

### 2. Cache Validation Testing
Test the validation logic independently:
```bash
# Check cache status for a channel
python3 scripts/telegram_tools/core/telegram_cache.py check aiclubsweggs today

# View detailed cache information
python3 scripts/telegram_tools/core/telegram_cache.py info
```

### 3. Forced Fresh Fetch
Bypass cache validation and retrieve fresh data:
```bash
# Using --clean flag
./telegram_manager.sh read aiclubsweggs today --clean

# Or clean_cache parameter
./telegram_manager.sh read aiclubsweggs clean_cache
```

### 4. Boundary Verification
Verify and correct cache boundaries:
```bash
# Run boundary verification
./telegram_manager.sh verify-boundaries aiclubsweggs 2025-09-14

# Test boundaries across multiple days
./telegram_manager.sh test-boundaries aiclubsweggs 2025-09-14 7

# Verify cache content against live data
./telegram_manager.sh verify-content telegram_cache/aiclubsweggs_20250915_224022.json --auto-correct
```

### 5. Systematic Verification
Use test scripts to verify date handling:
```bash
# Run date calculation tests
./tests/test_05_date_today.sh
```

These procedures ensure reliable recovery from cache validation issues while maintaining data integrity.

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L60-L100)
- [telegram_manager.sh](file://telegram_manager.sh#L50-L55)
- [test_05_date_today.sh](file://tests/test_05_date_today.sh#L1-L52)
- [boundary_detector.py](file://scripts/telegram_tools/boundary_detector.py#L1-L50)

## Conclusion

The cache validation mechanism provides an intelligent balance between data freshness and system efficiency. By implementing tiered TTL rules based on filter types and accurately calculating cache age from filenames, the system minimizes unnecessary API calls while ensuring users receive timely information. The integration with the telegram_manager.sh script creates a seamless user experience, automatically handling cache validation behind the scenes. The enhanced boundary detection system adds an additional layer of verification to ensure cache completeness and prevent data truncation. Understanding the TTL rules, timestamp extraction process, boundary detection workflow, and troubleshooting procedures enables effective maintenance and optimization of the caching system.