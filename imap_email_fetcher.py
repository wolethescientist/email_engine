#!/usr/bin/env python3
"""
Production-Ready IMAP Email Fetcher
===================================

This script demonstrates a comprehensive IMAP email fetching solution that:
1. Always fetches new emails when refreshed or polled
2. Handles provider delays and connection issues
3. Detects emails in various folders (INBOX, Spam, Promotions)
4. Supports both polling and IMAP IDLE for real-time updates
5. Includes extensive logging and error handling
6. Works with Gmail, Yahoo, Outlook, and other providers

Usage:
    python imap_email_fetcher.py --host imap.gmail.com --email your@gmail.com --password your_password
    python imap_email_fetcher.py --config config.json --poll --interval 30
    python imap_email_fetcher.py --config config.json --idle --timeout 300
"""

import imaplib
import email
import time
import json
import argparse
import logging
import ssl
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import getaddresses, formataddr
from email.parser import BytesParser
from email import policy
from typing import List, Dict, Optional, Tuple
import threading
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('imap_fetcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class IMAPEmailFetcher:
    """Production-ready IMAP email fetcher with comprehensive refresh strategies."""
    
    def __init__(self, host: str, port: int, email: str, password: str, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.email = email
        self.password = password
        self.use_ssl = use_ssl
        self.running = False
        
        logger.info(f"Initialized IMAP fetcher for {email} on {host}:{port} (SSL: {use_ssl})")
    
    def connect(self, timeout_seconds: int = 30) -> imaplib.IMAP4:
        """Create a fresh IMAP connection with proper error handling."""
        try:
            if self.use_ssl:
                imap = imaplib.IMAP4_SSL(host=self.host, port=self.port, timeout=timeout_seconds)
            else:
                imap = imaplib.IMAP4(host=self.host, port=self.port, timeout=timeout_seconds)
                imap.starttls(ssl_context=ssl.create_default_context())
            
            imap.login(self.email, self.password)
            logger.info(f"Successfully connected to IMAP server {self.host}")
            return imap
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            raise
    
    def comprehensive_refresh(self, imap: imaplib.IMAP4, folder: str) -> List[str]:
        """
        Comprehensive refresh strategy to ensure new emails are detected.
        Returns list of refresh commands executed.
        """
        refresh_commands = []
        
        try:
            # Step 1: NOOP to get server updates
            try:
                imap.noop()
                refresh_commands.append("NOOP: OK")
                logger.debug("NOOP command successful")
            except Exception as e:
                refresh_commands.append(f"NOOP: FAILED - {e}")
                logger.warning(f"NOOP failed: {e}")
            
            # Step 2: CHECK for mailbox checkpoint
            try:
                imap.check()
                refresh_commands.append("CHECK: OK")
                logger.debug("CHECK command successful")
            except Exception as e:
                refresh_commands.append(f"CHECK: FAILED - {e}")
                logger.warning(f"CHECK failed: {e}")
            
            # Step 3: Re-select folder for fresh state
            try:
                imap.close()
                status, response = imap.select(folder, readonly=True)
                if status == "OK":
                    refresh_commands.append("RE-SELECT: OK")
                    logger.debug(f"Folder {folder} re-selected successfully")
                else:
                    refresh_commands.append(f"RE-SELECT: FAILED - {status}")
                    logger.warning(f"Folder re-selection failed: {status}")
            except Exception as e:
                refresh_commands.append(f"RE-SELECT: FAILED - {e}")
                logger.warning(f"Folder re-selection failed: {e}")
                # Fallback to original selection
                imap.select(folder, readonly=True)
            
            # Step 4: Provider-specific optimizations
            if "gmail" in self.host.lower():
                try:
                    # Gmail-specific: force sync with X-GM-RAW
                    status, _ = imap.search(None, 'X-GM-RAW', 'has:nouserlabels')
                    refresh_commands.append(f"Gmail X-GM-RAW: {status}")
                    logger.debug(f"Gmail X-GM-RAW search status: {status}")
                except Exception as e:
                    refresh_commands.append(f"Gmail X-GM-RAW: FAILED - {e}")
                    logger.debug(f"Gmail X-GM-RAW not supported: {e}")
            
            elif any(provider in self.host.lower() for provider in ["yahoo", "outlook", "hotmail", "live"]):
                try:
                    time.sleep(0.2)  # Small delay for Yahoo/Outlook
                    imap.noop()
                    refresh_commands.append("Provider-specific NOOP: OK")
                    logger.debug("Additional NOOP for Yahoo/Outlook completed")
                except Exception as e:
                    refresh_commands.append(f"Provider-specific NOOP: FAILED - {e}")
                    logger.warning(f"Additional NOOP failed: {e}")
            
        except Exception as e:
            logger.error(f"Comprehensive refresh failed: {e}")
            refresh_commands.append(f"REFRESH ERROR: {e}")
        
        return refresh_commands
    
    def search_emails(self, imap: imaplib.IMAP4, folder: str) -> Dict:
        """
        Search for emails using multiple strategies to ensure new emails are found.
        """
        results = {
            "total_emails": 0,
            "unseen_emails": 0,
            "recent_emails": 0,
            "all_uids": [],
            "unseen_uids": [],
            "recent_uids": []
        }
        
        try:
            # Search for all emails
            status, all_data = imap.search(None, "ALL")
            if status == "OK" and all_data and all_data[0]:
                results["all_uids"] = all_data[0].split()
                results["total_emails"] = len(results["all_uids"])
                logger.info(f"Found {results['total_emails']} total emails in {folder}")
            
            # Search for unseen emails (new/unread)
            status, unseen_data = imap.search(None, "UNSEEN")
            if status == "OK" and unseen_data and unseen_data[0]:
                results["unseen_uids"] = unseen_data[0].split()
                results["unseen_emails"] = len(results["unseen_uids"])
                logger.info(f"Found {results['unseen_emails']} unseen emails: {results['unseen_uids']}")
            
            # Search for recent emails (newly arrived)
            status, recent_data = imap.search(None, "RECENT")
            if status == "OK" and recent_data and recent_data[0]:
                results["recent_uids"] = recent_data[0].split()
                results["recent_emails"] = len(results["recent_uids"])
                logger.info(f"Found {results['recent_emails']} recent emails: {results['recent_uids']}")
            
            # For additional coverage, search for emails from the last hour
            try:
                one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
                status, recent_hour_data = imap.search(None, f'SINCE "{one_hour_ago}"')
                if status == "OK" and recent_hour_data and recent_hour_data[0]:
                    recent_hour_uids = recent_hour_data[0].split()
                    logger.info(f"Found {len(recent_hour_uids)} emails from last hour")
                    # Add to recent if not already there
                    for uid in recent_hour_uids:
                        if uid not in results["recent_uids"]:
                            results["recent_uids"].append(uid)
                    results["recent_emails"] = len(results["recent_uids"])
            except Exception as e:
                logger.debug(f"Recent hour search failed: {e}")
            
        except Exception as e:
            logger.error(f"Email search failed: {e}")
        
        return results
    
    def parse_email_headers(self, imap: imaplib.IMAP4, uid: bytes) -> Optional[Dict]:
        """Parse email headers and return basic information."""
        try:
            status, msg_data = imap.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE TO)] FLAGS)")
            if status != "OK" or not msg_data:
                return None
            
            raw_bytes = b""
            flags_info = ""
            for part in msg_data:
                if isinstance(part, tuple):
                    raw_bytes += part[1]
                else:
                    flags_info = str(part)
            
            # Parse headers
            msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            
            # Decode subject
            subject = "No Subject"
            if msg.get('Subject'):
                dh = decode_header(msg.get('Subject'))
                subject = str(make_header(dh))
            
            # Parse from address
            from_addr = "Unknown Sender"
            if msg.get('From'):
                from_parsed = getaddresses([msg.get('From')])
                from_addr = formataddr(from_parsed[0]) if from_parsed else msg.get('From')
            
            # Parse to addresses
            to_addrs = []
            if msg.get('To'):
                to_parsed = getaddresses([msg.get('To')])
                to_addrs = [formataddr(t) for t in to_parsed]
            
            # Parse date
            date = msg.get('Date', 'Unknown Date')
            
            # Parse flags
            is_read = "\\Seen" in flags_info
            is_recent = "\\Recent" in flags_info
            
            return {
                "uid": uid.decode() if isinstance(uid, bytes) else str(uid),
                "subject": subject,
                "from": from_addr,
                "to": to_addrs,
                "date": date,
                "is_read": is_read,
                "is_recent": is_recent,
                "flags": flags_info
            }
            
        except Exception as e:
            logger.error(f"Failed to parse email UID {uid}: {e}")
            return None
    
    def fetch_emails(self, folder: str = "INBOX", limit: int = 10) -> Dict:
        """
        Fetch emails from specified folder with comprehensive refresh strategy.
        """
        logger.info(f"Starting email fetch from {folder} (limit: {limit})")
        
        try:
            imap = self.connect()
            try:
                # Select folder
                status, select_response = imap.select(folder, readonly=True)
                if status != "OK":
                    logger.error(f"Failed to select folder {folder}: {select_response}")
                    return {"success": False, "error": f"Failed to select folder {folder}"}
                
                logger.info(f"Selected folder {folder}: {select_response}")
                
                # Comprehensive refresh
                refresh_commands = self.comprehensive_refresh(imap, folder)
                
                # Search for emails
                search_results = self.search_emails(imap, folder)
                
                # Get details of recent/new emails
                new_emails = []
                priority_uids = list(dict.fromkeys(search_results["recent_uids"] + search_results["unseen_uids"]))
                
                for uid in priority_uids[:limit]:
                    email_info = self.parse_email_headers(imap, uid)
                    if email_info:
                        new_emails.append(email_info)
                        logger.info(f"Parsed email: {email_info['subject']} from {email_info['from']}")
                
                return {
                    "success": True,
                    "folder": folder,
                    "refresh_commands": refresh_commands,
                    "total_emails": search_results["total_emails"],
                    "unseen_emails": search_results["unseen_emails"],
                    "recent_emails": search_results["recent_emails"],
                    "new_emails": new_emails,
                    "timestamp": datetime.now().isoformat()
                }
                
            finally:
                try:
                    imap.logout()
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Email fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    def check_multiple_folders(self, folders: List[str] = None) -> Dict:
        """
        Check multiple folders for new emails (INBOX, Spam, Promotions, etc.)
        """
        if folders is None:
            folders = ["INBOX", "[Gmail]/Spam", "[Gmail]/Promotions", "Junk", "Spam"]
        
        logger.info(f"Checking multiple folders: {folders}")
        results = {}
        
        try:
            imap = self.connect()
            try:
                # List available folders first
                status, folder_list = imap.list()
                available_folders = []
                if status == "OK":
                    for folder_info in folder_list:
                        folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                        available_folders.append(folder_str)
                        logger.debug(f"Available folder: {folder_str}")
                
                # Check each requested folder
                for folder in folders:
                    try:
                        status, _ = imap.select(folder, readonly=True)
                        if status == "OK":
                            logger.info(f"Checking folder: {folder}")
                            
                            # Quick refresh and search
                            imap.noop()
                            search_results = self.search_emails(imap, folder)
                            
                            results[folder] = {
                                "accessible": True,
                                "total_emails": search_results["total_emails"],
                                "unseen_emails": search_results["unseen_emails"],
                                "recent_emails": search_results["recent_emails"]
                            }
                            
                            if search_results["recent_emails"] > 0 or search_results["unseen_emails"] > 0:
                                logger.warning(f"Found new emails in {folder}!")
                        else:
                            results[folder] = {"accessible": False, "error": f"Cannot select folder: {status}"}
                            logger.debug(f"Cannot access folder {folder}: {status}")
                    except Exception as e:
                        results[folder] = {"accessible": False, "error": str(e)}
                        logger.debug(f"Error checking folder {folder}: {e}")
                
                results["available_folders"] = available_folders
                return {"success": True, "results": results}
                
            finally:
                try:
                    imap.logout()
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Multiple folder check failed: {e}")
            return {"success": False, "error": str(e)}
    
    def poll_emails(self, interval_seconds: int = 30, max_iterations: int = None):
        """
        Poll for new emails at regular intervals.
        """
        logger.info(f"Starting email polling every {interval_seconds} seconds")
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"Reached maximum iterations ({max_iterations})")
                    break
                
                iteration += 1
                logger.info(f"Polling iteration {iteration}")
                
                # Fetch emails
                result = self.fetch_emails()
                
                if result["success"]:
                    if result["recent_emails"] > 0 or result["unseen_emails"] > 0:
                        logger.info(f"NEW EMAILS DETECTED! Recent: {result['recent_emails']}, Unseen: {result['unseen_emails']}")
                        for email in result["new_emails"]:
                            logger.info(f"  - {email['subject']} from {email['from']}")
                    else:
                        logger.info("No new emails found")
                else:
                    logger.error(f"Polling failed: {result.get('error', 'Unknown error')}")
                
                # Wait for next iteration
                if self.running:
                    time.sleep(interval_seconds)
                    
        except KeyboardInterrupt:
            logger.info("Polling interrupted by user")
        finally:
            self.running = False
    
    def idle_monitor(self, folder: str = "INBOX", timeout_seconds: int = 300) -> Dict:
        """
        Use IMAP IDLE to monitor for new emails in real-time.
        """
        logger.info(f"Starting IMAP IDLE monitor for {folder} (timeout: {timeout_seconds}s)")
        
        try:
            imap = self.connect(timeout_seconds=timeout_seconds)
            try:
                # Check if server supports IDLE
                if 'IDLE' not in imap.capabilities:
                    logger.error("Server does not support IMAP IDLE")
                    return {
                        "success": False,
                        "error": "Server does not support IMAP IDLE",
                        "capabilities": list(imap.capabilities)
                    }
                
                # Select folder
                status, _ = imap.select(folder, readonly=True)
                if status != "OK":
                    return {"success": False, "error": f"Failed to select folder {folder}"}
                
                logger.info(f"Starting IDLE command for {folder}")
                
                # Start IDLE
                tag = imap._new_tag()
                imap.send(f'{tag} IDLE\r\n'.encode())
                
                # Wait for server response
                response = imap.readline()
                if b'+ idling' not in response.lower() and b'+ waiting' not in response.lower():
                    return {"success": False, "error": f"IDLE command failed: {response.decode()}"}
                
                logger.info("IDLE started successfully, waiting for updates...")
                
                # Monitor for updates
                updates = []
                start_time = time.time()
                
                while time.time() - start_time < timeout_seconds:
                    try:
                        imap.sock.settimeout(1.0)
                        response = imap.readline()
                        
                        if response:
                            response_str = response.decode().strip()
                            logger.info(f"IDLE response: {response_str}")
                            updates.append(response_str)
                            
                            if 'EXISTS' in response_str or 'RECENT' in response_str:
                                logger.info(f"NEW EMAIL DETECTED: {response_str}")
                                break
                                
                    except Exception as e:
                        if "timed out" not in str(e).lower():
                            logger.debug(f"IDLE monitoring error: {e}")
                        continue
                
                # End IDLE
                try:
                    imap.send(b'DONE\r\n')
                    response = imap.readline()
                    logger.info(f"IDLE ended: {response.decode()}")
                except Exception as e:
                    logger.warning(f"Failed to end IDLE cleanly: {e}")
                
                # Check for new emails after IDLE
                search_results = self.search_emails(imap, folder)
                
                return {
                    "success": True,
                    "folder": folder,
                    "idle_duration": time.time() - start_time,
                    "updates_received": updates,
                    "total_emails": search_results["total_emails"],
                    "unseen_emails": search_results["unseen_emails"],
                    "recent_emails": search_results["recent_emails"],
                    "new_emails_detected": any('EXISTS' in update or 'RECENT' in update for update in updates)
                }
                
            finally:
                try:
                    imap.logout()
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"IDLE monitor failed: {e}")
            return {"success": False, "error": str(e)}


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    logger.info("Received interrupt signal, shutting down...")
    sys.exit(0)


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description="Production-Ready IMAP Email Fetcher")
    
    # Connection parameters
    parser.add_argument("--host", help="IMAP server hostname")
    parser.add_argument("--port", type=int, default=993, help="IMAP server port (default: 993)")
    parser.add_argument("--email", help="Email address")
    parser.add_argument("--password", help="Email password")
    parser.add_argument("--no-ssl", action="store_true", help="Disable SSL/TLS")
    
    # Configuration file
    parser.add_argument("--config", help="JSON configuration file")
    
    # Operation modes
    parser.add_argument("--fetch", action="store_true", help="Fetch emails once")
    parser.add_argument("--poll", action="store_true", help="Poll for emails continuously")
    parser.add_argument("--idle", action="store_true", help="Use IMAP IDLE for real-time monitoring")
    parser.add_argument("--check-folders", action="store_true", help="Check multiple folders for emails")
    
    # Parameters
    parser.add_argument("--folder", default="INBOX", help="Folder to check (default: INBOX)")
    parser.add_argument("--interval", type=int, default=30, help="Polling interval in seconds (default: 30)")
    parser.add_argument("--timeout", type=int, default=300, help="IDLE timeout in seconds (default: 300)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum emails to fetch (default: 10)")
    parser.add_argument("--max-iterations", type=int, help="Maximum polling iterations")
    
    # Logging
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return 1
    
    # Get connection parameters
    host = args.host or config.get("host")
    port = args.port or config.get("port", 993)
    email = args.email or config.get("email")
    password = args.password or config.get("password")
    use_ssl = not args.no_ssl and config.get("ssl", True)
    
    if not all([host, email, password]):
        logger.error("Missing required parameters: host, email, password")
        parser.print_help()
        return 1
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create fetcher
    fetcher = IMAPEmailFetcher(host, port, email, password, use_ssl)
    
    try:
        if args.check_folders:
            logger.info("Checking multiple folders...")
            result = fetcher.check_multiple_folders()
            print(json.dumps(result, indent=2))
            
        elif args.idle:
            logger.info("Starting IMAP IDLE monitoring...")
            result = fetcher.idle_monitor(args.folder, args.timeout)
            print(json.dumps(result, indent=2))
            
        elif args.poll:
            logger.info("Starting email polling...")
            fetcher.poll_emails(args.interval, args.max_iterations)
            
        else:  # Default: fetch once
            logger.info("Fetching emails...")
            result = fetcher.fetch_emails(args.folder, args.limit)
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())