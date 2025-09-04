# Telegram Manager Script

A comprehensive, production-ready Telegram management script built with TDD SOLID architecture principles. Provides secure session-based authentication for reading and sending messages via Telegram.

## 🚀 Quick Start

### Prerequisites
- Python 3.6+ with telethon package
- Bash 4.0+ with jq utility
- Network connectivity to Telegram servers

### Setup
1. **Get Telegram API Credentials:**
   ```bash
   # Visit https://my.telegram.org/apps
   # Create application to get API_ID and API_HASH
   ```

2. **Create Environment File:**
   ```bash
   cat > telegram_manager.env << 'EOF'
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_STRING_SESSION=your_session_string
   EOF
   ```

3. **Generate Session String (one-time):**
   ```bash
   python3 -c "
   from telethon import TelegramClient
   import asyncio
   
   async def main():
       client = TelegramClient('session_name', your_api_id, 'your_api_hash')
       await client.start()
       session_string = client.session.save()
       print(f'Session string: {session_string}')
       await client.disconnect()
   
   asyncio.run(main())
   "
   ```

## 📱 Usage

### Basic Commands
```bash
# Read messages from channel
./telegram_manager.sh read @channel_name [limit]

# Send message to channel
./telegram_manager.sh send @channel_name "Your message"

# Send file to channel
./telegram_manager.sh send_file @channel_name /path/to/file [caption]

# Check system health
./telegram_manager.sh health

# View metrics
./telegram_manager.sh metrics

# Run tests
./telegram_manager.sh test

# Get help
./telegram_manager.sh help
```

### Advanced Features
```bash
# Create rollback point before operations
./telegram_manager.sh rollback rollback_id true

# Comprehensive testing
./telegram_manager.sh test
```

## 🏗️ Architecture

### 5-Layer SOLID Design
- **Layer 1:** Error handling & classification with retry logic
- **Layer 2:** Session lifecycle management with state machine
- **Layer 3:** Dependency validation & version compatibility
- **Layer 4:** Observability with metrics, tracing & health monitoring
- **Layer 5:** Rollback mechanism with state snapshots

### Key Features
- 🔐 Real user session authentication with secure token storage
- 📱 Read from private/public channels with access validation
- 💬 Send messages to channels with format preservation
- 📎 Send files with automatic type detection and progress tracking
- 🔄 Automatic retry with exponential backoff and smart error handling
- 📊 Performance metrics & health monitoring with detailed logging
- 🎯 Comprehensive rollback system with state snapshots
- ⚡ High-performance operation tracing and monitoring
- 🛡️ Robust error classification and recovery strategies
- 🧪 Built with Test-Driven Development (TDD) methodology

## 📊 Channel Formats

- `@username` - Public channels, users, or bots (5-32 characters)
- `@channelname` - Public channels (must start with @)
- `-100xxxxxxxxx` - Private groups and supergroups (numeric ID with -100 prefix)

### Examples
```bash
@aiclubsweggs    # Public channel
@mybot          # Bot account
@john_doe       # User account
-1001234567890  # Private group ID
```

## 📁 File Operations

### Supported Features
- **Max Size:** 2GB (2,147,483,648 bytes)
- **Formats:** All file types supported
- **Path:** Absolute or relative to current directory
- **Permissions:** File must be readable by current user
- **Network:** Large files may timeout on slow connections

### Examples
```bash
# Send file with caption
./telegram_manager.sh send_file @channel /path/to/archive.zip "MCP FALLBACK_SCRIPTS archive"

# Send document without caption
./telegram_manager.sh send_file @group123 ./document.pdf
```

## 🔧 Configuration

### Environment Variables (telegram_manager.env)
```bash
# Required
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_string
TELEGRAM_STRING_SESSION=your_session_string

# Optional
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY=1
HEALTH_CHECK_INTERVAL=60
```

### System Files
- **Config:** `/tmp/telegram_manager/`
- **Logs:** `/tmp/telegram_manager/telegram_manager.log`
- **State:** `/tmp/telegram_manager/state/current_state.json`
- **Rollbacks:** `/tmp/telegram_manager/rollback_points/`

## 🛡️ Error Handling

### Error Categories
- **AUTH:** Authentication or session issues
- **NETWORK:** Connection timeouts or network problems
- **RATE_LIMIT:** API rate limiting or flood control
- **PERMISSION:** Access denied or insufficient permissions
- **FORMAT:** Invalid input format or data structure
- **DEPENDENCY:** Missing system dependencies or packages
- **SYSTEM:** Internal errors or unexpected failures

### Retry Behavior
- Automatic retry with exponential backoff
- Default: 3 attempts with 1, 2, 4 second delays
- Retry triggers: Network errors, temporary failures
- No retry: Authentication failures, permission errors

## 🔄 State Management

### Session States
- **UNINITIALIZED:** Initial state, no session active
- **INITIALIZING:** Connecting and authenticating
- **ACTIVE:** Ready for operations
- **RECONNECTING:** Recovering from connection loss
- **FAILED:** Authentication or critical error
- **TERMINATED:** Clean shutdown completed

### Rollback System
- Automatic snapshots before major operations
- Rollback points stored in `/tmp/telegram_manager/rollback_points/`
- Format: `rollback_YYYYMMDD_HHMMSS.json`
- Contains: State, configuration, operation context
- Cleanup: Old rollback points automatically removed

## 📈 Monitoring & Metrics

### Built-in Metrics
- Success/failure counts
- Response times
- Health checks
- Operation tracing
- Error classification

### Health Monitoring
- Real-time system health checks
- Component status monitoring
- Performance tracking
- Error rate monitoring

## 🧪 Testing

### Comprehensive Test Suite
```bash
# Run all layer tests
./telegram_manager.sh test

# Tests include:
# - Layer 1: Error handling and retry logic
# - Layer 2: Session management and state transitions
# - Layer 3: Dependencies and version compatibility
# - Layer 4: Observability and metrics
# - Layer 5: Rollback mechanism
```

## 🚨 Troubleshooting

### Common Issues
```bash
# Session not authorized
→ Regenerate session string

# Cannot find entity
→ Check channel format and access

# Rate limited
→ Wait and retry later

# File not found
→ Verify file path and permissions

# Connection failed
→ Check network and Telegram status
```

### Debug Mode
```bash
DEBUG=1 ./telegram_manager.sh <command>
```

## 📋 Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success - Operation completed successfully |
| 1 | Invalid Arguments - Wrong command syntax or missing parameters |
| 2 | Authentication Failed - Invalid credentials or expired session |
| 3 | Network Error - Connection timeout or network unavailable |
| 4 | Permission Denied - No access to target channel or operation |
| 5 | Rate Limited - Telegram API rate limit exceeded |
| 6 | File Error - File not found, too large, or permission denied |
| 7 | System Error - Internal error or dependency failure |

## 📚 Examples

### Reading Messages
```bash
# Read last 5 messages
./telegram_manager.sh read @aiclubsweggs 5

# Read single message (default)
./telegram_manager.sh read @mychannel
```

### Sending Messages
```bash
# Send text message
./telegram_manager.sh send @mychannel "Hello world"

# Send with emojis
./telegram_manager.sh send @group "🚀 Update: System maintenance completed"
```

### File Operations
```bash
# Send archive with caption
./telegram_manager.sh send_file @channel /path/to/file.zip "MCP FALLBACK_SCRIPTS archive"

# Send document
./telegram_manager.sh send_file @group123 ./report.pdf "Monthly Report"
```

### System Management
```bash
# Check health
./telegram_manager.sh health

# View metrics
./telegram_manager.sh metrics

# Run tests
./telegram_manager.sh test

# Rollback to previous state
./telegram_manager.sh rollback rollback_20250814_120000 true
```

## 🔒 Security

### Best Practices
- Keep session strings secure and private
- Use environment files for sensitive data
- Regular session regeneration
- Monitor access logs
- Implement rate limiting

### Session Security
- Encrypted session strings
- Automatic session validation
- Secure token storage
- Access logging

## 📞 Support

- **Version:** 6.0.0
- **Compatible:** Telegram Bot API 6.0+, telethon 1.24+
- **Issues:** https://github.com/MiniMax-AI/telegram-manager-mcp

## 🏆 Features

### Core Capabilities
- ✅ Session-based authentication with real user accounts
- ✅ Read from private/public channels
- ✅ Send messages with full formatting
- ✅ File uploads with progress tracking
- ✅ Automatic retry with exponential backoff
- ✅ Comprehensive error handling
- ✅ Performance monitoring and metrics
- ✅ Health checks and system monitoring
- ✅ Rollback system for state recovery
- ✅ Built-in testing framework
- ✅ Production-ready logging

### Technical Excellence
- 🏗️ 5-Layer SOLID architecture
- 🧪 Test-Driven Development methodology
- 📊 Observability and monitoring
- 🔄 State management and rollbacks
- 🛡️ Security best practices
- ⚡ High-performance operations
- 🔧 Comprehensive configuration
- 📚 Extensive documentation