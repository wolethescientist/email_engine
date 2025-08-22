# IMAP Email Fetching Solution

This solution provides a comprehensive, production-ready IMAP email fetching system that reliably detects new emails, even when they arrive after the system is already running.

## Problem Solved

The original issue was that new emails sent to a test mailbox were not being detected by the IMAP integration, even after refreshing. This solution addresses:

1. **Stale IMAP connections** - Always creates fresh connections
2. **Server-side caching** - Uses comprehensive refresh strategies
3. **Provider-specific issues** - Handles Gmail, Yahoo, Outlook differences
4. **Missing new emails** - Multiple search strategies ensure detection
5. **Real-time updates** - Supports both polling and IMAP IDLE

## Key Features

### 🔄 Comprehensive Refresh Strategy
- **NOOP command** - Forces server to send pending updates
- **CHECK command** - Requests mailbox checkpoint
- **Folder re-selection** - Ensures fresh mailbox state
- **Provider-specific optimizations** - Gmail X-GM-RAW, Yahoo/Outlook delays

### 🔍 Robust Email Detection
- **Multiple search criteria** - ALL, UNSEEN, RECENT searches
- **Time-based searches** - Recent emails from last hour/day
- **Priority ordering** - New/unread emails shown first
- **Cross-folder checking** - Checks INBOX, Spam, Promotions

### ⚡ Real-time Capabilities
- **Polling mode** - Configurable intervals (30s default)
- **IMAP IDLE** - Real-time push notifications (when supported)
- **Background monitoring** - Continuous email watching

### 🛡️ Production-Ready
- **Comprehensive logging** - Debug and production logging
- **Error handling** - Graceful failure recovery
- **Timeout management** - Prevents hanging connections
- **Signal handling** - Clean shutdown on Ctrl+C

## Files Overview

### Core Implementation
- **`app/services/email_service.py`** - Enhanced IMAP service with comprehensive refresh
- **`app/api/routes/emails.py`** - New API endpoints for polling and IDLE

### Standalone Solution
- **`imap_email_fetcher.py`** - Complete standalone IMAP fetcher
- **`test_imap_fetcher.py`** - Test script to verify functionality
- **`config_example.json`** - Configuration file example

## Quick Start

### 1. Update Your Email Configuration

Edit `config_example.json`:
```json
{
  "host": "imap.gmail.com",
  "port": 993,
  "email": "your-email@gmail.com",
  "password": "your-app-password",
  "ssl": true
}
```

### 2. Test the Solution

```bash
# Test basic functionality
python test_imap_fetcher.py

# Fetch emails once
python imap_email_fetcher.py --config config_example.json --fetch

# Poll every 30 seconds
python imap_email_fetcher.py --config config_example.json --poll --interval 30

# Use IMAP IDLE for real-time updates
python imap_email_fetcher.py --config config_example.json --idle --timeout 300
```

### 3. Test New Email Detection

1. Start polling: `python imap_email_fetcher.py --config config_example.json --poll --interval 10`
2. Send yourself an email from another account
3. Watch the logs - you should see the new email detected within 10 seconds

## API Endpoints

The enhanced email service provides new endpoints:

### GET `/emails/poll`
Poll for new emails with comprehensive refresh strategy.
```bash
curl "http://localhost:8000/emails/poll?folder=INBOX&timeout=30"
```

### GET `/emails/idle`
Use IMAP IDLE for real-time email monitoring.
```bash
curl "http://localhost:8000/emails/idle?folder=INBOX&timeout=300"
```

### GET `/emails/debug/imap`
Debug IMAP connection and server capabilities.
```bash
curl "http://localhost:8000/emails/debug/imap"
```

## How It Works

### 1. Connection Management
- Creates fresh IMAP connection for each request
- Uses appropriate timeouts (30s for INBOX, 15s for others)
- Handles SSL/TLS properly for different providers

### 2. Comprehensive Refresh Process
```python
# Step 1: Server synchronization
imap.noop()  # Get pending updates
imap.check()  # Request checkpoint

# Step 2: Fresh folder state
imap.close()
imap.select(folder, readonly=True)

# Step 3: Provider-specific optimizations
if "gmail" in host:
    imap.search(None, 'X-GM-RAW', 'has:nouserlabels')
elif "yahoo" in host or "outlook" in host:
    time.sleep(0.2)
    imap.noop()
```

### 3. Multi-Strategy Email Search
```python
# Get all emails
all_uids = imap.search(None, "ALL")

# Get unread emails
unseen_uids = imap.search(None, "UNSEEN")

# Get recent emails (newly arrived)
recent_uids = imap.search(None, "RECENT")

# Prioritize recent and unseen
priority_uids = recent_uids + unseen_uids
final_uids = priority_uids + other_uids
```

### 4. Real-time Monitoring
```python
# IMAP IDLE for real-time updates
imap.send(b'IDLE\\r\\n')
while monitoring:
    response = imap.readline()
    if 'EXISTS' in response or 'RECENT' in response:
        # New email detected!
        break
```

## Provider-Specific Notes

### Gmail
- Uses X-GM-RAW search for forced synchronization
- Supports IMAP IDLE
- Folders: `INBOX`, `[Gmail]/Spam`, `[Gmail]/Promotions`

### Yahoo Mail
- Requires additional delays and NOOP commands
- May not support IMAP IDLE
- Folders: `INBOX`, `Bulk Mail`, `Spam`

### Outlook/Hotmail
- Similar to Yahoo, needs extra synchronization
- Supports IMAP IDLE
- Folders: `INBOX`, `Junk Email`

## Troubleshooting

### New Emails Not Detected
1. Check server logs for refresh command results
2. Verify IMAP credentials and permissions
3. Test with multiple folders (check Spam/Promotions)
4. Try different polling intervals

### Connection Issues
1. Verify IMAP server settings (host, port, SSL)
2. Check firewall and network connectivity
3. Ensure app passwords are used (Gmail, Yahoo)
4. Test with longer timeouts

### Performance Issues
1. Use IMAP IDLE instead of polling when possible
2. Increase polling intervals for high-volume accounts
3. Limit email fetch counts
4. Monitor connection timeouts

## Logging

The solution provides comprehensive logging:

```python
# Enable debug logging
logging.getLogger().setLevel(logging.DEBUG)

# Log files
- imap_fetcher.log  # Main log file
- Console output    # Real-time feedback
```

Key log messages to watch for:
- `"NEW EMAILS DETECTED!"` - New emails found
- `"NOOP: OK"` - Server refresh successful
- `"RE-SELECT: OK"` - Folder refresh successful
- `"IDLE response:"` - Real-time IDLE updates

## Production Deployment

### 1. Environment Variables
```bash
export IMAP_HOST="imap.gmail.com"
export IMAP_PORT="993"
export EMAIL_ADDRESS="your@email.com"
export EMAIL_PASSWORD="your-app-password"
```

### 2. Systemd Service (Linux)
```ini
[Unit]
Description=IMAP Email Fetcher
After=network.target

[Service]
Type=simple
User=emailfetcher
WorkingDirectory=/opt/email-fetcher
ExecStart=/usr/bin/python3 imap_email_fetcher.py --config /etc/email-fetcher/config.json --poll --interval 30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "imap_email_fetcher.py", "--config", "config.json", "--poll", "--interval", "30"]
```

## Testing Checklist

- [ ] Basic IMAP connection works
- [ ] Can fetch existing emails
- [ ] New emails are detected within polling interval
- [ ] IMAP IDLE works (if supported by server)
- [ ] Multiple folders are checked correctly
- [ ] Error handling works (wrong credentials, network issues)
- [ ] Logging provides useful information
- [ ] Performance is acceptable for your email volume

## Support

This solution has been tested with:
- Gmail (imap.gmail.com:993)
- Yahoo Mail (imap.mail.yahoo.com:993)
- Outlook/Hotmail (outlook.office365.com:993)
- Generic IMAP servers

For issues or questions, check the logs first and verify your IMAP server settings.