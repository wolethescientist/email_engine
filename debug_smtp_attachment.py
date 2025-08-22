#!/usr/bin/env python3

import base64
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate

def test_smtp_attachment():
    # Create a simple PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    # Test different ways of adding attachments
    print("=== Testing different attachment methods ===")
    
    # Method 1: Current implementation
    print("\n1. Current implementation:")
    msg1 = EmailMessage()
    msg1["From"] = "test@example.com"
    msg1["To"] = "recipient@example.com"
    msg1["Subject"] = "Test PDF - Method 1"
    msg1["Date"] = formatdate(localtime=True)
    msg1.set_content("Test email with PDF attachment - Method 1")
    
    filename = "test.pdf"
    content_type = "application/pdf"
    maintype, subtype = (content_type.split("/", 1) if content_type and "/" in content_type else ("application", "octet-stream"))
    print(f"  MIME type: {maintype}/{subtype}")
    msg1.add_attachment(pdf_content, maintype=maintype, subtype=subtype, filename=filename)
    
    print(f"  Message parts: {len(list(msg1.walk()))}")
    for i, part in enumerate(msg1.walk()):
        print(f"    Part {i}: {part.get_content_type()}, filename: {part.get_filename()}")
    
    # Method 2: Using add_attachment with explicit disposition
    print("\n2. With explicit disposition:")
    msg2 = EmailMessage()
    msg2["From"] = "test@example.com"
    msg2["To"] = "recipient@example.com"
    msg2["Subject"] = "Test PDF - Method 2"
    msg2["Date"] = formatdate(localtime=True)
    msg2.set_content("Test email with PDF attachment - Method 2")
    
    msg2.add_attachment(pdf_content, 
                       maintype="application", 
                       subtype="pdf", 
                       filename=filename,
                       disposition="attachment")
    
    print(f"  Message parts: {len(list(msg2.walk()))}")
    for i, part in enumerate(msg2.walk()):
        print(f"    Part {i}: {part.get_content_type()}, filename: {part.get_filename()}")
        if part.get_filename():
            print(f"      Content-Disposition: {part.get('Content-Disposition')}")
            print(f"      Content-Transfer-Encoding: {part.get('Content-Transfer-Encoding')}")
    
    # Method 3: Manual attachment creation
    print("\n3. Manual attachment creation:")
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    
    msg3 = MIMEMultipart()
    msg3["From"] = "test@example.com"
    msg3["To"] = "recipient@example.com"
    msg3["Subject"] = "Test PDF - Method 3"
    msg3["Date"] = formatdate(localtime=True)
    
    # Add text part
    text_part = MIMEText("Test email with PDF attachment - Method 3")
    msg3.attach(text_part)
    
    # Add PDF attachment
    pdf_part = MIMEApplication(pdf_content, _subtype="pdf")
    pdf_part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg3.attach(pdf_part)
    
    print(f"  Message parts: {len(msg3.get_payload())}")
    for i, part in enumerate(msg3.walk()):
        print(f"    Part {i}: {part.get_content_type()}, filename: {part.get_filename()}")
        if part.get_filename():
            print(f"      Content-Disposition: {part.get('Content-Disposition')}")
            print(f"      Content-Transfer-Encoding: {part.get('Content-Transfer-Encoding')}")
    
    # Compare raw message sizes
    print(f"\nMessage sizes:")
    print(f"  Method 1: {len(msg1.as_bytes())} bytes")
    print(f"  Method 2: {len(msg2.as_bytes())} bytes")
    print(f"  Method 3: {len(msg3.as_bytes())} bytes")
    
    # Check if PDF content is present in each
    for i, msg in enumerate([msg1, msg2, msg3], 1):
        raw = msg.as_bytes()
        has_pdf = pdf_content[:20] in raw
        has_b64 = base64.b64encode(pdf_content)[:50] in raw
        print(f"  Method {i} - Raw PDF: {has_pdf}, Base64 PDF: {has_b64}")

if __name__ == "__main__":
    test_smtp_attachment()