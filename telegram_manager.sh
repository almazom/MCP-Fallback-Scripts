#!/bin/bash
# telegram_manager.sh - Simple Telegram manager for single user
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TELEGRAM_DIR="$SCRIPT_DIR/scripts/telegram_tools/core"

case "${1:-help}" in
    fetch)
        [[ -z "${2:-}" ]] && echo "Usage: $0 fetch <channel> [limit]" && exit 1
        cd "$TELEGRAM_DIR" && python3 telegram_fetch.py "$2" "${3:-200}"
        ;;
    read)
        [[ -z "${2:-}" ]] && echo "Usage: $0 read <channel> [filter] [--clean|clean_cache]" && exit 1

        # Check for --clean flag
        clean_cache=false
        filter_arg="${3:-today}"

        if [[ "${3:-}" == "--clean" ]] || [[ "${4:-}" == "--clean" ]] || [[ "${3:-}" == "clean_cache" ]] || [[ "${4:-}" == "clean_cache" ]]; then
            clean_cache=true
            # If --clean or clean_cache is in position 3, use default filter
            [[ "${3:-}" == "--clean" ]] || [[ "${3:-}" == "clean_cache" ]] && filter_arg="today"
        fi

        # Clean cache if requested
        if [[ "$clean_cache" == "true" ]]; then
            echo "🧹 Cleaning cache..."
            python3 "$TELEGRAM_DIR/telegram_cache.py" clean "$2"
            echo "📡 Fetching fresh messages..."
            cd "$TELEGRAM_DIR" && python3 telegram_fetch.py "$2" 200
        else
            # Simple boundary check: is cache fresh?
            if python3 "$TELEGRAM_DIR/telegram_cache.py" check "$2" "$filter_arg" >/dev/null 2>&1; then
                echo "📋 Using cached data..."
            else
                echo "🔄 Cache stale, fetching fresh data..."
                cd "$TELEGRAM_DIR" && python3 telegram_fetch.py "$2" 200
            fi
        fi

        python3 "$TELEGRAM_DIR/telegram_filter.py" "$2" "$filter_arg"
        ;;
    send)
        [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] && echo "Usage: $0 send <target> <message>" && exit 1
        python3 -c "
import asyncio
import sys
import os
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

async def send_message():
    # Use the script directory to find .env
    script_dir = Path('$SCRIPT_DIR')
    env_file = script_dir / '.env'

    creds = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                creds[key] = value.strip('\"')

    client = TelegramClient(StringSession(creds['TELEGRAM_SESSION']),
                          int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    await client.connect()
    await client.send_message('$2', '$3')
    await client.disconnect()
    print('✅ Message sent')

asyncio.run(send_message())
" "$2" "$3"
        ;;
    send_file)
        [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] && echo "Usage: $0 send_file <target> <file_path> [caption]" && exit 1
        python3 -c "
import asyncio
import sys
import os
from pathlib import Path
from telethon import TelegramClient
from telethon.sessions import StringSession

async def send_file_to_telegram():
    # Use the script directory to find .env
    script_dir = Path('$SCRIPT_DIR')
    env_file = script_dir / '.env'

    creds = {}
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                creds[key] = value.strip('\"')

    client = TelegramClient(StringSession(creds['TELEGRAM_SESSION']),
                          int(creds['TELEGRAM_API_ID']), creds['TELEGRAM_API_HASH'])
    await client.connect()

    # Get file path and optional caption
    file_path = '$3'
    caption = '${4:-📎 File attached}'

    # Check if file exists
    if not Path(file_path).exists():
        print(f'❌ File not found: {file_path}')
        await client.disconnect()
        return

    await client.send_file('$2', file_path, caption=caption)
    await client.disconnect()
    print(f'✅ File sent successfully: {Path(file_path).name}')

asyncio.run(send_file_to_telegram())
" "$2" "$3" "${4:-}"
        ;;
    cache)
        cd "$TELEGRAM_DIR" && python3 telegram_cache.py info
        ;;
    clean)
        cd "$TELEGRAM_DIR" && python3 telegram_cache.py clean "${2:-}"
        ;;
    json)
        [[ -z "${2:-}" ]] && echo "Usage: $0 json <channel> [filter] [--summary|--full]" && exit 1
        cd "$TELEGRAM_DIR" && python3 telegram_json_export.py "$2" "${3:-today}" "${4:---summary}"
        ;;
    archive)
        [[ -z "${2:-}" ]] && echo "Usage: $0 archive <channel> [date]" && exit 1
        cd "$TELEGRAM_DIR" && python3 daily_persistence.py archive "$2" "${3:-}"
        ;;
    restore)
        [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] && echo "Usage: $0 restore <channel> <date>" && exit 1
        cd "$TELEGRAM_DIR" && python3 daily_persistence.py restore "$2" "$3"
        ;;
    validate)
        [[ -z "${2:-}" ]] && echo "Usage: $0 validate <channel> [cache_file]" && exit 1
        cd "$TELEGRAM_DIR"
        if [[ -n "${3:-}" ]]; then
            python3 gap_validator.py validate "$2" "$3"
        else
            python3 gap_validator.py validate "$2"
        fi
        ;;
    anchor)
        action="${2:-list}"
        case "$action" in
            set)
                [[ -z "${3:-}" ]] || [[ -z "${4:-}" ]] || [[ -z "${5:-}" ]] && echo "Usage: $0 anchor set <channel> <message_id> <timestamp> [date]" && exit 1
                cd "$TELEGRAM_DIR" && python3 temporal_anchor.py set "$3" "$4" "$5" "${6:-}"
                ;;
            get)
                [[ -z "${3:-}" ]] && echo "Usage: $0 anchor get <channel> [date]" && exit 1
                cd "$TELEGRAM_DIR"
                if [[ -n "${4:-}" ]]; then
                    python3 temporal_anchor.py get "$3" "$4"
                else
                    python3 temporal_anchor.py get "$3"
                fi
                ;;
            list)
                cd "$TELEGRAM_DIR" && python3 temporal_anchor.py list "${3:-}"
                ;;
            *)
                echo "Usage: $0 anchor <set|get|list> [args...]"
                echo "  set <channel> <message_id> <timestamp> [date]"
                echo "  get <channel> [date]"
                echo "  list [channel]"
                ;;
        esac
        ;;
    verify-boundaries)
        [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] && echo "Usage: $0 verify-boundaries <channel> <date>" && exit 1
        cd "$TELEGRAM_DIR" && python3 border_message_validator.py "$2" "$3"
        ;;
    test-boundaries)
        [[ -z "${2:-}" ]] && echo "Usage: $0 test-boundaries <channel> [start_date] [days]" && exit 1
        cd "$SCRIPT_DIR/scripts/telegram_tools" && python3 test_boundaries.py "$2" "${3:-}" "${4:-7}"
        ;;
    verify-content)
        [[ -z "${2:-}" ]] && echo "Usage: $0 verify-content <cache_file> [--auto-correct]" && exit 1
        cd "$TELEGRAM_DIR"
        if [[ "${3:-}" == "--auto-correct" ]]; then
            python3 content_verifier.py "$2" --auto-correct
        else
            python3 content_verifier.py "$2"
        fi
        ;;
    fetch-media)
        [[ -z "${2:-}" ]] && echo "Usage: $0 fetch-media <channel> [limit]" && exit 1
        cd "$TELEGRAM_DIR" && python3 telegram_fetch.py "$2" "${3:-100}" 0 "media" --fetch-media
        ;;
    ocr-cache)
        [[ -z "${2:-}" ]] && echo "Usage: $0 ocr-cache <channel> [filter] [--refresh] [--lang=LANG] [--limit N] [--display]" && exit 1
        cd "$TELEGRAM_DIR" && python3 media_ocr_cache.py "$2" "${@:3}"
        ;;
    verify-boundaries-cache)
        [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]] || [[ -z "${4:-}" ]] && echo "Usage: $0 verify-boundaries-cache <channel> <date> <cache_file>" && exit 1
        cd "$TELEGRAM_DIR" && python3 border_message_validator.py "$2" "$3" --verify-cache "$4"
        ;;
    analyze-with-gemini)
        [[ -z "${2:-}" ]] && echo "Usage: $0 analyze-with-gemini <channel> [filter] [message_id]" && exit 1
        channel="$2"
        filter="${3:-today}"
        message_id="${4:-}"

        if [[ -n "$message_id" ]]; then
            # Analyze specific message by ID
            message_content=$(cd "$TELEGRAM_DIR" && python3 telegram_json_export.py "$channel" all --full | jq -r ".messages[] | select(.id == $message_id) | .text")
            if [[ "$message_content" == "null" || -z "$message_content" ]]; then
                echo "❌ Message ID $message_id not found"
                exit 1
            fi
            echo "🤖 Analyzing message ID $message_id with Gemini..."
            gemini -p "Analyze this Telegram message and provide a detailed description of its content, context, and meaning: '$message_content'"
        else
            # Analyze all messages in filter
            echo "🤖 Analyzing $channel messages ($filter) with Gemini..."
            messages_json=$(cd "$TELEGRAM_DIR" && python3 telegram_json_export.py "$channel" "$filter" --full)
            gemini -p "Analyze these Telegram messages and provide a detailed summary and insights: $messages_json"
        fi
        ;;
    analyze-with-claude)
        [[ -z "${2:-}" ]] && echo "Usage: $0 analyze-with-claude <channel> [filter] [message_id]" && exit 1
        channel="$2"
        filter="${3:-today}"
        message_id="${4:-}"

        if [[ -n "$message_id" ]]; then
            # Analyze specific message by ID
            message_content=$(cd "$TELEGRAM_DIR" && python3 telegram_json_export.py "$channel" all --full | jq -r ".messages[] | select(.id == $message_id) | .text")
            if [[ "$message_content" == "null" || -z "$message_content" ]]; then
                echo "❌ Message ID $message_id not found"
                exit 1
            fi
            echo "🧠 Analyzing message ID $message_id with Claude..."
            claude --print "Analyze this Telegram message and provide a detailed description of its content, context, and meaning: '$message_content'"
        else
            # Analyze all messages in filter
            echo "🧠 Analyzing $channel messages ($filter) with Claude..."
            messages_json=$(cd "$TELEGRAM_DIR" && python3 telegram_json_export.py "$channel" "$filter" --full)
            claude --print "Analyze these Telegram messages and provide a detailed summary and insights: $messages_json"
        fi
        ;;
    *)
        cat << 'EOF'
telegram_manager.sh - Advanced Telegram Manager with 10/10 Confidence Border Detection

BASIC COMMANDS:
  fetch <channel> [limit]                    Fetch messages from Telegram
  read <channel> [filter] [--clean]         Read cached messages (--clean to clear cache first)
  send <target> <message>                   Send message
  send_file <target> <file_path> [caption]  Send file attachment
  json <channel> [filter] [--summary|--full] Export raw JSON
  cache                                     Show cache info
  clean [channel]                           Clean old cache

ADVANCED VERIFICATION (NEW - 10/10 CONFIDENCE):
  verify-boundaries <channel> <date>        🎯 Ultimate boundary detection with triple verification
  test-boundaries <channel> [start_date] [days] 🧪 Comprehensive multi-day boundary testing
  verify-content <cache_file> [--auto-correct]  🔍 Verify cache against live data with auto-fix
  fetch-media <channel> [limit]             📎 Fetch messages with automatic media download
  ocr-cache <channel> [filter] [options]   📝 Generate & reuse OCR descriptions for media
  verify-boundaries-cache <channel> <date> <cache> Compare cached vs live boundaries

AI ANALYSIS:
  analyze-with-gemini <channel> [filter] [message_id] 🤖 Detailed message analysis using Gemini
  analyze-with-claude <channel> [filter] [message_id] 🧠 Detailed message analysis using Claude

PERSISTENCE & ANCHORING:
  archive <channel> [date]                  Archive daily cache for permanent storage
  restore <channel> <date>                  Restore daily cache from storage
  validate <channel> [cache]                Validate message completeness
  anchor <action> [args...]                 Manage temporal anchors

FILTERS: today, yesterday, last:N, all, YYYY-MM-DD

BASIC EXAMPLES:
  ./telegram_manager.sh fetch aiclubsweggs 100
  ./telegram_manager.sh read aiclubsweggs today
  ./telegram_manager.sh read aiclubsweggs today --clean
  ./telegram_manager.sh json aiclubsweggs yesterday --summary
  ./telegram_manager.sh send @almazom "Hello"
  ./telegram_manager.sh send_file @almazom /path/to/file.pdf "📎 Document attached"

VERIFICATION EXAMPLES (10/10 CONFIDENCE SYSTEM):
  # Ultimate boundary detection with triple verification + media download
  ./telegram_manager.sh verify-boundaries @aiclubsweggs 2025-09-14

  # Comprehensive testing across multiple days with confidence scoring
  ./telegram_manager.sh test-boundaries @aiclubsweggs 2025-09-14 7

  # Verify cache accuracy against live Telegram data
  ./telegram_manager.sh verify-content telegram_cache/aiclubsweggs_20250915_224022.json

  # Auto-correct cache inconsistencies
  ./telegram_manager.sh verify-content cache.json --auto-correct

  # Fetch messages with automatic media download and hash verification
  ./telegram_manager.sh fetch-media @aiclubsweggs 50

  # Compare cached boundary vs live detection
  ./telegram_manager.sh verify-boundaries-cache @aiclubsweggs 2025-09-14 cache.json

AI ANALYSIS EXAMPLES:
  # Analyze specific message with detailed AI description
  ./telegram_manager.sh analyze-with-gemini @aiclubsweggs today 72856
  ./telegram_manager.sh analyze-with-claude @aiclubsweggs today 72856

  # Analyze all messages from a time period
  ./telegram_manager.sh analyze-with-gemini @aiclubsweggs yesterday
  ./telegram_manager.sh analyze-with-claude @aiclubsweggs 2025-09-14

PERSISTENCE EXAMPLES:
  ./telegram_manager.sh archive @aiclubsweggs 2025-09-14
  ./telegram_manager.sh restore @aiclubsweggs 2025-09-14
  ./telegram_manager.sh validate @aiclubsweggs

ANCHOR MANAGEMENT:
  ./telegram_manager.sh anchor list @aiclubsweggs
  ./telegram_manager.sh anchor set @aiclubsweggs 72856 00:58:11 2025-09-15
  ./telegram_manager.sh anchor get @aiclubsweggs 2025-09-15

🎯 NEW FEATURES:
  ✅ Triple verification using 3 different Telegram API methods
  ✅ Automatic media download with content hash verification
  ✅ 100% confidence scoring with detailed reporting
  ✅ Cross-validation against live Telegram data
  ✅ Auto-correction of cache inconsistencies
  ✅ Comprehensive multi-day boundary testing
  ✅ Moscow timezone aware date handling
  ✅ Phase-based boundary detection (Broad→Verify→Triple-check)

🏆 CONFIDENCE LEVELS:
  100%  = Perfect verification (10/10)
  ≥95%  = Excellent (9/10)
  ≥90%  = Good (8/10)
  ≥80%  = Fair (7/10)
  <80%  = Needs investigation

📊 VERIFICATION REPORTS:
  All verification operations generate detailed JSON reports in:
  ./telegram_verification/

  Reports include:
  - Confidence scores and verification methods used
  - Media download status and content hashes
  - Boundary detection phases and candidate analysis
  - Cross-validation results against live data
  - Performance metrics and timing information
EOF
        ;;
esac
