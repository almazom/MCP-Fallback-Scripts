# Direct Module Usage

<cite>
**Referenced Files in This Document**   
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py) - *Updated with CLI interface in recent commit*
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py) - *Updated with CLI interface in recent commit*
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py) - *Enhanced with boundary detection and validation capabilities*
- [telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py) - *Newly added for OCR caching functionality*
- [.env](file://.env)
</cite>

## Update Summary
**Changes Made**   
- Added new section for media_ocr_cache.py module usage
- Updated Core Module Interfaces diagram to include OCR caching module
- Enhanced Using telegram_filter.py section with boundary detection details
- Added OCR dependencies and initialization requirements
- Updated code examples to reflect new OCR functionality
- Added section sources for newly analyzed files
- Updated referenced files list to include new media_ocr_cache.py

## Table of Contents
1. [Introduction](#introduction)
2. [Core Module Interfaces](#core-module-interfaces)
3. [Module Initialization and Configuration](#module-initialization-and-configuration)
4. [Using telegram_fetch.py Programmatically](#using-telegram_fetchpy-programmatically)
5. [Using telegram_cache.py for Cache Management](#using-telegram_cachepy-for-cache-management)
6. [Using telegram_filter.py for Message Filtering](#using-telegram_filterpy-for-message-filtering)
7. [Using media_ocr_cache.py for OCR Processing](#using-media_ocr_cachepy-for-ocr-processing)
8. [Advanced Use Cases and Integration Patterns](#advanced-use-cases-and-integration-patterns)
9. [API Stability and Version Compatibility](#api-stability-and-version-compatibility)
10. [Troubleshooting and Best Practices](#troubleshooting-and-best-practices)

## Introduction
This document provides comprehensive guidance on leveraging the core Python modules of the Telegram tools suite directly within custom applications. The recent refactoring to a JSON-based architecture has enhanced the modularity and independence of these components. Each core module now features a documented CLI interface, enabling direct usage outside the `telegram_manager.sh` wrapper. This update details the programmatic and command-line interfaces of the primary modules: `telegram_fetch.py`, `telegram_cache.py`, `telegram_filter.py`, and the newly added `media_ocr_cache.py`, covering their usage, dependencies, configuration requirements, and implementation patterns for advanced use cases.

## Core Module Interfaces
The core modules expose both programmatic functions and CLI interfaces that serve as entry points for integration. Each module follows a clean separation of concerns, allowing independent or combined usage based on application needs. The recent refactoring has standardized the CLI interfaces across modules, making them more consistent and predictable.

```mermaid
graph TD
subgraph "telegram_fetch.py"
fetch_and_cache["fetch_and_cache(channel, limit=100, offset_id=0, suffix='', use_anchor=True)"]:::function
main["main() - CLI interface"]:::function
end
subgraph "telegram_cache.py"
is_cache_valid["is_cache_valid(channel, filter_type='today')"]:::function
clean_old_caches["clean_old_caches(channel=None, keep_latest=3)"]:::function
cache_info["cache_info()"]:::function
main["main() - CLI interface"]:::function
end
subgraph "telegram_filter.py"
filter_messages["filter_messages(channel, filter_type='today', pattern=None, limit=None)"]:::function
display_messages["display_messages(messages, group_by_date=True)"]:::function
main["main() - CLI interface"]:::function
end
subgraph "media_ocr_cache.py"
process_media["process_media(channel, messages, cache, refresh=False, lang='rus+eng', limit=None)"]:::function
main["main() - CLI interface"]:::function
OCRCache["OCRCache() - OCR cache manager"]:::class
end
subgraph "telegram_json_export.py"
filter_messages_json["filter_messages_json(channel, filter_type='today')"]:::function
export_range_summary["export_range_summary(messages)"]:::function
end
fetch_and_cache --> |creates| cache_file["Cache File"]
is_cache_valid --> |checks| cache_file
filter_messages --> |reads| cache_file
filter_messages_json --> |reads| cache_file
media_ocr_cache --> |reads| media_file["Media File"]
media_ocr_cache --> |writes| ocr_cache["media_ocr_cache.json"]
```

**Diagram sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L100-L140) - *Updated with enhanced CLI interface*
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L30-L100) - *Updated with standardized CLI commands*
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L100-L150) - *Updated with consistent CLI parameter structure*
- [telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L30-L80)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L150-L250) - *Newly added module for OCR caching*

## Module Initialization and Configuration
All modules rely on a unified `.env` file located in the project root for configuration. This file must contain the following credentials for Telegram API access:

:TELEGRAM_API_ID: Your Telegram API ID (integer)
:TELEGRAM_API_HASH: Your Telegram API hash (string)
:TELEGRAM_SESSION: String session data for the authenticated client

The modules automatically locate the `.env` file relative to their own path using `Path(__file__).parent.parent.parent.parent / ".env"`. When integrating these modules into external applications, ensure the `.env` file is accessible at the expected location or modify the path resolution logic accordingly. The `telethon` library is a required dependency and must be installed via `pip install telethon`. For OCR functionality, additional dependencies are required: `Pillow` for image processing and `pytesseract` for OCR processing, which can be installed via `pip install Pillow pytesseract`.

**Section sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L20-L40)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L10-L20)
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L10-L20)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L20-L40) - *Added OCR dependencies and configuration*

## Using telegram_fetch.py Programmatically
The `fetch_and_cache` function is the primary interface for retrieving messages from a Telegram channel and storing them in JSON format. It is an asynchronous function that must be awaited within an async context.

To use this module in a standalone script, import the function and run it within an asyncio event loop. The function accepts parameters for the channel identifier, message limit, offset ID for pagination, suffix for the cache filename, and a flag to enable/disable temporal anchoring. It returns the path to the created cache file upon successful execution. Error handling should account for network issues, authentication failures, and invalid channel names.

The module also provides a CLI interface through its `main()` function, accessible by running the script directly with command-line arguments:

```python
# Programmatic usage
import asyncio
from scripts.telegram_tools.core.telegram_fetch import fetch_and_cache

async def main():
    cache_path = await fetch_and_cache("@aiclubsweggs", limit=100, suffix="today")
    print(f"Cache created at: {cache_path}")

asyncio.run(main())
```

```bash
# CLI usage
python scripts/telegram_tools/core/telegram_fetch.py aiclubsweggs 100 0 today --no-anchor
```

**Section sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L100-L140) - *Updated with --no-anchor flag and enhanced CLI*

## Using telegram_cache.py for Cache Management
The `telegram_cache.py` module provides utilities for managing the lifecycle of cached message data. The `is_cache_valid` function checks whether the latest cache file for a given channel is still valid based on configurable TTL (Time-To-Live) rules, which vary by filter type (e.g., 5 minutes for "today", 60 minutes for "recent"). This function is essential for building applications that need to balance freshness with performance.

The `clean_old_caches` function allows for programmatic cleanup of outdated cache files, retaining only the most recent N files per channel. This is useful for automated maintenance tasks. The `cache_info` function provides detailed statistics about the current cache state, which can be integrated into monitoring dashboards.

The module includes a comprehensive CLI interface with commands for cache inspection and management:

```python
# Programmatic usage
from scripts.telegram_tools.core.telegram_cache import is_cache_valid, clean_old_caches

valid, cache_file = is_cache_valid("aiclubsweggs", "today")
if not valid:
    clean_old_caches("aiclubsweggs")
    # Trigger fresh fetch
```

```bash
# CLI usage
python scripts/telegram_tools/core/telegram_cache.py info
python scripts/telegram_tools/core/telegram_cache.py clean aiclubsweggs
python scripts/telegram_tools/core/telegram_cache.py check aiclubsweggs today
```

**Section sources**
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L30-L100) - *Updated with standardized CLI commands*

## Using telegram_filter.py for Message Filtering
The `filter_messages` function enables powerful filtering of cached messages based on date, text patterns, and result limits. It supports various filter types including "today", "yesterday", "last:N" days, specific dates, and "all" messages. Pattern filtering uses Python's `re` module for case-insensitive regex matching.

This function now includes enhanced boundary detection capabilities that validate the temporal boundaries between days, particularly important for channels with early morning messages that might be misclassified. The `validate_border_detection` function automatically checks messages around date boundaries and can trigger additional message fetching when necessary to ensure accurate results.

The function returns a list of message dictionaries, making it ideal for integration into data processing pipelines. The `display_messages` function is provided for human-readable output but is less relevant for programmatic use. For applications requiring raw JSON output, the `telegram_json_export.py` module's `filter_messages_json` function offers a similar interface without the display formatting.

The module features a robust CLI interface that mirrors its programmatic capabilities:

```python
# Programmatic usage
from scripts.telegram_tools.core.telegram_filter import filter_messages, display_messages

messages = filter_messages("aiclubsweggs", "last:3", pattern="gemini", limit=10)
display_messages(messages)
```

```bash
# CLI usage
python scripts/telegram_tools/core/telegram_filter.py aiclubsweggs last:3 'gemini' 10
```

**Section sources**
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L100-L150) - *Updated with enhanced boundary detection*
- [telegram_json_export.py](file://scripts/telegram_tools/core/telegram_json_export.py#L30-L80)

## Using media_ocr_cache.py for OCR Processing
The newly added `media_ocr_cache.py` module provides OCR (Optical Character Recognition) capabilities for Telegram media messages. This module enables caching of OCR results for images in messages, preventing redundant processing and improving performance for applications that need to extract text from images.

The primary interface is the `process_media` function, which processes media messages from a channel, performs OCR on images, and caches the results. The module uses Tesseract OCR engine via the `pytesseract` library and handles image processing through `Pillow`. Results are stored in a JSON cache file (`media_ocr_cache.json`) that includes the extracted text, image metadata, and content hashes to detect changes.

The `OCRCache` class manages the cache lifecycle, automatically updating entries when image content changes. The module supports multiple languages (defaulting to Russian and English) and can be configured to refresh existing OCR results.

```python
# Programmatic usage
from scripts.telegram_tools.core.media_ocr_cache import process_media, OCRCache
from scripts.telegram_tools.core.telegram_filter import filter_messages

# First, get media messages
messages = filter_messages("aiclubsweggs", "today")
media_messages = [m for m in messages if m.get("media_info")]

# Process with OCR
cache = OCRCache()
results = process_media("@aiclubsweggs", media_messages, cache, lang="rus+eng", limit=10)

# Display results
for result in results:
    if result["status"] == "updated" and result.get("ocr_text"):
        print(f"Message {result['message_id']}: {result['ocr_text'][:100]}...")
```

```bash
# CLI usage
python scripts/telegram_tools/core/media_ocr_cache.py aiclubsweggs today --lang rus+eng --display --limit 5
```

**Section sources**
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L150-L250) - *Newly added module for OCR caching functionality*
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L200-L238) - *Integration point for media message filtering*

## Advanced Use Cases and Integration Patterns
These modules can be combined to build sophisticated applications. For example, a custom dashboard can use `is_cache_valid` to determine if a refresh is needed, call `fetch_and_cache` to update data, and then use `filter_messages` to extract relevant information for display. Web services can embed these functions to provide real-time Telegram analytics.

The new OCR functionality enables advanced use cases such as automated content analysis of image-based messages, searchable archives of visual content, and compliance monitoring for image content. Specialized filtering logic can be implemented by processing the message list returned by `filter_messages`, adding custom metadata extraction or sentiment analysis. The modules' design supports embedding into larger applications by treating the cache directory as a shared data layer, enabling multiple components to access the same message data without redundant API calls.

The standardized CLI interfaces allow for easy integration into shell scripts, cron jobs, and containerized workflows, expanding the range of possible deployment patterns.

**Section sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L100-L140)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L30-L100)
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L100-L150)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L150-L250) - *New OCR integration patterns*

## API Stability and Version Compatibility
The public interfaces of these modules are considered stable for the current version. The recent refactoring has solidified both the programmatic and CLI interfaces, making them reliable for external integration. However, internal implementation details, such as the cache file naming convention and JSON structure, are subject to change. Applications should depend on the documented function signatures and not on the specific format of cache files.

When upgrading the tools suite, verify that the function parameters and return values remain consistent. The dependency on `telethon` should be pinned to a compatible version to avoid breaking changes. Long-term maintenance is facilitated by the modular design, which isolates changes to individual components.

**Section sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L100-L140)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L30-L100)
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L100-L150)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L150-L250) - *New module with stable interface*

## Troubleshooting and Best Practices
Ensure the `telegram_cache` directory exists and is writable. Handle exceptions from `telethon` operations, particularly during network failures. When using the modules in a web context, avoid blocking the main thread by running async functions in a separate executor. For high-frequency polling, leverage the TTL-based cache validation to minimize unnecessary API calls. Always validate the return values of functions, as they may indicate failure conditions (e.g., no cache found).

When using the CLI interfaces in automated scripts, check the exit codes to handle errors appropriately. The standardized command structure across modules simplifies error handling and logging in complex workflows. For OCR processing, ensure that Tesseract is properly installed and configured with the required language packs. Monitor the `media_ocr_cache.json` file size as it may grow significantly with extensive media processing.

**Section sources**
- [telegram_fetch.py](file://scripts/telegram_tools/core/telegram_fetch.py#L140-L146)
- [telegram_cache.py](file://scripts/telegram_tools/core/telegram_cache.py#L100-L178)
- [telegram_filter.py](file://scripts/telegram_tools/core/telegram_filter.py#L200-L238)
- [media_ocr_cache.py](file://scripts/telegram_tools/core/media_ocr_cache.py#L250-L277) - *Error handling and diagnostics*