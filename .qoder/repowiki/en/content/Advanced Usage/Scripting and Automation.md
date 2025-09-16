# Scripting and Automation

<cite>
**Referenced Files in This Document**   
- [telegram_manager.sh](file://telegram_manager.sh) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py)
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py)
- [scripts/telegram_tools/core/border_message_validator.py](file://scripts/telegram_tools/core/border_message_validator.py) - *Added in recent commit*
- [scripts/telegram_tools/core/media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py) - *Added in recent commit*
- [scripts/telegram_tools/core/content_verifier.py](file://scripts/telegram_tools/core/content_verifier.py) - *Added in recent commit*
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh)
- [tests/boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh)
- [tests/test_10_error_handling.sh](file://tests/test_10_error_handling.sh)
</cite>

## Update Summary
**Changes Made**   
- Added new section on Advanced Verification and Boundary Detection to reflect new commands
- Updated Core Commands Overview to include new subcommands: verify-boundaries, test-boundaries, verify-content, ocr-cache
- Enhanced Message Monitoring Workflows with boundary detection examples
- Added new diagram for boundary detection workflow
- Updated referenced files list to include newly added Python modules
- Revised Common Pitfalls and Solutions to address boundary detection challenges

## Table of Contents
1. [Introduction](#introduction)
2. [Core Commands Overview](#core-commands-overview)
3. [Message Monitoring Workflows](#message-monitoring-workflows)
4. [Automated Alerting Systems](#automated-alerting-systems)
5. [JSON Processing and Downstream Integration](#json-processing-and-downstream-integration)
6. [Cron Integration for Periodic Execution](#cron-integration-for-periodic-execution)
7. [Error Handling in Unattended Scripts](#error-handling-in-unattended-scripts)
8. [Best Practices for Production Scripts](#best-practices-for-production-scripts)
9. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)
10. [Comprehensive Pipeline Design](#comprehensive-pipeline-design)
11. [Advanced Verification and Boundary Detection](#advanced-verification-and-boundary-detection)

## Introduction
The FALLBACK_SCRIPTS toolkit provides a robust framework for scripting and automation of Telegram message monitoring and alerting workflows. This document details how to create shell scripts that chain multiple commands (fetch, filter, json, send) to build automated systems for daily digest generation, anomaly detection, and scheduled message relaying. The toolkit's modular design enables flexible pipeline construction with proper error handling, caching strategies, and integration capabilities.

## Core Commands Overview
The telegram_manager.sh script serves as the primary interface for interacting with Telegram channels through various subcommands that can be chained together in automation workflows. Recent refactoring has introduced a JSON-based architecture that allows direct invocation of modular Python scripts. The latest update adds advanced verification commands for boundary detection and content validation.

```mermaid
flowchart TD
A["Command: fetch <channel> [limit]"] --> B["Action: Retrieves messages from Telegram"]
C["Command: read <channel> [filter]"] --> D["Action: Reads cached messages with optional filtering"]
E["Command: send <target> <message>"] --> F["Action: Sends message to specified target"]
G["Command: json <channel> [filter]"] --> H["Action: Exports raw JSON data"]
I["Command: cache"] --> J["Action: Shows cache information"]
K["Command: clean [channel]"] --> L["Action: Cleans old cache files"]
M["Command: verify-boundaries <channel> <date>"] --> N["Action: Validates first message with 10/10 confidence"]
O["Command: test-boundaries <channel>"] --> P["Action: Comprehensive multi-day boundary testing"]
Q["Command: verify-content <cache_file>"] --> R["Action: Validates cache against live data"]
S["Command: ocr-cache <channel>"] --> T["Action: Generates OCR cache for media"]
B --> U["Output: Cached JSON files in telegram_cache/"]
D --> V["Output: Filtered message display"]
F --> W["Output: Message delivery confirmation"]
H --> X["Output: JSON data for processing"]
N --> Y["Output: Boundary verification report"]
P --> Z["Output: Multi-day confidence scoring"]
R --> AA["Output: Cache consistency report"]
T --> AB["Output: OCR text cache"]
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L0-L146) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L0-L238) - *Updated in recent commit*
- [scripts/telegram_tools/core/border_message_validator.py](file://scripts/telegram_tools/core/border_message_validator.py#L0-L491) - *Added in recent commit*

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*

## Message Monitoring Workflows
The toolkit enables creation of sophisticated message monitoring workflows by chaining commands together. These workflows can be designed for various use cases including daily digest generation and anomaly detection. The recent JSON-based architecture refactor allows direct invocation of Python modules, enhancing script flexibility and performance.

### Daily Digest Generation
Daily digest scripts can be created by combining the fetch, filter, and send commands to automatically compile and deliver summaries of channel activity.

```mermaid
sequenceDiagram
participant Cron as "Cron Scheduler"
participant Script as "Daily Digest Script"
participant Fetch as "telegram_fetch.py"
participant Filter as "telegram_filter.py"
participant Send as "Message Sender"
Cron->>Script : Execute daily at 9 : 00 AM
Script->>Fetch : fetch @target_channel 500
Fetch-->>Script : Cache messages
Script->>Filter : read @target_channel today
Filter-->>Script : Filter today's messages
Script->>Send : send @recipient "Daily digest : [summary]"
Send-->>Script : Confirmation
Script-->>Cron : Completion
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L0-L146) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L0-L238) - *Updated in recent commit*

### Anomaly Detection via Pattern Filtering
Anomaly detection workflows use pattern matching to identify specific message content that requires attention or further action.

```mermaid
flowchart TD
Start([Start]) --> FetchMessages["fetch @channel 200"]
FetchMessages --> FilterPattern["filter messages with regex pattern"]
FilterPattern --> MessagesFound{"Messages found?"}
MessagesFound --> |Yes| FormatAlert["Format alert message"]
MessagesFound --> |No| End([No anomalies detected])
FormatAlert --> SendAlert["send @admin_team Alert: Pattern detected"]
SendAlert --> LogEvent["Log detection event"]
LogEvent --> End
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L0-L238) - *Updated in recent commit*

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L0-L238) - *Updated in recent commit*

## Automated Alerting Systems
The toolkit supports creation of automated alerting systems that can detect specific conditions and send notifications through various channels.

### Scheduled Message Relaying
Scheduled message relaying workflows automatically forward messages from one channel to another based on timing or content criteria.

```mermaid
sequenceDiagram
participant Cron as "Cron Job"
participant RelayScript as "Relay Script"
participant Source as "Source Channel"
participant Target as "Target Channel"
Cron->>RelayScript : Execute hourly
RelayScript->>Source : fetch @source_channel 100
Source-->>RelayScript : Return messages
RelayScript->>RelayScript : Filter for relay criteria
RelayScript->>Target : send @target_channel filtered_messages
Target-->>RelayScript : Delivery confirmation
RelayScript-->>Cron : Job completed
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*

## JSON Processing and Downstream Integration
The json command enables integration with downstream processing systems by providing raw JSON output that can be parsed and analyzed.

### Parsing JSON Output
The telegram_json_export.py script provides structured JSON output that can be processed by other tools or systems.

```mermaid
flowchart TD
A["telegram_json_export.py"] --> B["Output Modes"]
B --> C["--summary: First/last message summary"]
B --> D["--full: Complete JSON export"]
C --> E["Extract time range and message counts"]
D --> F["Process all messages for analysis"]
E --> G["Generate reports"]
F --> H["Perform comprehensive analysis"]
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L0-L124)

### Downstream Processing Pipeline
JSON output can be integrated into larger data processing pipelines for advanced analytics and reporting.

```mermaid
sequenceDiagram
participant Fetch as "telegram_fetch.py"
participant Export as "telegram_json_export.py"
participant Process as "JSON Processor"
participant Store as "Data Store"
participant Analyze as "Analytics Engine"
Fetch->>Export : Generate cache
Export->>Process : Export JSON (--full)
Process->>Process : Parse and transform data
Process->>Store : Save to database
Store->>Analyze : Provide data for analysis
Analyze->>Analyze : Generate insights
Analyze->>Analyze : Create visualizations
```

**Diagram sources**
- [scripts/telegram_tools/core/telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L0-L146) - *Updated in recent commit*
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L0-L124)

**Section sources**
- [scripts/telegram_tools/core/telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L0-L124)

## Cron Integration for Periodic Execution
Cron integration enables periodic execution of monitoring and alerting scripts without manual intervention.

### Cron Job Configuration
Cron jobs can be configured to execute scripts at specified intervals for continuous monitoring.

```mermaid
flowchart TD
A["Crontab Entry"] --> B["Schedule Definition"]
B --> C["Minute: 0"]
B --> D["Hour: 9"]
B --> E["Day of Month: *"]
B --> F["Month: *"]
B --> G["Day of Week: 1-5"]
C --> H["Execute daily at 9:00 AM"]
D --> H
E --> H
F --> H
G --> H
H --> I["Run: /path/to/script.sh"]
```

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*

## Error Handling in Unattended Scripts
Proper error handling is critical for unattended scripts to ensure reliability and provide meaningful diagnostics when issues occur.

### Error Handling Strategies
The toolkit includes comprehensive error handling mechanisms to manage various failure scenarios.

```mermaid
flowchart TD
A["Script Execution"] --> B{"Success?"}
B --> |Yes| C["Continue workflow"]
B --> |No| D["Capture error details"]
D --> E["Log error with timestamp"]
E --> F{"Critical error?"}
F --> |Yes| G["Send alert to administrator"]
F --> |No| H["Continue with next task"]
G --> I["Exit with error code"]
H --> I
I --> J["End execution"]
```

**Diagram sources**
- [tests/test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L0-L244)

**Section sources**
- [tests/test_10_error_handling.sh](file://tests/test_10_error_handling.sh#L0-L244)

## Best Practices for Production Scripts
Implementing best practices ensures reliable and maintainable automation scripts in production environments.

### Logging and Monitoring
Comprehensive logging provides visibility into script execution and aids in troubleshooting.

```mermaid
flowchart TD
A["Script Start"] --> B["Log execution start"]
B --> C["Log each major step"]
C --> D["Log data processing results"]
D --> E["Log completion status"]
E --> F["Include timestamps in all logs"]
F --> G["Rotate logs to prevent disk exhaustion"]
```

### Failure Recovery
Robust failure recovery mechanisms ensure scripts can handle transient issues gracefully.

```mermaid
flowchart TD
A["Operation"] --> B{"Success?"}
B --> |Yes| C["Continue"]
B --> |No| D["Wait with exponential backoff"]
D --> E{"Retry limit reached?"}
E --> |No| F["Retry operation"]
F --> B
E --> |Yes| G["Escalate error"]
G --> H["Send alert"]
```

### Rate Limit Avoidance
Strategies to avoid rate limits when interacting with external APIs.

```mermaid
flowchart TD
A["API Request"] --> B{"Within rate limits?"}
B --> |Yes| C["Execute request"]
B --> |No| D["Wait until window resets"]
C --> E{"Request successful?"}
E --> |Yes| F["Update rate limit counter"]
E --> |No| G["Handle error appropriately"]
F --> H["Continue workflow"]
```

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L0-L178)
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*

## Common Pitfalls and Solutions
Understanding common pitfalls helps avoid issues when developing automation scripts with the toolkit.

### Environment Variable Scoping
Environment variables must be properly scoped and accessible to all script components.

```mermaid
flowchart TD
A["Main Script"] --> B["Subprocess"]
B --> C{"Environment inherited?"}
C --> |No| D["Explicitly pass required variables"]
C --> |Yes| E["Verify variable availability"]
D --> F["Use export or direct assignment"]
F --> G["Test in target execution context"]
```

### Cache Contention in Concurrent Scripts
Multiple concurrent scripts accessing the cache require proper coordination to avoid conflicts.

```mermaid
flowchart TD
A["Script 1"] --> B["Access cache"]
C["Script 2"] --> D["Access cache"]
B --> E{"Cache locked?"}
D --> E
E --> |Yes| F["Wait for release"]
E --> |No| G["Acquire lock"]
G --> H["Perform cache operation"]
H --> I["Release lock"]
```

**Section sources**
- [scripts/telegram_tools/core/telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L0-L178)

## Comprehensive Pipeline Design
The comprehensive_message_analysis.sh script demonstrates robust pipeline design principles for complex message analysis workflows.

### Robust Pipeline Components
A well-designed pipeline incorporates multiple components working together to achieve reliable results.

```mermaid
flowchart TD
A["Input Validation"] --> B["Error Handling"]
B --> C["Cache Management"]
C --> D["Data Processing"]
D --> E["Result Formatting"]
E --> F["Output Delivery"]
F --> G["Logging and Monitoring"]
G --> H["Failure Recovery"]
H --> A
```

**Section sources**
- [tests/comprehensive_message_analysis.sh](file://tests/comprehensive_message_analysis.sh#L0-L114)
- [tests/boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh#L0-L156)

## Advanced Verification and Boundary Detection
The toolkit now includes advanced verification commands for boundary detection and content validation, providing 10/10 confidence in message timing and content accuracy.

### Boundary Detection Workflow
The verify-boundaries command uses triple verification to detect the first message of a date with high confidence.

```mermaid
flowchart TD
A["Start: verify-boundaries @channel 2025-09-14"] --> B["Phase 1: Broad search for date boundaries"]
B --> C["Phase 2: Identify candidate messages"]
C --> D["Phase 3: Triple verification (Direct, History, Iterative)"]
D --> E{"Verification successful?"}
E --> |Yes| F["Generate confidence score and report"]
E --> |No| G["Retry with alternative methods"]
F --> H["Save detailed JSON report to telegram_verification/"]
G --> H
H --> I["Output first message with 100% confidence"]
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/border_message_validator.py](file://scripts/telegram_tools/core/border_message_validator.py#L0-L491) - *Added in recent commit*

### OCR Cache for Media Content
The ocr-cache command generates and maintains OCR descriptions for media content, enabling text-based search and analysis.

```mermaid
flowchart TD
A["ocr-cache @channel today"] --> B["Load cached messages with media"]
B --> C["Process each media file"]
C --> D{"File is image?"}
D --> |Yes| E["Compute content hash"]
D --> |No| F["Skip non-image file"]
E --> G{"Cache entry exists and valid?"}
G --> |Yes| H["Use cached OCR text"]
G --> |No| I["Perform OCR with specified language"]
I --> J["Store OCR result in media_ocr_cache.json"]
J --> K["Return processed results"]
H --> K
K --> L["Display results with --display flag"]
```

**Diagram sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L0-L277) - *Added in recent commit*

**Section sources**
- [telegram_manager.sh](file://telegram_manager.sh#L0-L309) - *Updated in recent commit*
- [scripts/telegram_tools/core/border_message_validator.py](file://scripts/telegram_tools/core/border_message_validator.py#L0-L491) - *Added in recent commit*
- [scripts/telegram_tools/core/media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L0-L277) - *Added in recent commit*
- [scripts/telegram_tools/core/content_verifier.py](file://scripts/telegram_tools/core/content_verifier.py#L0-L189) - *Added in recent commit*
- [tests/boundary_aware_first_message_detector.sh](file://tests/boundary_aware_first_message_detector.sh#L0-L156) - *Updated in recent commit*