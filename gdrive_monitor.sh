#!/bin/bash

# Enhanced Google Drive Access Monitor
export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/gdrive_monitor.log"

log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_telegram_update() {
    local message="$1"
    "$SCRIPT_DIR/telegram_manager.sh" send almazom "$message" 2>/dev/null
}

test_folder_access() {
    local folder_name="$1"
    rclone lsd "mydrive:$folder_name" >/dev/null 2>&1
    return $?
}

test_general_access() {
    rclone lsd mydrive: >/dev/null 2>&1
    return $?
}

main_monitor() {
    log_with_timestamp "🔄 Starting enhanced Google Drive monitoring"
    log_with_timestamp "Folders to monitor: API_Test, Plaude"
    
    local check_count=0
    local max_checks=72  # 72 * 5 minutes = 6 hours max
    
    while [ $check_count -lt $max_checks ]; do
        check_count=$((check_count + 1))
        log_with_timestamp "📊 Monitor check $check_count/$max_checks"
        
        # Test general access first
        if test_general_access; then
            log_with_timestamp "✅ Service account can access Google Drive!"
            
            # List what's visible
            folders=$(rclone lsd mydrive: 2>/dev/null | head -10)
            if [ ! -z "$folders" ]; then
                log_with_timestamp "📁 Visible folders found:"
                echo "$folders" | tee -a "$LOG_FILE"
                
                # Test specific folders
                for folder in "API_Test" "Plaude"; do
                    if test_folder_access "$folder"; then
                        log_with_timestamp "✅ SUCCESS: $folder folder is accessible!"
                        send_telegram_update "🎉 SUCCESS! $folder folder is now accessible! You can run: ./gdrive_manager.sh list \"$folder\""
                    else
                        log_with_timestamp "⏳ $folder folder not yet accessible"
                    fi
                done
                
                send_telegram_update "📁 Google Drive access working! Found $(echo "$folders" | wc -l) folders. Check $LOG_FILE for details."
                break
            fi
        else
            log_with_timestamp "⌛ Google Drive access not ready yet (attempt $check_count)"
        fi
        
        # Send periodic updates
        if [ $((check_count % 6)) -eq 0 ]; then
            local elapsed=$((check_count * 5))
            send_telegram_update "⏰ Update: Still monitoring Google Drive access after ${elapsed} minutes (attempt $check_count/$max_checks)"
        fi
        
        # Progressive backoff: start with 5 minutes, increase gradually
        local sleep_time=300  # 5 minutes
        if [ $check_count -gt 12 ]; then
            sleep_time=600  # 10 minutes after 1 hour
        fi
        if [ $check_count -gt 24 ]; then
            sleep_time=900  # 15 minutes after 2 hours
        fi
        
        log_with_timestamp "⏱️  Sleeping for $((sleep_time / 60)) minutes until next check..."
        sleep $sleep_time
    done
    
    if [ $check_count -ge $max_checks ]; then
        log_with_timestamp "⚠️  Reached maximum monitoring time (6 hours)"
        send_telegram_update "⚠️  Google Drive folders still not accessible after 6 hours. This suggests we may need a different strategy. Check the log for details."
    fi
    
    log_with_timestamp "🏁 Monitoring completed"
}

# Run main monitoring function
main_monitor

echo "Monitor log saved to: $LOG_FILE"