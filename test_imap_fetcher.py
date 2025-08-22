#!/usr/bin/env python3
"""
Test script for the IMAP Email Fetcher
=====================================

This script tests the IMAP email fetching functionality with your email account.
It demonstrates all the key features and helps verify that new emails are being detected.

Usage:
    python test_imap_fetcher.py
"""

import json
import time
from imap_email_fetcher import IMAPEmailFetcher

def test_email_fetching():
    """Test the email fetching functionality."""
    
    # Configuration - UPDATE THESE VALUES
    config = {
        "host": "imap.gmail.com",  # Change to your IMAP server
        "port": 993,
        "email": "your-email@gmail.com",  # Change to your email
        "password": "your-app-password",  # Change to your password/app password
        "use_ssl": True
    }
    
    print("IMAP Email Fetcher Test")
    print("=" * 50)
    print(f"Testing with: {config['email']} on {config['host']}")
    print()
    
    # Create fetcher instance
    fetcher = IMAPEmailFetcher(
        host=config["host"],
        port=config["port"],
        email=config["email"],
        password=config["password"],
        use_ssl=config["use_ssl"]
    )
    
    # Test 1: Basic connection and folder check
    print("Test 1: Checking multiple folders...")
    folder_result = fetcher.check_multiple_folders()
    if folder_result["success"]:
        print("✓ Successfully checked folders")
        for folder, info in folder_result["results"].items():
            if info.get("accessible"):
                print(f"  - {folder}: {info['total_emails']} total, {info['unseen_emails']} unseen, {info['recent_emails']} recent")
            else:
                print(f"  - {folder}: Not accessible ({info.get('error', 'Unknown error')})")
    else:
        print(f"✗ Folder check failed: {folder_result.get('error')}")
    print()
    
    # Test 2: Fetch emails from INBOX
    print("Test 2: Fetching emails from INBOX...")
    fetch_result = fetcher.fetch_emails("INBOX", limit=5)
    if fetch_result["success"]:
        print("✓ Successfully fetched emails")
        print(f"  - Total emails: {fetch_result['total_emails']}")
        print(f"  - Unseen emails: {fetch_result['unseen_emails']}")
        print(f"  - Recent emails: {fetch_result['recent_emails']}")
        print(f"  - Refresh commands: {', '.join(fetch_result['refresh_commands'])}")
        
        if fetch_result["new_emails"]:
            print("  - Recent/New emails:")
            for email in fetch_result["new_emails"]:
                print(f"    * {email['subject']} from {email['from']} ({'unread' if not email['is_read'] else 'read'})")
        else:
            print("  - No recent/new emails found")
    else:
        print(f"✗ Email fetch failed: {fetch_result.get('error')}")
    print()
    
    # Test 3: Test IMAP IDLE (if supported)
    print("Test 3: Testing IMAP IDLE support...")
    idle_result = fetcher.idle_monitor("INBOX", timeout_seconds=10)  # Short timeout for testing
    if idle_result["success"]:
        print("✓ IMAP IDLE is supported")
        print(f"  - Monitored for {idle_result['idle_duration']:.1f} seconds")
        print(f"  - Updates received: {len(idle_result['updates_received'])}")
        if idle_result["new_emails_detected"]:
            print("  - NEW EMAILS DETECTED during IDLE!")
        else:
            print("  - No new emails detected during IDLE")
    else:
        print(f"✗ IMAP IDLE failed: {idle_result.get('error')}")
    print()
    
    # Test 4: Demonstrate polling (short test)
    print("Test 4: Testing polling (3 iterations, 5 second intervals)...")
    print("This will poll for new emails 3 times with 5-second intervals.")
    print("Send yourself an email during this test to see it detected!")
    print()
    
    try:
        fetcher.poll_emails(interval_seconds=5, max_iterations=3)
        print("✓ Polling test completed")
    except KeyboardInterrupt:
        print("✓ Polling interrupted by user")
    print()
    
    print("Test Summary:")
    print("=" * 50)
    print("✓ All tests completed!")
    print()
    print("To test new email detection:")
    print("1. Send yourself an email")
    print("2. Run: python imap_email_fetcher.py --config config_example.json --fetch")
    print("3. Or use polling: python imap_email_fetcher.py --config config_example.json --poll --interval 10")
    print("4. Or use IDLE: python imap_email_fetcher.py --config config_example.json --idle --timeout 60")


if __name__ == "__main__":
    test_email_fetching()