#!/usr/bin/env python3

import requests
import base64
import json

# Test the attachment API with a small file
def test_attachment_api():
    # Create a small test file content
    test_content = b"This is a test PDF file content"
    test_base64 = base64.b64encode(test_content).decode('utf-8')
    
    # Prepare the request payload
    payload = {
        "subject": "Test Email with Attachment",
        "body": "This is a test email with a small attachment",
        "to": ["test@example.com"],
        "cc": [],
        "bcc": [],
        "attachments": [
            {
                "filename": "test.pdf",
                "content_base64": test_base64,
                "content_type": "application/pdf"
            }
        ]
    }
    
    print(f"Payload size: {len(json.dumps(payload))} characters")
    print(f"Attachment base64 size: {len(test_base64)} characters")
    print(f"Original content size: {len(test_content)} bytes")
    
    # Print the payload structure
    print("\nPayload structure:")
    print(f"- Subject: {payload['subject']}")
    print(f"- To: {payload['to']}")
    print(f"- Attachments count: {len(payload['attachments'])}")
    if payload['attachments']:
        att = payload['attachments'][0]
        print(f"  - Filename: {att['filename']}")
        print(f"  - Content type: {att['content_type']}")
        print(f"  - Base64 length: {len(att['content_base64'])}")
        print(f"  - Base64 preview: {att['content_base64'][:50]}...")

if __name__ == "__main__":
    test_attachment_api()