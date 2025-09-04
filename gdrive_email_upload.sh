#!/bin/bash

# Google Drive Email Upload - IFTTT Integration
# Bypasses OAuth verification by using email triggers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

setup_ifttt_integration() {
    log_info "Setting up IFTTT Email-to-Drive integration..."
    echo
    echo "📋 SETUP STEPS:"
    echo "1. Go to: https://ifttt.com/create"
    echo "2. Choose trigger: Email → 'Send IFTTT an email tagged'"
    echo "3. Set tag: 'gdrive_upload'"
    echo "4. Choose action: Google Drive → 'Add file from URL'"
    echo "5. Set folder: 'made_by_cc' (or any folder)"
    echo "6. Get your trigger email: trigger@applet.ifttt.com"
    echo
    echo "💡 Your trigger email will be: trigger@applet.ifttt.com"
    echo "   Subject format: #gdrive_upload filename.txt"
    echo
    echo "⚡ Once setup, test with:"
    echo "   $0 upload test.txt 'Hello from Claude Code!'"
}

upload_file() {
    local filename="$1"
    local content="$2"
    local folder="${3:-made_by_cc}"
    
    if [ -z "$filename" ] || [ -z "$content" ]; then
        log_error "Usage: upload_file <filename> <content> [folder]"
        return 1
    fi
    
    log_info "Uploading via email to Google Drive..."
    log_info "File: $filename"
    log_info "Folder: $folder"
    
    # Create temporary file
    local temp_file="/tmp/gdrive_upload_$$"
    echo "$content" > "$temp_file"
    
    # Email subject with folder specification
    local subject="#gdrive_upload [$folder] $filename"
    
    # Check if mail command is available
    if ! command -v mail &> /dev/null; then
        log_error "Mail command not found. Installing..."
        sudo apt-get update && sudo apt-get install -y mailutils
    fi
    
    # Send email with attachment
    if command -v mail &> /dev/null; then
        echo "File uploaded via Claude Code bash runner at $(date)" | \
        mail -s "$subject" \
             -A "$temp_file" \
             trigger@applet.ifttt.com
        
        if [ $? -eq 0 ]; then
            log_success "Email sent successfully!"
            log_info "File will appear in Google Drive in 1-5 minutes"
            log_info "Check your Drive folder: $folder"
        else
            log_error "Failed to send email"
        fi
    else
        log_error "Mail system not configured"
        log_info "Alternative: Use python email method"
    fi
    
    # Cleanup
    rm -f "$temp_file"
}

upload_file_python() {
    local filename="$1"
    local content="$2"
    local folder="${3:-made_by_cc}"
    
    python3 << EOF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import os

# Create temp file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write('$content')
    temp_file = f.name

try:
    # Gmail SMTP (you'll need app password)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    
    # Note: User needs to set up Gmail app password
    print("📧 Python email upload requires Gmail app password setup")
    print("🔧 Alternative: Use IFTTT webhook method instead")
    
    # For now, show the webhook approach
    import requests
    
    # IFTTT webhook trigger (user needs to set this up)
    webhook_url = "https://maker.ifttt.com/trigger/gdrive_upload/with/key/YOUR_KEY"
    
    payload = {
        'value1': '$filename',
        'value2': '$content',  
        'value3': '$folder'
    }
    
    print(f"💡 Set up IFTTT webhook at: {webhook_url}")
    print(f"📋 Payload: {payload}")

finally:
    os.unlink(temp_file)
EOF
}

test_upload() {
    log_info "Testing email upload system..."
    
    local test_content="Test upload from Claude Code bash runner
Created: $(date)
Method: Email-to-Drive via IFTTT
Status: Testing upload capability"
    
    upload_file "claude_test_$(date +%s).txt" "$test_content" "made_by_cc"
}

show_status() {
    echo "📊 Google Drive Email Upload Status"
    echo "=================================="
    echo
    echo "✅ Method: Email-to-Drive via IFTTT"
    echo "✅ Bypass: No OAuth verification needed"
    echo "✅ Integration: Works with bash scripts"
    echo "⚠️  Limit: 30MB per file"
    echo "⚠️  Delay: 1-5 minutes processing"
    echo
    echo "🔗 Setup URL: https://ifttt.com/create"
    echo "📧 Trigger: trigger@applet.ifttt.com"
    echo
}

case "$1" in
    "setup")
        setup_ifttt_integration
        ;;
    "upload")
        if [ -n "$2" ] && [ -n "$3" ]; then
            upload_file "$2" "$3" "$4"
        else
            echo "Usage: $0 upload <filename> <content> [folder]"
        fi
        ;;
    "test")
        test_upload
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Google Drive Email Upload - OAuth Verification Bypass"
        echo "===================================================="
        echo
        echo "Usage: $0 {setup|upload|test|status}"
        echo
        echo "Commands:"
        echo "  setup   - Show IFTTT integration setup steps"
        echo "  upload  - Upload file via email"
        echo "  test    - Test upload functionality" 
        echo "  status  - Show current status"
        echo
        echo "Examples:"
        echo "  $0 setup"
        echo "  $0 upload report.txt 'File content here' folder_name"
        echo "  $0 test"
        ;;
esac