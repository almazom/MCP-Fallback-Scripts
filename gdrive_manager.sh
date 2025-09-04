#!/bin/bash

# Google Drive Manager - CRUD operations through rclone
# Usage: ./gdrive_manager.sh <command> [args...]

# Set PATH to include local bin
export PATH="$HOME/.local/bin:$PATH"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Load environment variables if exists
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

# Default configuration
GDRIVE_REMOTE_NAME="${GDRIVE_REMOTE_NAME:-mydrive}"
GDRIVE_MOUNT_PATH="${GDRIVE_MOUNT_PATH:-$HOME/gdrive_mount}"
GDRIVE_CACHE_DIR="${GDRIVE_CACHE_DIR:-/tmp/gdrive_cache}"
GDRIVE_CONFIG_DIR="${GDRIVE_CONFIG_DIR:-$HOME/.config/rclone}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if rclone is available
check_rclone() {
    if ! command -v rclone &> /dev/null; then
        error "rclone not found in PATH. Please install rclone first."
        exit 1
    fi
}

# Check if remote is configured
check_remote() {
    if ! rclone listremotes | grep -q "^${GDRIVE_REMOTE_NAME}:$"; then
        error "Remote '${GDRIVE_REMOTE_NAME}' not configured."
        echo "Run: ./gdrive_manager.sh config"
        exit 1
    fi
}

# Configure Google Drive remote
configure_gdrive() {
    log "Starting Google Drive configuration..."
    
    echo "You will need:"
    echo "1. Google Cloud Project with Drive API enabled"
    echo "2. OAuth2 Client ID credentials (Desktop application type)"
    echo ""
    echo "Follow the interactive prompts to set up Google Drive access."
    echo ""
    
    mkdir -p "$GDRIVE_CONFIG_DIR"
    
    rclone config create "$GDRIVE_REMOTE_NAME" drive \
        config_is_local=false \
        config_refresh_token=false
    
    if [ $? -eq 0 ]; then
        success "Google Drive remote '$GDRIVE_REMOTE_NAME' configured successfully!"
        log "Testing connection..."
        test_connection
    else
        error "Failed to configure Google Drive remote."
        exit 1
    fi
}

# Test connection to Google Drive
test_connection() {
    log "Testing connection to Google Drive..."
    
    if rclone lsd "${GDRIVE_REMOTE_NAME}:" | head -5; then
        success "Connection successful! Google Drive is accessible."
        return 0
    else
        error "Connection failed. Please check your configuration."
        return 1
    fi
}

# Mount Google Drive as filesystem
mount_gdrive() {
    check_rclone
    check_remote
    
    if mountpoint -q "$GDRIVE_MOUNT_PATH" 2>/dev/null; then
        warning "Google Drive already mounted at $GDRIVE_MOUNT_PATH"
        return 0
    fi
    
    log "Creating mount point: $GDRIVE_MOUNT_PATH"
    mkdir -p "$GDRIVE_MOUNT_PATH"
    mkdir -p "$GDRIVE_CACHE_DIR"
    
    log "Mounting Google Drive at $GDRIVE_MOUNT_PATH..."
    
    rclone mount "${GDRIVE_REMOTE_NAME}:" "$GDRIVE_MOUNT_PATH" \
        --vfs-cache-mode writes \
        --vfs-cache-max-size 1G \
        --cache-dir "$GDRIVE_CACHE_DIR" \
        --daemon \
        --log-level INFO
    
    # Wait a moment for mount to complete
    sleep 2
    
    if mountpoint -q "$GDRIVE_MOUNT_PATH" 2>/dev/null; then
        success "Google Drive mounted successfully at $GDRIVE_MOUNT_PATH"
        log "You can now access Google Drive as a normal filesystem!"
    else
        error "Failed to mount Google Drive."
        exit 1
    fi
}

# Unmount Google Drive
unmount_gdrive() {
    if ! mountpoint -q "$GDRIVE_MOUNT_PATH" 2>/dev/null; then
        warning "Google Drive not mounted at $GDRIVE_MOUNT_PATH"
        return 0
    fi
    
    log "Unmounting Google Drive from $GDRIVE_MOUNT_PATH..."
    
    if fusermount -u "$GDRIVE_MOUNT_PATH" 2>/dev/null || umount "$GDRIVE_MOUNT_PATH" 2>/dev/null; then
        success "Google Drive unmounted successfully."
    else
        error "Failed to unmount Google Drive. Trying force unmount..."
        fusermount -u -z "$GDRIVE_MOUNT_PATH" 2>/dev/null
    fi
}

# List files/folders
list_files() {
    local path="${1:-}"
    check_rclone
    check_remote
    
    log "Listing contents of: ${GDRIVE_REMOTE_NAME}:${path}"
    rclone lsl "${GDRIVE_REMOTE_NAME}:${path}"
}

# Read file content
read_file() {
    local file_path="$1"
    
    if [ -z "$file_path" ]; then
        error "Please specify a file path."
        echo "Usage: $0 read <file_path>"
        exit 1
    fi
    
    check_rclone
    check_remote
    
    log "Reading file: ${GDRIVE_REMOTE_NAME}:${file_path}"
    rclone cat "${GDRIVE_REMOTE_NAME}:${file_path}"
}

# Write/create file
write_file() {
    local file_path="$1"
    local content="$2"
    local local_file="$3"
    
    if [ -z "$file_path" ]; then
        error "Please specify a file path."
        echo "Usage: $0 write <remote_path> [content] [local_file]"
        exit 1
    fi
    
    check_rclone
    check_remote
    
    if [ -n "$local_file" ]; then
        # Copy from local file
        log "Uploading file: $local_file -> ${GDRIVE_REMOTE_NAME}:${file_path}"
        rclone copyto "$local_file" "${GDRIVE_REMOTE_NAME}:${file_path}"
    elif [ -n "$content" ]; then
        # Write content from string
        log "Writing content to: ${GDRIVE_REMOTE_NAME}:${file_path}"
        echo "$content" | rclone rcat "${GDRIVE_REMOTE_NAME}:${file_path}"
    else
        # Read from stdin
        log "Writing from stdin to: ${GDRIVE_REMOTE_NAME}:${file_path}"
        rclone rcat "${GDRIVE_REMOTE_NAME}:${file_path}"
    fi
    
    if [ $? -eq 0 ]; then
        success "File written successfully: ${file_path}"
    else
        error "Failed to write file: ${file_path}"
        exit 1
    fi
}

# Delete file/folder
delete_file() {
    local file_path="$1"
    
    if [ -z "$file_path" ]; then
        error "Please specify a file/folder path."
        echo "Usage: $0 delete <file_path>"
        exit 1
    fi
    
    check_rclone
    check_remote
    
    log "Deleting: ${GDRIVE_REMOTE_NAME}:${file_path}"
    
    # Ask for confirmation
    echo -n "Are you sure you want to delete '${file_path}'? (y/N): "
    read -r confirmation
    
    if [[ "$confirmation" =~ ^[Yy]$ ]]; then
        rclone deletefile "${GDRIVE_REMOTE_NAME}:${file_path}" 2>/dev/null || \
        rclone purge "${GDRIVE_REMOTE_NAME}:${file_path}"
        
        if [ $? -eq 0 ]; then
            success "Deleted successfully: ${file_path}"
        else
            error "Failed to delete: ${file_path}"
            exit 1
        fi
    else
        log "Deletion cancelled."
    fi
}

# Create folder
mkdir_remote() {
    local folder_path="$1"
    
    if [ -z "$folder_path" ]; then
        error "Please specify a folder path."
        echo "Usage: $0 mkdir <folder_path>"
        exit 1
    fi
    
    check_rclone
    check_remote
    
    log "Creating folder: ${GDRIVE_REMOTE_NAME}:${folder_path}"
    rclone mkdir "${GDRIVE_REMOTE_NAME}:${folder_path}"
    
    if [ $? -eq 0 ]; then
        success "Folder created successfully: ${folder_path}"
    else
        error "Failed to create folder: ${folder_path}"
        exit 1
    fi
}

# Sync local folder with remote
sync_folders() {
    local local_path="$1"
    local remote_path="$2"
    local direction="${3:-up}"
    
    if [ -z "$local_path" ] || [ -z "$remote_path" ]; then
        error "Please specify both local and remote paths."
        echo "Usage: $0 sync <local_path> <remote_path> [up|down|both]"
        exit 1
    fi
    
    check_rclone
    check_remote
    
    case "$direction" in
        "up")
            log "Syncing UP: $local_path -> ${GDRIVE_REMOTE_NAME}:${remote_path}"
            rclone sync "$local_path" "${GDRIVE_REMOTE_NAME}:${remote_path}" --progress
            ;;
        "down")
            log "Syncing DOWN: ${GDRIVE_REMOTE_NAME}:${remote_path} -> $local_path"
            rclone sync "${GDRIVE_REMOTE_NAME}:${remote_path}" "$local_path" --progress
            ;;
        "both")
            log "Syncing BOTH ways: $local_path <-> ${GDRIVE_REMOTE_NAME}:${remote_path}"
            rclone bisync "$local_path" "${GDRIVE_REMOTE_NAME}:${remote_path}" --progress
            ;;
        *)
            error "Invalid direction. Use: up, down, or both"
            exit 1
            ;;
    esac
}

# Status check
status() {
    log "=== Google Drive Manager Status ==="
    echo "Remote name: $GDRIVE_REMOTE_NAME"
    echo "Mount path: $GDRIVE_MOUNT_PATH"
    echo "Cache dir: $GDRIVE_CACHE_DIR"
    echo "Config dir: $GDRIVE_CONFIG_DIR"
    echo ""
    
    # Check rclone
    if command -v rclone &> /dev/null; then
        echo "rclone: $(rclone version | head -1)"
    else
        echo "rclone: NOT FOUND"
    fi
    
    # Check remote configuration
    if rclone listremotes | grep -q "^${GDRIVE_REMOTE_NAME}:$"; then
        echo "Remote '$GDRIVE_REMOTE_NAME': CONFIGURED"
        
        # Test connection
        if rclone lsd "${GDRIVE_REMOTE_NAME}:" &>/dev/null; then
            echo "Connection: OK"
        else
            echo "Connection: FAILED"
        fi
    else
        echo "Remote '$GDRIVE_REMOTE_NAME': NOT CONFIGURED"
    fi
    
    # Check mount
    if mountpoint -q "$GDRIVE_MOUNT_PATH" 2>/dev/null; then
        echo "Mount: ACTIVE at $GDRIVE_MOUNT_PATH"
    else
        echo "Mount: NOT MOUNTED"
    fi
}

# Show help
show_help() {
    echo "Google Drive Manager - CRUD operations for Google Drive"
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "Configuration Commands:"
    echo "  config                    - Configure Google Drive remote"
    echo "  status                    - Show current status"
    echo "  test                      - Test connection to Google Drive"
    echo ""
    echo "Mount Commands:"
    echo "  mount                     - Mount Google Drive as filesystem"
    echo "  unmount                   - Unmount Google Drive"
    echo ""
    echo "File Operations:"
    echo "  list [path]               - List files/folders"
    echo "  read <file_path>          - Read file content"
    echo "  write <file_path> [content] [local_file]  - Write/upload file"
    echo "  delete <file_path>        - Delete file/folder"
    echo "  mkdir <folder_path>       - Create folder"
    echo ""
    echo "Sync Operations:"
    echo "  sync <local> <remote> [up|down|both]  - Sync folders"
    echo ""
    echo "Examples:"
    echo "  $0 config                 # Configure Google Drive"
    echo "  $0 mount                  # Mount as filesystem"
    echo "  $0 list                   # List root folder"
    echo "  $0 read \"My Document.txt\" # Read file content"
    echo "  $0 write \"new.txt\" \"Hello World\"  # Create file with content"
    echo "  $0 write \"upload.txt\" \"\" \"/path/to/local.txt\"  # Upload local file"
    echo "  $0 sync ./local_folder remote_folder up  # Sync local to remote"
    echo ""
    echo "Configuration:"
    echo "  Environment variables can be set in: $ENV_FILE"
    echo "  GDRIVE_REMOTE_NAME (default: mydrive)"
    echo "  GDRIVE_MOUNT_PATH (default: ~/gdrive_mount)"
    echo "  GDRIVE_CACHE_DIR (default: /tmp/gdrive_cache)"
}

# Main command dispatcher
main() {
    local command="$1"
    shift
    
    case "$command" in
        "config")
            configure_gdrive
            ;;
        "test")
            check_rclone
            test_connection
            ;;
        "mount")
            mount_gdrive
            ;;
        "unmount")
            unmount_gdrive
            ;;
        "list"|"ls")
            list_files "$1"
            ;;
        "read"|"cat")
            read_file "$1"
            ;;
        "write"|"upload")
            write_file "$1" "$2" "$3"
            ;;
        "delete"|"rm")
            delete_file "$1"
            ;;
        "mkdir")
            mkdir_remote "$1"
            ;;
        "sync")
            sync_folders "$1" "$2" "$3"
            ;;
        "status")
            status
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"