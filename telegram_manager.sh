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
    *)
        cat << 'EOF'
telegram_manager.sh - Simple Telegram Manager

COMMANDS:
  fetch <channel> [limit]       Fetch messages from Telegram
  read <channel> [filter] [--clean|clean_cache]  Read cached messages (--clean or clean_cache to clear cache first)
  send <target> <message>       Send message
  json <channel> [filter]       Export raw JSON (--summary or --full)
  cache                         Show cache info
  clean [channel]               Clean old cache

  archive <channel> [date]      Archive daily cache for permanent storage
  restore <channel> <date>      Restore daily cache from storage
  validate <channel> [cache]    Validate message completeness
  anchor <action> [args...]     Manage temporal anchors

FILTERS: today, yesterday, last:N, all

Examples:
  ./telegram_manager.sh fetch aiclubsweggs 100
  ./telegram_manager.sh read aiclubsweggs today
  ./telegram_manager.sh read aiclubsweggs today --clean
  ./telegram_manager.sh read aiclubsweggs clean_cache
  ./telegram_manager.sh read aiclubsweggs --clean
  ./telegram_manager.sh json aiclubsweggs today --summary
  ./telegram_manager.sh send @almazom "Hello"

  ./telegram_manager.sh archive @aiclubsweggs
  ./telegram_manager.sh restore @aiclubsweggs 2025-09-15
  ./telegram_manager.sh validate @aiclubsweggs
  ./telegram_manager.sh anchor list @aiclubsweggs
  ./telegram_manager.sh anchor set @aiclubsweggs 72856 00:58:11
EOF
        ;;
esac
