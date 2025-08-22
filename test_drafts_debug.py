#!/usr/bin/env python3
"""
Test script for debugging draft functionality in the email engine.
This script helps create test drafts and verify they can be retrieved.
"""

import json
import requests
from typing import Dict, Any
import base64

class EmailEngineDebugger:
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    def set_auth_token(self, token: str):
        """Set authentication token for API requests."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def create_test_draft(self, subject: str = None, body: str = None, to_emails: list = None) -> Dict[str, Any]:
        """Create a test draft."""
        if subject is None:
            subject = "Test Draft - Debug"
        if body is None:
            body = "This is a test draft created for debugging purposes."
        if to_emails is None:
            to_emails = ["test@example.com"]
        
        payload = {
            "subject": subject,
            "body": body,
            "to": to_emails,
            "cc": [],
            "bcc": [],
            "attachments": []
        }
        
        print(f"Creating draft with payload: {json.dumps(payload, indent=2)}")
        
        response = self.session.post(f"{self.base_url}/emails/compose", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Draft created successfully with ID: {result.get('id')}")
            return result
        else:
            print(f"❌ Failed to create draft: {response.status_code} - {response.text}")
            return {}
    
    def create_test_draft_with_attachment(self) -> Dict[str, Any]:
        """Create a test draft with a simple text attachment."""
        # Create a simple text file content
        text_content = "This is a test attachment for debugging."
        text_bytes = text_content.encode('utf-8')
        text_base64 = base64.b64encode(text_bytes).decode('utf-8')
        
        payload = {
            "subject": "Test Draft with Attachment - Debug",
            "body": "This draft has a test attachment.",
            "to": ["test@example.com"],
            "cc": [],
            "bcc": [],
            "attachments": [
                {
                    "filename": "test_attachment.txt",
                    "content_base64": text_base64,
                    "content_type": "text/plain"
                }
            ]
        }
        
        print(f"Creating draft with attachment...")
        
        response = self.session.post(f"{self.base_url}/emails/compose", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Draft with attachment created successfully with ID: {result.get('id')}")
            return result
        else:
            print(f"❌ Failed to create draft with attachment: {response.status_code} - {response.text}")
            return {}
    
    def get_drafts(self, page: int = 1, size: int = 50) -> Dict[str, Any]:
        """Get all drafts using the official endpoint."""
        response = self.session.get(f"{self.base_url}/emails/drafts", params={"page": page, "size": size})
        print(f"Get drafts response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved drafts: {result.get('total', 0)} total")
            return result
        else:
            print(f"❌ Failed to get drafts: {response.status_code} - {response.text}")
            return {}
    
    def debug_all_emails(self) -> Dict[str, Any]:
        """Get all emails from the debug endpoint."""
        response = self.session.get(f"{self.base_url}/emails/debug/all-emails")
        print(f"Debug all emails response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Debug info - Total emails: {result.get('total_emails', 0)}")
            print(f"   Folders: {result.get('folders', [])}")
            print(f"   Drafts count: {result.get('drafts_count', 0)}")
            return result
        else:
            print(f"❌ Failed to get debug info: {response.status_code} - {response.text}")
            return {}
    
    def debug_drafts_detailed(self) -> Dict[str, Any]:
        """Get detailed draft information from the debug endpoint."""
        response = self.session.get(f"{self.base_url}/emails/debug/drafts-detailed")
        print(f"Debug drafts detailed response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Detailed draft info - Total drafts: {result.get('total_drafts', 0)}")
            return result
        else:
            print(f"❌ Failed to get detailed draft info: {response.status_code} - {response.text}")
            return {}
    
    def test_imap_drafts_connectivity(self) -> Dict[str, Any]:
        """Test IMAP drafts folder connectivity."""
        response = self.session.get(f"{self.base_url}/emails/debug/imap-drafts-test")
        print(f"IMAP drafts test response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print(f"✅ IMAP drafts accessible - Total: {result.get('total_drafts_in_imap', 0)}")
            else:
                print(f"❌ IMAP drafts not accessible: {result.get('message')}")
            return result
        else:
            print(f"❌ Failed to test IMAP drafts: {response.status_code} - {response.text}")
            return {}
    
    def get_draft_detail(self, draft_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific draft."""
        response = self.session.get(f"{self.base_url}/emails/{draft_id}", params={"folder": "drafts"})
        print(f"Get draft detail response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved draft {draft_id} details")
            return result
        else:
            print(f"❌ Failed to get draft {draft_id} details: {response.status_code} - {response.text}")
            return {}
    
    def run_full_test(self):
        """Run a comprehensive test of the draft functionality."""
        print("=" * 60)
        print("EMAIL ENGINE DRAFT DEBUG TEST")
        print("=" * 60)
        
        # Step 1: Check current state
        print("\n1. Checking current drafts...")
        current_drafts = self.get_drafts()
        print(f"Current drafts: {json.dumps(current_drafts, indent=2)}")
        
        # Step 2: Test IMAP drafts connectivity
        print("\n2. Testing IMAP drafts connectivity...")
        imap_test = self.test_imap_drafts_connectivity()
        print(f"IMAP test result: {json.dumps(imap_test, indent=2)}")
        
        # Step 3: Get debug information
        print("\n3. Getting debug information...")
        debug_info = self.debug_all_emails()
        print(f"Debug info: {json.dumps(debug_info, indent=2)}")
        
        # Step 4: Create test draft
        print("\n4. Creating test draft...")
        new_draft = self.create_test_draft()
        
        # Step 5: Create draft with attachment
        print("\n5. Creating test draft with attachment...")
        new_draft_with_attachment = self.create_test_draft_with_attachment()
        
        # Step 6: Check drafts again
        print("\n6. Checking drafts after creation...")
        updated_drafts = self.get_drafts()
        print(f"Updated drafts: {json.dumps(updated_drafts, indent=2)}")
        
        # Step 7: Get detailed draft information
        print("\n7. Getting detailed draft information...")
        detailed_drafts = self.debug_drafts_detailed()
        print(f"Detailed drafts: {json.dumps(detailed_drafts, indent=2)}")
        
        # Step 8: Test specific draft retrieval
        if new_draft.get('id'):
            print(f"\n8. Getting details for draft {new_draft['id']}...")
            draft_detail = self.get_draft_detail(new_draft['id'])
            print(f"Draft detail: {json.dumps(draft_detail, indent=2)}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)


def main():
    debugger = EmailEngineDebugger()
    
    print("Email Engine Draft Debugger")
    print("=" * 40)
    print("Make sure your email engine is running on http://localhost:8000")
    print("You may need to set an authentication token if your API requires it.")
    
    # Ask for authentication token if needed
    token = input("\nEnter your auth token (press Enter if not needed): ").strip()
    if token:
        debugger.set_auth_token(token)
    
    print("\nChoose an option:")
    print("1. Run full test")
    print("2. Create simple test draft")
    print("3. Create test draft with attachment")
    print("4. Get current drafts")
    print("5. Get debug information")
    print("6. Get detailed draft information")
    print("7. Test IMAP drafts connectivity")
    
    choice = input("\nEnter your choice (1-7): ").strip()
    
    if choice == "1":
        debugger.run_full_test()
    elif choice == "2":
        debugger.create_test_draft()
    elif choice == "3":
        debugger.create_test_draft_with_attachment()
    elif choice == "4":
        result = debugger.get_drafts()
        print(f"Drafts: {json.dumps(result, indent=2)}")
    elif choice == "5":
        result = debugger.debug_all_emails()
        print(f"Debug info: {json.dumps(result, indent=2)}")
    elif choice == "6":
        result = debugger.debug_drafts_detailed()
        print(f"Detailed drafts: {json.dumps(result, indent=2)}")
    elif choice == "7":
        result = debugger.test_imap_drafts_connectivity()
        print(f"IMAP drafts test: {json.dumps(result, indent=2)}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()