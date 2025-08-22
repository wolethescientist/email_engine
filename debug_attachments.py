#!/usr/bin/env python3

import base64
from email.message import EmailMessage

# Test the attachment handling logic
def test_attachment_handling():
    # Create a simple PDF content (just for testing)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    # Encode as base64 (simulating what comes from the API)
    pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
    
    print(f"Original PDF size: {len(pdf_content)} bytes")
    print(f"Base64 encoded size: {len(pdf_base64)} characters")
    
    # Simulate the attachment processing from the API
    attachments_data = []
    filename = "test.pdf"
    content_type = "application/pdf"
    
    try:
        content = base64.b64decode(pdf_base64)
        print(f"Decoded content size: {len(content)} bytes")
        print(f"Content matches original: {content == pdf_content}")
        attachments_data.append((filename, content_type, content))
    except Exception as e:
        print(f"Base64 decode error: {e}")
        return
    
    # Test the email message creation (simulating send_email function)
    msg = EmailMessage()
    msg["From"] = "test@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "Test with PDF attachment"
    msg.set_content("This is a test email with PDF attachment")
    
    # Add attachment using the same logic as in send_email
    for filename, content_type, content in attachments_data:
        print(f"Adding attachment: {filename}, type: {content_type}, size: {len(content)} bytes")
        maintype, subtype = (content_type.split("/", 1) if content_type and "/" in content_type else ("application", "octet-stream"))
        print(f"Parsed MIME type: {maintype}/{subtype}")
        
        msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    
    # Check if attachment was added
    print(f"Message has {len(msg.get_payload())} parts")
    for i, part in enumerate(msg.walk()):
        print(f"Part {i}: {part.get_content_type()}")
        if part.get_filename():
            print(f"  Filename: {part.get_filename()}")
            print(f"  Content-Disposition: {part.get('Content-Disposition')}")
    
    # Get the raw message
    raw_message = msg.as_bytes()
    print(f"Raw message size: {len(raw_message)} bytes")
    
    # Check if PDF content is in the raw message
    if pdf_content[:20] in raw_message:
        print("✓ PDF content found in raw message")
    else:
        print("✗ PDF content NOT found in raw message")
        # Check if base64 encoded version is there
        if pdf_base64[:50].encode() in raw_message:
            print("✓ Base64 encoded PDF found in raw message")
        else:
            print("✗ Neither raw nor base64 PDF content found")

if __name__ == "__main__":
    test_attachment_handling()