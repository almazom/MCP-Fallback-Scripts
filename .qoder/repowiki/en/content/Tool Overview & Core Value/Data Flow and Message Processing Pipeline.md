# Data Flow and Message Processing Pipeline

<cite>
**Referenced Files in This Document**   
- [telegram_manager.sh](file://telegram_manager.sh)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py)
- [scripts/telegram_tools/telegram_smart_cache.py](file://scripts/telegram_tools/telegram_smart_cache.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [End-to-End Data Flow Overview](#end-to-end-data-flow-overview)
3. [Cache Validation and TTL Management](#cache-validation-and-ttl-management)
4. [Message Fetching and Caching Strategy](#message-fetching-and-caching-strategy)
5. [Message Filtering and Border Detection](#message-filtering-and-border-detection)
6. [Conditional Logic in the 'read' Command](#conditional-logic-in-the-read-command)
7. [Message Processing Pipeline](#message-processing-pipeline)
8. [Cache Integrity and Edge Case Handling](#cache-integrity-and-edge-case-handling)
9. [Performance Implications and Optimization](#performance-implications-and-optimization)

## Introduction
The FALLBACK_SCRIPTS system implements a robust message processing pipeline for Telegram channels, designed to balance performance, accuracy, and reliability. This document details the end-to-end data flow from user command execution through cache validation, message fetching, filtering, and final output. The system employs intelligent caching strategies, timezone-aware timestamp handling, and sophisticated border detection to ensure message integrity across cache boundaries.

## End-to-End Data Flow Overview
The system processes user requests through a coordinated pipeline involving shell orchestration, Python-based caching logic, message fetching, and content filtering. The primary entry point is the `telegram_manager.sh` script, which routes commands to specialized Python modules responsible for cache management, API interaction, and data processing.

```mermaid
flowchart TD
User["User Command\n(e.g., ./telegram_manager.sh read)"] --> Manager["telegram_manager.sh"]
Manager --> CacheCheck["telegram_cache.py\nis_cache_valid()"]
CacheCheck --> |Cache Valid| Filter["telegram_filter.py\nfilter_messages()"]
CacheCheck --> |Cache Stale| Fetch["telegram_fetch.py\nfetch_and_cache()"]
Fetch --> Cache["Write to telegram_cache/"]
Cache --> Filter
Filter --> Output["Formatted Message Output"]
style User fill:#f9f,stroke:#333
style Output fill:#bbf,stroke:#333
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)

## Cache Validation and TTL Management
The system implements a tiered TTL (Time-To-Live) strategy based on message recency, ensuring fresh data for recent messages while conserving bandwidth for archival content. Cache validity is determined by the `is_cache_valid()` function in `telegram_cache.py`, which applies different TTL rules based on filter type.

```mermaid
flowchart TD
Start["Start: is_cache_valid(channel, filter_type)"] --> Extract["Extract timestamp from\nlatest cache filename"]
Extract --> Age["Calculate cache age in minutes"]
Age --> Decision["Determine TTL based on filter_type"]
Decision --> Today{"filter_type == 'today'?"}
Today --> |Yes| Set5Min["TTL = 5 minutes"]
Today --> |No| Recent{"filter_type starts with 'last:'?"}
Recent --> |Yes| Days["Extract days from filter"]
Days --> Check7["days <= 7?"]
Check7 --> |Yes| Set60Min["TTL = 60 minutes"]
Check7 --> |No| Set1440Min["TTL = 1440 minutes"]
Recent --> |No| Yesterday{"filter_type in ['yesterday', 'all']?"}
Yesterday --> |Yes| Set60Min
Yesterday --> |No| Set1440Min
Set60Min --> Compare["age_minutes < ttl?"]
Set1440Min --> Compare
Set5Min --> Compare
Compare --> |Yes| Valid["Return: True, latest_cache"]
Compare --> |No| Stale["Return: False, latest_cache"]
style Start fill:#f9f,stroke:#333
style Valid fill:#9f9,stroke:#333
style Stale fill:#f99,stroke:#333
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L45-L98)

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)

## Message Fetching and Caching Strategy
The message fetching process, implemented in `telegram_fetch.py`, retrieves messages from Telegram's API and stores them in JSON format with comprehensive metadata. The system uses Moscow time (UTC+3) for all displayed timestamps, ensuring consistency across timezones. Each cache file includes metadata about the fetch operation, including request parameters and caching time.

```mermaid
sequenceDiagram
participant User as "User"
participant Manager as "telegram_manager.sh"
participant Fetch as "telegram_fetch.py"
participant Telegram as "Telegram API"
participant CacheDir as "telegram_cache/"
User->>Manager : read command with filter
Manager->>Fetch : Execute fetch_and_cache()
Fetch->>Telegram : GetHistoryRequest<br/>with offset_id=0, limit=100
Telegram-->>Fetch : Message batch with metadata
Fetch->>Fetch : Convert UTC to Moscow time<br/>Extract sender info<br/>Process media indicators
Fetch->>CacheDir : Save JSON with timestamped filename
CacheDir-->>Fetch : Confirmation
Fetch-->>Manager : Cache file path
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)

**Section sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)

## Message Filtering and Border Detection
The filtering process, managed by `telegram_filter.py`, applies date-based, pattern-based, and limit-based filters to cached messages. A critical feature is the border detection mechanism that validates whether the first message in a filtered set truly represents the boundary of the requested time period, preventing truncation errors.

```mermaid
flowchart TD
Start["filter_messages(channel, filter_type)"] --> FindCache["find_latest_cache()"]
FindCache --> Load["Load JSON cache file"]
Load --> DateFilter["Apply date filter based on filter_type"]
DateFilter --> HasFiltered{"Filtered messages exist?"}
HasFiltered --> |Yes| Border["validate_border_detection()"]
Border --> CheckCount["Available previous messages ≥ 3?"]
CheckCount --> |No| AutoFetch["Auto-fetch more messages<br/>Run telegram_fetch.py with higher limit"]
AutoFetch --> Reload["Reload new cache"]
Reload --> Border
CheckCount --> |Yes| Validate["Check 3-7 previous messages<br/>for same date"]
Validate --> Issues{"Any previous messages<br/>have same date?"}
Issues --> |Yes| Fail["Border detection FAILED"]
Issues --> |No| Pass["Border detection confirmed"]
Pass --> Pattern["Apply regex pattern filter (if specified)"]
Pattern --> Limit["Apply limit (if specified)"]
Limit --> Return["Return filtered messages"]
style AutoFetch fill:#ff9,stroke:#333
style Fail fill:#f99,stroke:#333
style Pass fill:#9f9,stroke:#333
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

**Section sources**
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

## Conditional Logic in the 'read' Command
The 'read' command in `telegram_manager.sh` implements conditional logic to determine whether to use cached data or fetch fresh messages. This decision is based on cache validity checks and optional clean cache flags provided by the user.

```mermaid
flowchart TD
Start["telegram_manager.sh read command"] --> Parse["Parse arguments:<br/>channel, filter, --clean flag"]
Parse --> CleanFlag{"--clean or clean_cache flag?"}
CleanFlag --> |Yes| Clean["Execute telegram_cache.py clean"]
Clean --> Fetch["Execute telegram_fetch.py"]
Fetch --> Filter["Execute telegram_filter.py"]
CleanFlag --> |No| CheckValid["Execute telegram_cache.py check"]
CheckValid --> IsValid{"Cache valid?"}
IsValid --> |Yes| UseCache["Display 'Using cached data...'"]
UseCache --> Filter
IsValid --> |No| FetchStale["Execute telegram_fetch.py"]
FetchStale --> Filter
Filter --> Display["Output filtered messages"]
style Clean fill:#ff9,stroke:#333
style UseCache fill:#9f9,stroke:#333
style FetchStale fill:#ff9,stroke:#333
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L1-L110)

## Message Processing Pipeline
The message processing pipeline handles timestamp conversion, metadata extraction, and content filtering to deliver a consistent output format. All timestamps are converted from UTC to Moscow time (UTC+3) for display, and media messages are annotated with appropriate icons.

```mermaid
flowchart LR
Raw["Raw Telegram Message"] --> Time["Convert UTC timestamp<br/>to Moscow time (UTC+3)"]
Time --> Sender["Extract sender name:<br/>first_name + last_name"]
Sender --> Media["Process media content:<br/>Photo → 📷, File → 📎, Other → 📦"]
Media --> Text["Combine text content with<br/>media indicators"]
Text --> Meta["Extract metadata:<br/>views, forwards, reply_to_id"]
Meta --> Struct["Create structured JSON:<br/>id, date_utc, date_msk,<br/>text, sender, views, etc."]
Struct --> Cache["Store in timestamped JSON file"]
style Raw fill:#f9f,stroke:#333
style Cache fill:#9f9,stroke:#333
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

**Section sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

## Cache Integrity and Edge Case Handling
The system implements several mechanisms to maintain message integrity across cache boundaries and handle edge cases such as empty channels or network failures. The fallback border detection automatically triggers additional message fetching when insufficient data is available for proper validation.

```mermaid
flowchart TD
EmptyChannel["Empty Channel Detection"] --> CheckMessages{"messages array empty?"}
CheckMessages --> |Yes| Error["Display 'No cache found' message<br/>Suggest running fetch command"]
NetworkFailure["Network/API Failure"] --> TryCatch{"Exception during API call?"}
TryCatch --> |Yes| ErrorOutput["Display 'Error: [message]' in stderr<br/>Exit with code 1"]
BorderIssue["Border Detection Issue"] --> Insufficient{"< 3 previous messages?"}
Insufficient --> |Yes| AutoRecovery["Auto-recovery protocol:<br/>1. Log warning<br/>2. Auto-fetch more messages<br/>3. Retry validation<br/>4. Proceed with caution if still insufficient"]
CorruptedCache["Corrupted Cache File"] --> JSONParse{"JSON load successful?"}
JSONParse --> |No| Skip["Skip file, log error<br/>Continue with next cache file"]
style Error fill:#f99,stroke:#333
style ErrorOutput fill:#f99,stroke:#333
style AutoRecovery fill:#ff9,stroke:#333
style Skip fill:#ff9,stroke:#333
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

**Section sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

## Performance Implications and Optimization
The system balances performance through intelligent caching strategies and optimized data retrieval. Different data pathways have distinct performance characteristics based on cache hit rates, network latency, and processing overhead.

```mermaid
flowchart LR
CacheHit["Cache Hit Path"] --> Check["Cache validity check: ~10ms"]
Check --> Filter["Message filtering: ~50-200ms<br/>depending on cache size"]
Filter --> Output["Total latency: ~60-210ms"]
CacheMiss["Cache Miss Path"] --> Check2["Cache validity check: ~10ms"]
Check2 --> Fetch["API fetch: ~1000-3000ms<br/>network dependent"]
Fetch --> CacheWrite["Cache write: ~50ms"]
CacheWrite --> Filter2["Message filtering: ~50-200ms"]
Filter2 --> Output2["Total latency: ~1100-3250ms"]
Optimization["Optimization Opportunities"] --> TTL["Adjust TTL values based on usage patterns"]
Optimization --> Batch["Increase fetch batch size for large requests"]
Optimization --> Index["Implement message indexing for faster filtering"]
Optimization --> Compress["Add cache compression for storage efficiency"]
Optimization --> Preemptive["Preemptive caching during off-peak hours"]
style CacheHit fill:#9f9,stroke:#333
style CacheMiss fill:#f99,stroke:#333
style Optimization fill:#ff9,stroke:#333
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L1-L178)
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L1-L146)
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L1-L238)