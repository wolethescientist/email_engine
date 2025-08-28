# Email Engine API Documentation

This comprehensive guide helps developers integrate email services into their web applications using the Email Engine API. The API provides full email management capabilities including sending, receiving, organizing, and real-time monitoring of emails.

## Base URL
```
http://localhost:8000
```

## Authentication

All endpoints (except `/connect`) require authentication. You can provide credentials in three ways:

### 1. Request Body (Recommended)
Include a `creds` object in your request body:
```json
{
  "creds": {
    "email": "user@example.com",
    "password": "your-password",
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "smtp_host": "smtp.gmail.com", 
    "smtp_port": 587
  }
}
```

### 2. Headers
```
X-Email: user@example.com
X-Password: your-password
X-IMAP-Host: imap.gmail.com
X-IMAP-Port: 993
X-SMTP-Host: smtp.gmail.com
X-SMTP-Port: 587
```

### 3. Query Parameters
```
?username=user@example.com&password=your-password&imap_host=imap.gmail.com&imap_port=993&smtp_host=smtp.gmail.com&smtp_port=587
```

## Integration Workflow

1. **Test Connection**: Use `/connect` to validate credentials
2. **Get Folders**: Retrieve available mailbox folders
3. **List Emails**: Fetch emails from specific folders
4. **Email Operations**: Send, delete, archive, mark as read
5. **Real-time Updates**: Use WebSocket for live notifications

---

## Connect Endpoint

### `POST /connect`

**Purpose**: Validates email server credentials before performing any email operations. This is the first endpoint you should call to ensure the user's email settings are correct.

**Use Case**: Call this when users add their email account to your application or when testing connection settings.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your-password",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Connection validated"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "IMAP validation failed: [AUTHENTICATIONFAILED] Authentication failed."
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

const validateConnection = async (credentials) => {
  try {
    const response = await axios.post('http://localhost:8000/connect', credentials, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('Connection successful:', response.data.message);
    return true;
  } catch (error) {
    if (error.response) {
      console.error('Connection failed:', error.response.data.detail);
    } else {
      console.error('Network error:', error.message);
    }
    return false;
  }
};

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

validateConnection(credentials);
```

---

## Emails Endpoints

### `POST /emails/folders`

**Purpose**: Retrieves all available mailbox folders. Essential for building navigation menus and folder selection interfaces.

**Use Case**: Call this after successful connection to populate your email client's folder list (Inbox, Sent, Drafts, etc.).

**Request Body:**
```json
{
  "creds": {
    "email": "user@example.com",
    "password": "your-password",
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587
  }
}
```

**Response (200 OK):**
```json
{
  "folders": [
    "INBOX",
    "Sent",
    "Drafts",
    "Trash",
    "Archive",
    "Spam"
  ]
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

const getFolders = async (creds) => {
  try {
    const response = await axios.post('http://localhost:8000/emails/folders', {
      creds: creds
    });
    
    const folders = response.data.folders;
    console.log('Available folders:', folders);
    return folders;
  } catch (error) {
    console.error('Error fetching folders:', error.response?.data?.detail || error.message);
    return [];
  }
};

// Usage
const creds = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

getFolders(creds).then(folders => {
  console.log('Folders loaded:', folders);
});
```

### `POST /emails/compose`

**Purpose**: Creates and saves a new email draft to the Drafts folder without sending it. Perfect for "Save Draft" functionality.

**Use Case**: When users want to save their work-in-progress emails to continue editing later.

**Request Body:**
```json
{
  "creds": { ... },
  "subject": "Project Update",
  "body": "<p>Hello team,</p><p>Here's the latest update...</p>",
  "to": ["team@company.com"],
  "cc": ["manager@company.com"],
  "bcc": ["archive@company.com"],
  "attachments": [
    {
      "filename": "report.pdf",
      "content_type": "application/pdf",
      "content_base64": "JVBERi0xLjQKJcfsj6IKNSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwo..."
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Draft saved to IMAP"
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

const saveDraft = async (emailData, credentials) => {
  const payload = {
    creds: credentials,
    ...emailData
  };
  
  try {
    const response = await axios.post('http://localhost:8000/emails/compose', payload);
    
    console.log('Draft saved successfully');
    return response.data;
  } catch (error) {
    console.error('Error saving draft:', error.response?.data?.detail || error.message);
    throw error;
  }
};

// Usage
const draftData = {
  subject: 'Meeting Notes',
  body: '<p>Today we discussed...</p>',
  to: ['colleague@company.com'],
  cc: ['boss@company.com']
};

const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

saveDraft(draftData, credentials)
  .then(result => console.log('Draft saved:', result))
  .catch(error => console.error('Failed to save draft:', error));
```

### `POST /emails/send`

**Purpose**: Sends an email immediately via SMTP and saves a copy to the Sent folder. Can send new emails or existing drafts.

**Use Case**: When users click "Send" button in your email composer or want to send a previously saved draft.

**Request Body:**
```json
{
  "creds": { ... },
  "subject": "Quarterly Report",
  "body": "<p>Please find the quarterly report attached.</p>",
  "to": ["client@company.com"],
  "cc": ["manager@company.com"],
  "bcc": ["archive@company.com"],
  "draft_id": 12345,
  "attachments": [
    {
      "filename": "Q3_Report.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "content_base64": "UEsDBBQAAAAIAA..."
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "id": null,
  "folder": "Sent",
  "subject": "Quarterly Report",
  "body": "<p>Please find the quarterly report attached.</p>",
  "from_address": "user@company.com",
  "to_addresses": ["client@company.com"],
  "cc_addresses": ["manager@company.com"],
  "bcc_addresses": ["archive@company.com"],
  "is_read": true,
  "attachments": [
    {
      "filename": "Q3_Report.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 15420
    }
  ]
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const sendEmail = async (creds, emailData, attachmentPath = null) => {
  const payload = {
    creds: creds,
    ...emailData
  };
  
  // Add attachment if provided
  if (attachmentPath) {
    try {
      const fileContent = fs.readFileSync(attachmentPath);
      const base64Content = fileContent.toString('base64');
      
      payload.attachments = [{
        filename: path.basename(attachmentPath),
        content_type: 'application/octet-stream',
        content_base64: base64Content
      }];
    } catch (error) {
      console.error('Error reading attachment:', error.message);
      throw error;
    }
  }
  
  try {
    const response = await axios.post('http://localhost:8000/emails/send', payload);
    
    console.log(`Email sent successfully to ${response.data.to_addresses}`);
    return response.data;
  } catch (error) {
    console.error('Error sending email:', error.response?.data?.detail || error.message);
    throw error;
  }
};

// Usage
const emailData = {
  subject: 'Project Update',
  body: '<p>The project is on track for completion.</p>',
  to: ['team@company.com'],
  cc: ['manager@company.com']
};

const creds = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

sendEmail(creds, emailData, './report.pdf')
  .then(result => console.log('Email sent:', result))
  .catch(error => console.error('Failed to send email:', error));
```

### `POST /emails/inbox`
### `POST /emails/sent` 
### `POST /emails/drafts`
### `POST /emails/trash`
### `POST /emails/archive`
### `POST /emails/spam`

**Purpose**: Retrieves a paginated list of emails from specific folders. Each endpoint corresponds to a different mailbox folder.

**Use Case**: Display email lists in your application's folder views with pagination support for performance.

**Request Body:**
```json
{
  "creds": { ... },
  "page": 1,
  "size": 25
}
```

**Response (200 OK):**
```json
{
  "page": 1,
  "size": 25,
  "total": 147,
  "items": [
    {
      "id": 1001,
      "subject": "Weekly Team Meeting",
      "from_address": "manager@company.com",
      "to_addresses": ["team@company.com"],
      "is_read": false,
      "timestamp": "2024-01-15T14:30:00Z",
      "has_attachments": true
    },
    {
      "id": 1000,
      "subject": "Project Deadline Reminder",
      "from_address": "pm@company.com",
      "to_addresses": ["dev-team@company.com"],
      "is_read": true,
      "timestamp": "2024-01-15T09:15:00Z",
      "has_attachments": false
    }
  ]
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

class EmailListManager {
  constructor(credentials) {
    this.credentials = credentials;
    this.emails = [];
    this.pagination = { page: 1, size: 25, total: 0 };
  }

  async fetchEmails(folder, page = 1) {
    try {
      const response = await axios.post(`http://localhost:8000/emails/${folder}`, {
        creds: this.credentials,
        page: page,
        size: this.pagination.size
      });
      
      this.emails = response.data.items;
      this.pagination = {
        page: response.data.page,
        size: response.data.size,
        total: response.data.total
      };
      
      console.log(`Loaded ${this.emails.length} emails from ${folder}`);
      return this.emails;
    } catch (error) {
      console.error('Failed to fetch emails:', error.response?.data?.detail || error.message);
      throw error;
    }
  }

  displayEmails() {
    console.log('\n=== EMAIL LIST ===');
    this.emails.forEach(email => {
      const status = email.is_read ? '✓' : '●';
      const attachment = email.has_attachments ? '📎' : '';
      console.log(`${status} [${email.id}] ${email.subject} ${attachment}`);
      console.log(`    From: ${email.from_address}`);
      console.log(`    Date: ${new Date(email.timestamp).toLocaleString()}`);
      console.log('');
    });
    
    const totalPages = Math.ceil(this.pagination.total / this.pagination.size);
    console.log(`Page ${this.pagination.page} of ${totalPages} (${this.pagination.total} total emails)`);
  }

  async nextPage(folder) {
    const totalPages = Math.ceil(this.pagination.total / this.pagination.size);
    if (this.pagination.page < totalPages) {
      return await this.fetchEmails(folder, this.pagination.page + 1);
    }
    console.log('Already on last page');
    return this.emails;
  }

  async previousPage(folder) {
    if (this.pagination.page > 1) {
      return await this.fetchEmails(folder, this.pagination.page - 1);
    }
    console.log('Already on first page');
    return this.emails;
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const emailManager = new EmailListManager(credentials);

// Fetch and display inbox emails
emailManager.fetchEmails('inbox')
  .then(() => {
    emailManager.displayEmails();
  })
  .catch(error => {
    console.error('Error:', error.message);
  });
```

### `POST /emails/{email_id}`

**Purpose**: Retrieves complete email details including body content, headers, and attachment information. Essential for email viewer functionality.

**Use Case**: When users click on an email from the list to read its full content, view attachments, or reply/forward.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "inbox"
}
```

**Response (200 OK):**
```json
{
  "id": 1001,
  "folder": "inbox",
  "subject": "Q4 Budget Planning",
  "body": "<p>Dear Team,</p><p>Please review the attached budget proposal for Q4...</p>",
  "from_address": "finance@company.com",
  "to_addresses": ["team@company.com"],
  "cc_addresses": ["manager@company.com"],
  "bcc_addresses": [],
  "is_read": false,
  "timestamp": "2024-01-15T14:30:00Z",
  "attachments": [
    {
      "filename": "Q4_Budget_Proposal.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 45678
    },
    {
      "filename": "Guidelines.pdf",
      "content_type": "application/pdf",
      "size": 123456
    }
  ]
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

class EmailViewer {
  constructor(credentials) {
    this.credentials = credentials;
    this.email = null;
    this.loading = false;
    this.error = null;
  }

  async fetchEmail(emailId, folder) {
    this.loading = true;
    this.error = null;
    
    try {
      const response = await axios.post(`http://localhost:8000/emails/${emailId}`, {
        creds: this.credentials,
        folder: folder
      });
      
      this.email = response.data;
      console.log(`Email loaded: ${this.email.subject}`);
      
      // Mark as read if it wasn't already
      if (!this.email.is_read) {
        await this.markAsRead(emailId, folder);
      }
      
      return this.email;
    } catch (error) {
      this.error = error.response?.data?.detail || error.message;
      console.error('Failed to load email:', this.error);
      throw error;
    } finally {
      this.loading = false;
    }
  }
  
  async markAsRead(emailId, folder) {
    try {
      await axios.post(`http://localhost:8000/emails/${emailId}/read`, {
        creds: this.credentials,
        folder: folder,
        read: true
      });
      console.log(`Email ${emailId} marked as read`);
    } catch (error) {
      console.error('Failed to mark email as read:', error.response?.data?.detail || error.message);
    }
  }

  displayEmail() {
    if (this.loading) {
      console.log('Loading email...');
      return;
    }
    
    if (this.error) {
      console.log(`Error: ${this.error}`);
      return;
    }
    
    if (!this.email) {
      console.log('No email loaded');
      return;
    }

    console.log('\n=== EMAIL DETAILS ===');
    console.log(`Subject: ${this.email.subject}`);
    console.log(`From: ${this.email.from_address}`);
    console.log(`To: ${this.email.to_addresses.join(', ')}`);
    if (this.email.cc_addresses.length) {
      console.log(`CC: ${this.email.cc_addresses.join(', ')}`);
    }
    console.log(`Date: ${new Date(this.email.timestamp).toLocaleString()}`);
    console.log(`Read: ${this.email.is_read ? 'Yes' : 'No'}`);
    console.log('\n--- Body ---');
    console.log(this.email.body.replace(/<[^>]*>/g, '')); // Strip HTML tags for console
    
    if (this.email.attachments.length) {
      console.log('\n--- Attachments ---');
      this.email.attachments.forEach(attachment => {
        const sizeKB = Math.round(attachment.size / 1024);
        console.log(`📎 ${attachment.filename} (${sizeKB} KB)`);
      });
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const emailViewer = new EmailViewer(credentials);

// Fetch and display a specific email
emailViewer.fetchEmail(1001, 'inbox')
  .then(() => {
    emailViewer.displayEmail();
  })
  .catch(error => {
    console.error('Error viewing email:', error.message);
  });
```

### `POST /emails/{email_id}/delete`

**Purpose**: Moves an email to the Trash folder (soft delete). The email can be recovered from Trash until permanently deleted.

**Use Case**: When users click the delete button on an email. Provides a safety net by moving to trash instead of permanent deletion.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "inbox"
}
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');
const readline = require('readline');

class EmailManager {
  constructor(credentials) {
    this.credentials = credentials;
  }

  async deleteEmail(emailId, currentFolder, confirmDelete = true) {
    if (confirmDelete) {
      const confirmed = await this.confirmAction(`Are you sure you want to delete email ${emailId}?`);
      if (!confirmed) {
        console.log('Delete operation cancelled');
        return false;
      }
    }
    
    try {
      const response = await axios.post(`http://localhost:8000/emails/${emailId}/delete`, {
        creds: this.credentials,
        folder: currentFolder
      });
      
      console.log('Email moved to trash successfully');
      return true;
    } catch (error) {
      console.error('Error deleting email:', error.response?.data?.detail || error.message);
      return false;
    }
  }

  async deleteMultipleEmails(emailIds, currentFolder) {
    console.log(`Deleting ${emailIds.length} emails...`);
    const results = [];
    
    for (const emailId of emailIds) {
      try {
        const success = await this.deleteEmail(emailId, currentFolder, false); // Skip individual confirmations
        results.push({ emailId, success });
        
        if (success) {
          console.log(`✓ Email ${emailId} deleted`);
        } else {
          console.log(`✗ Failed to delete email ${emailId}`);
        }
      } catch (error) {
        results.push({ emailId, success: false, error: error.message });
        console.log(`✗ Error deleting email ${emailId}: ${error.message}`);
      }
    }
    
    const successCount = results.filter(r => r.success).length;
    console.log(`\nDeleted ${successCount} of ${emailIds.length} emails`);
    
    return results;
  }

  async confirmAction(message) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    return new Promise((resolve) => {
      rl.question(`${message} (y/N): `, (answer) => {
        rl.close();
        resolve(answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes');
      });
    });
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const emailManager = new EmailManager(credentials);

// Delete a single email
emailManager.deleteEmail(1001, 'inbox')
  .then(success => {
    if (success) {
      console.log('Email deleted successfully');
    }
  });

// Delete multiple emails
const emailIds = [1002, 1003, 1004];
emailManager.deleteMultipleEmails(emailIds, 'inbox')
  .then(results => {
    console.log('Bulk delete completed:', results);
  });
```

### `POST /emails/{email_id}/archive`

**Purpose**: Moves an email from its current folder to the Archive folder. Helps users organize emails without deleting them.

**Use Case**: When users want to clean up their inbox by archiving emails they want to keep but don't need immediate access to.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "inbox"
}
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Code Example (Python with Flask):**
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/archive-email', methods=['POST'])
def archive_email():
    data = request.json
    email_id = data.get('email_id')
    current_folder = data.get('current_folder', 'inbox')
    credentials = data.get('credentials')
    
    if not all([email_id, credentials]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Archive the email
        response = requests.post(
            f'http://localhost:8000/emails/{email_id}/archive',
            json={
                'creds': credentials,
                'folder': current_folder
            }
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Email {email_id} archived successfully'
            })
        else:
            error_data = response.json()
            return jsonify({
                'success': False,
                'error': error_data.get('detail', 'Archive failed')
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Network error: {str(e)}'
        }), 500

# Batch archive function
@app.route('/api/archive-emails-batch', methods=['POST'])
def archive_emails_batch():
    data = request.json
    email_ids = data.get('email_ids', [])
    current_folder = data.get('current_folder', 'inbox')
    credentials = data.get('credentials')
    
    results = []
    
    for email_id in email_ids:
        try:
            response = requests.post(
                f'http://localhost:8000/emails/{email_id}/archive',
                json={
                    'creds': credentials,
                    'folder': current_folder
                }
            )
            
            results.append({
                'email_id': email_id,
                'success': response.status_code == 200,
                'error': None if response.status_code == 200 else response.json().get('detail')
            })
            
        except Exception as e:
            results.append({
                'email_id': email_id,
                'success': False,
                'error': str(e)
            })
    
    success_count = sum(1 for r in results if r['success'])
    
    return jsonify({
        'total': len(email_ids),
        'success_count': success_count,
        'results': results
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### `POST /emails/{email_id}/unarchive`

**Purpose**: Moves an email from the Archive folder back to the Inbox. Useful for restoring archived emails that need attention.

**Use Case**: When users need to bring back an archived email to their inbox for follow-up or action.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "archive"
}
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

class EmailArchiveManager {
  constructor(credentials) {
    this.credentials = credentials;
    this.baseUrl = 'http://localhost:8000';
  }
  
  async unarchiveEmail(emailId) {
    try {
      const response = await axios.post(`${this.baseUrl}/emails/${emailId}/unarchive`, {
        creds: this.credentials,
        folder: 'archive'
      });
      
      console.log('Email unarchived successfully');
      return {
        success: true,
        message: 'Email unarchived successfully'
      };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      console.error('Unarchive failed:', errorMessage);
      return {
        success: false,
        error: errorMessage
      };
    }
  }
  
  async bulkUnarchive(emailIds) {
    console.log(`Unarchiving ${emailIds.length} emails...`);
    const results = [];
    
    for (const emailId of emailIds) {
      const result = await this.unarchiveEmail(emailId);
      results.push({ ...result, email_id: emailId });
      
      if (result.success) {
        console.log(`✓ Email ${emailId} unarchived`);
      } else {
        console.log(`✗ Failed to unarchive email ${emailId}: ${result.error}`);
      }
    }
    
    const successCount = results.filter(r => r.success).length;
    console.log(`\nUnarchived ${successCount} of ${emailIds.length} emails`);
    
    return results;
  }
}

// Usage
const credentials = {
  email: 'user@company.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const archiveManager = new EmailArchiveManager(credentials);

// Unarchive a single email
archiveManager.unarchiveEmail(1001)
  .then(result => {
    if (result.success) {
      console.log('Email unarchived successfully!');
    } else {
      console.log('Error:', result.error);
    }
  });

// Bulk unarchive
const emailIds = [1002, 1003, 1004];
archiveManager.bulkUnarchive(emailIds)
  .then(results => {
    console.log('Bulk unarchive completed:', results);
  });
```

### `POST /emails/{email_id}/read`

**Purpose**: Updates the read status of an email. Essential for tracking which emails have been viewed by the user.

**Use Case**: Automatically mark emails as read when opened, or allow users to manually mark emails as read/unread for organization.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "inbox",
  "read": true
}
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Code Example (Node.js):**
```javascript
const axios = require('axios');

class EmailReadManager {
  constructor(credentials) {
    this.credentials = credentials;
    this.baseUrl = 'http://localhost:8000';
  }
  
  async markEmailAsRead(emailId, folder, isRead = true) {
    try {
      const response = await axios.post(`${this.baseUrl}/emails/${emailId}/read`, {
        creds: this.credentials,
        folder: folder,
        read: isRead
      });
      
      console.log(`Email ${emailId} marked as ${isRead ? 'read' : 'unread'} successfully`);
      return true;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      console.error(`Error marking email as ${isRead ? 'read' : 'unread'}:`, errorMessage);
      return false;
    }
  }
  
  async bulkMarkAsRead(emailIds, folder) {
    console.log(`Marking ${emailIds.length} emails as read...`);
    let successCount = 0;
    
    for (const emailId of emailIds) {
      const success = await this.markEmailAsRead(emailId, folder, true);
      if (success) {
        successCount++;
        console.log(`✓ Email ${emailId} marked as read`);
      } else {
        console.log(`✗ Failed to mark email ${emailId} as read`);
      }
    }
    
    console.log(`\nMarked ${successCount} of ${emailIds.length} emails as read`);
    return successCount;
  }
  
  async bulkMarkAsUnread(emailIds, folder) {
    console.log(`Marking ${emailIds.length} emails as unread...`);
    let successCount = 0;
    
    for (const emailId of emailIds) {
      const success = await this.markEmailAsRead(emailId, folder, false);
      if (success) {
        successCount++;
        console.log(`✓ Email ${emailId} marked as unread`);
      } else {
        console.log(`✗ Failed to mark email ${emailId} as unread`);
      }
    }
    
    console.log(`\nMarked ${successCount} of ${emailIds.length} emails as unread`);
    return successCount;
  }
}

// Usage
const credentials = {
  email: 'user@company.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const readManager = new EmailReadManager(credentials);

// Mark single email as read
readManager.markEmailAsRead(1001, 'inbox')
  .then(success => {
    if (success) {
      console.log('Email marked as read successfully');
    }
  });

// Mark multiple emails as read
const emailIds = [1002, 1003, 1004];
readManager.bulkMarkAsRead(emailIds, 'inbox')
  .then(successCount => {
    console.log(`Successfully marked ${successCount} emails as read`);
  });

// Mark emails as unread
readManager.bulkMarkAsUnread([1005, 1006], 'inbox')
  .then(successCount => {
    console.log(`Successfully marked ${successCount} emails as unread`);
  });
```

### `POST /emails/{email_id}/attachments/{filename}`

**Purpose**: Downloads a specific attachment from an email. Returns the raw file content with appropriate headers for browser download.

**Use Case**: When users click on an attachment link to download files attached to emails.

**Request Body:**
```json
{
  "creds": { ... },
  "folder": "inbox"
}
```

**Response (200 OK):**
The response contains the raw file content with headers:
- `Content-Type`: The MIME type of the file
- `Content-Disposition`: attachment; filename="filename.ext"
- `Content-Length`: Size of the file in bytes

**Code Example (Node.js):**
```javascript
const axios = require('axios');
const fs = require('fs');
const path = require('path');

class AttachmentManager {
  constructor(credentials) {
    this.credentials = credentials;
    this.baseUrl = 'http://localhost:8000';
  }

  async downloadAttachment(emailId, filename, folder = 'inbox', savePath = './downloads') {
    try {
      const response = await axios.post(
        `${this.baseUrl}/emails/${emailId}/attachments/${filename}`,
        {
          creds: this.credentials,
          folder: folder
        },
        {
          responseType: 'stream'
        }
      );
      
      // Ensure download directory exists
      if (!fs.existsSync(savePath)) {
        fs.mkdirSync(savePath, { recursive: true });
      }
      
      const fullPath = path.join(savePath, filename);
      const writer = fs.createWriteStream(fullPath);
      
      response.data.pipe(writer);
      
      return new Promise((resolve, reject) => {
        writer.on('finish', () => {
          console.log(`Attachment downloaded successfully: ${fullPath}`);
          resolve({
            success: true,
            message: 'Attachment downloaded successfully',
            path: fullPath,
            size: fs.statSync(fullPath).size
          });
        });
        
        writer.on('error', (error) => {
          console.error('Error writing file:', error.message);
          reject({
            success: false,
            error: 'Failed to save attachment',
            details: error.message
          });
        });
      });
      
    } catch (error) {
      console.error('Error downloading attachment:', error.message);
      throw {
        success: false,
        error: 'Failed to download attachment',
        details: error.response?.data || error.message
      };
    }
  }

  async downloadAllAttachments(emailId, folder = 'inbox', savePath = './downloads') {
    try {
      // First get email details to see attachments
      const emailResponse = await axios.post(`${this.baseUrl}/emails/${emailId}`, {
        creds: this.credentials,
        folder: folder
      });
      
      const email = emailResponse.data;
      
      if (!email.attachments || email.attachments.length === 0) {
        console.log('No attachments found in this email');
        return [];
      }
      
      console.log(`Downloading ${email.attachments.length} attachments...`);
      const results = [];
      
      for (const attachment of email.attachments) {
        try {
          const result = await this.downloadAttachment(emailId, attachment.filename, folder, savePath);
          results.push({ filename: attachment.filename, ...result });
          console.log(`✓ Downloaded: ${attachment.filename}`);
        } catch (error) {
          results.push({ filename: attachment.filename, ...error });
          console.log(`✗ Failed to download: ${attachment.filename}`);
        }
      }
      
      const successCount = results.filter(r => r.success).length;
      console.log(`\nDownloaded ${successCount} of ${email.attachments.length} attachments`);
      
      return results;
    } catch (error) {
      console.error('Error downloading attachments:', error.message);
      throw error;
    }
  }

  async getAttachmentInfo(emailId, folder = 'inbox') {
    try {
      const response = await axios.post(`${this.baseUrl}/emails/${emailId}`, {
        creds: this.credentials,
        folder: folder
      });
      
      const attachments = response.data.attachments || [];
      
      console.log(`\n=== ATTACHMENTS (${attachments.length}) ===`);
      attachments.forEach((attachment, index) => {
        const sizeKB = Math.round(attachment.size / 1024);
        console.log(`${index + 1}. ${attachment.filename} (${sizeKB} KB) - ${attachment.content_type}`);
      });
      
      return attachments;
    } catch (error) {
      console.error('Error getting attachment info:', error.response?.data?.detail || error.message);
      throw error;
    }
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const attachmentManager = new AttachmentManager(credentials);

// Download a specific attachment
attachmentManager.downloadAttachment(1001, 'report.pdf', 'inbox', './downloads')
  .then(result => {
    console.log('Download result:', result);
  })
  .catch(error => {
    console.error('Download failed:', error);
  });

// Download all attachments from an email
attachmentManager.downloadAllAttachments(1001, 'inbox', './downloads')
  .then(results => {
    console.log('All downloads completed:', results);
  });

// Get attachment information
attachmentManager.getAttachmentInfo(1001, 'inbox')
  .then(attachments => {
    console.log('Attachment info retrieved');
  });
```

---

## WebSocket Endpoint

### `WS /ws/idle`

**Purpose**: Establishes a WebSocket connection to monitor the mailbox for new emails in real-time using the IMAP IDLE command. This provides instant notifications when new emails arrive without polling.

**Use Case**: Perfect for building real-time email clients that need to notify users immediately when new emails arrive, similar to Gmail or Outlook's push notifications.

**Connection URL:**
```
ws://localhost:8000/ws/idle
```

**Authentication:**
Provide credentials via headers or query parameters as described in the Authentication section above.

**Server Messages:**

When a new email arrives, the server sends a JSON message:
```json
{
  "event": "new_mail"
}
```

When an error occurs, the server sends:
```json
{
  "error": "An IDLE error occurred: [error details]"
}
```

**Connection Lifecycle:**
1. Client connects to WebSocket endpoint with authentication
2. Server establishes IMAP IDLE connection to monitor INBOX
3. Server sends notifications when new emails arrive
4. Connection automatically refreshes every 15 minutes to maintain stability
5. Connection closes gracefully when client disconnects

**Code Example (JavaScript):**
```javascript
class EmailNotificationService {
  constructor(credentials) {
    this.credentials = credentials;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
  }

  connect() {
    // Build WebSocket URL with authentication
    const params = new URLSearchParams({
      username: this.credentials.email,
      password: this.credentials.password,
      imap_host: this.credentials.imap_host,
      imap_port: this.credentials.imap_port,
      smtp_host: this.credentials.smtp_host,
      smtp_port: this.credentials.smtp_port
    });

    const wsUrl = `ws://localhost:8000/ws/idle?${params.toString()}`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('Connected to email notification service');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.onConnectionOpen();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.onConnectionClose();
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.onConnectionError(error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  handleMessage(data) {
    if (data.event === 'new_mail') {
      console.log('New email received!');
      this.onNewEmail();
    } else if (data.error) {
      console.error('Server error:', data.error);
      this.onServerError(data.error);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.onMaxReconnectAttemptsReached();
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${this.reconnectDelay}ms`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // Event handlers - override these in your implementation
  onConnectionOpen() {
    // Show connection status to user
    this.showNotification('Connected to email service', 'success');
  }

  onConnectionClose() {
    // Show disconnection status
    this.showNotification('Disconnected from email service', 'warning');
  }

  onConnectionError(error) {
    // Handle connection errors
    this.showNotification('Email service connection error', 'error');
  }

  onNewEmail() {
    // Handle new email notification
    this.showNotification('New email received!', 'info');
    this.playNotificationSound();
    this.refreshEmailList();
  }

  onServerError(error) {
    // Handle server-side errors
    this.showNotification(`Email service error: ${error}`, 'error');
  }

  onMaxReconnectAttemptsReached() {
    // Handle failed reconnection
    this.showNotification('Unable to connect to email service. Please check your connection.', 'error');
  }

  showNotification(message, type) {
    // Implement your notification system here
    console.log(`[${type.toUpperCase()}] ${message}`);
  }

  playNotificationSound() {
    // Play notification sound
    const audio = new Audio('/notification-sound.mp3');
    audio.play().catch(e => console.log('Could not play notification sound:', e));
  }

  refreshEmailList() {
    // Trigger email list refresh in your application
    window.dispatchEvent(new CustomEvent('newEmailReceived'));
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const emailNotifications = new EmailNotificationService(credentials);
emailNotifications.connect();

// Listen for new email events in your app
window.addEventListener('newEmailReceived', () => {
  // Refresh your email list UI
  fetchEmails('inbox');
});
```

**Code Example (React Hook):**
```javascript
import { useState, useEffect, useCallback } from 'react';

const useEmailNotifications = (credentials) => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [newEmailCount, setNewEmailCount] = useState(0);

  const connect = useCallback(() => {
    if (!credentials) return;

    const params = new URLSearchParams({
      username: credentials.email,
      password: credentials.password,
      imap_host: credentials.imap_host,
      imap_port: credentials.imap_port,
      smtp_host: credentials.smtp_host,
      smtp_port: credentials.smtp_port
    });

    const ws = new WebSocket(`ws://localhost:8000/ws/idle?${params.toString()}`);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.event === 'new_mail') {
        setNewEmailCount(prev => prev + 1);
      } else if (data.error) {
        setError(data.error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      setError('Connection error');
      setIsConnected(false);
    };

    return ws;
  }, [credentials]);

  useEffect(() => {
    const ws = connect();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connect]);

  const resetNewEmailCount = () => {
    setNewEmailCount(0);
  };

  return {
    isConnected,
    error,
    newEmailCount,
    resetNewEmailCount
  };
};

// Usage in component
const EmailApp = () => {
  const { isConnected, error, newEmailCount, resetNewEmailCount } = useEmailNotifications(credentials);

  return (
    <div>
      <div className="status-bar">
        {isConnected ? (
          <span className="connected">✅ Connected</span>
        ) : (
          <span className="disconnected">❌ Disconnected</span>
        )}
        {error && <span className="error">Error: {error}</span>}
      </div>
      
      {newEmailCount > 0 && (
        <div className="notification">
          {newEmailCount} new email{newEmailCount > 1 ? 's' : ''} received!
          <button onClick={resetNewEmailCount}>Clear</button>
        </div>
      )}
    </div>
  );
};
```

---

## Error Handling & Troubleshooting

### Common Error Responses

**Authentication Errors:**
```json
{
  "detail": "IMAP validation failed: [AUTHENTICATIONFAILED] Authentication failed."
}
```
**Solution**: Verify email credentials, ensure IMAP is enabled, check for 2FA requirements.

**Connection Errors:**
```json
{
  "detail": "IMAP connection failed: [Errno 111] Connection refused"
}
```
**Solution**: Check IMAP host and port settings, verify network connectivity.

**Folder Not Found:**
```json
{
  "detail": "Folder 'NonExistentFolder' not found"
}
```
**Solution**: Use `/emails/folders` endpoint to get available folder names.

**Email Not Found:**
```json
{
  "detail": "Email with ID 99999 not found in folder 'inbox'"
}
```
**Solution**: Verify email ID exists in the specified folder.

### Best Practices

**1. Credential Management:**
```javascript
// Store credentials securely
const credentialsManager = {
  store: (credentials) => {
    // Use secure storage (not localStorage for production)
    sessionStorage.setItem('email_creds', JSON.stringify(credentials));
  },
  
  retrieve: () => {
    const stored = sessionStorage.getItem('email_creds');
    return stored ? JSON.parse(stored) : null;
  },
  
  clear: () => {
    sessionStorage.removeItem('email_creds');
  }
};
```

**2. Error Handling Wrapper:**
```javascript
const apiCall = async (endpoint, data) => {
  try {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};
```

**3. Rate Limiting:**
```javascript
class RateLimiter {
  constructor(maxRequests = 10, windowMs = 60000) {
    this.requests = [];
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }
  
  canMakeRequest() {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.windowMs);
    return this.requests.length < this.maxRequests;
  }
  
  recordRequest() {
    this.requests.push(Date.now());
  }
}
```

---

## Integration Examples

### Node.js Email Client

```javascript
const axios = require('axios');
const readline = require('readline');

class EmailClient {
  constructor(credentials) {
    this.baseUrl = 'http://localhost:8000';
    this.credentials = credentials;
    this.folders = [];
    this.emails = [];
    this.selectedFolder = 'inbox';
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  async request(endpoint, data = {}) {
    try {
      const response = await axios.post(`${this.baseUrl}${endpoint}`, {
        creds: this.credentials,
        ...data
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  async getFolders() {
    return this.request('/emails/folders');
  }

  async getEmails(folder, page = 1, size = 25) {
    return this.request(`/emails/${folder}`, { page, size });
  }

  async sendEmail(emailData) {
    return this.request('/emails/send', emailData);
  }

  async loadFolders() {
    try {
      const response = await this.getFolders();
      this.folders = response.folders;
      console.log('Available folders:', this.folders.join(', '));
    } catch (error) {
      console.error('Failed to load folders:', error.message);
    }
  }

  async loadEmails() {
    try {
      const response = await this.getEmails(this.selectedFolder);
      this.emails = response.items;
      console.log(`\nLoaded ${this.emails.length} emails from ${this.selectedFolder}`);
      this.displayEmails();
    } catch (error) {
      console.error('Failed to load emails:', error.message);
    }
  }

  displayEmails() {
    console.log(`\n=== ${this.selectedFolder.toUpperCase()} EMAILS ===`);
    this.emails.forEach((email, index) => {
      const status = email.is_read ? '✓' : '●';
      const attachment = email.has_attachments ? '📎' : '';
      console.log(`${index + 1}. ${status} [${email.id}] ${email.subject} ${attachment}`);
      console.log(`    From: ${email.from_address}`);
      console.log(`    Date: ${new Date(email.timestamp).toLocaleString()}`);
      console.log('');
    });
  }

  async selectFolder(folder) {
    if (this.folders.includes(folder)) {
      this.selectedFolder = folder;
      await this.loadEmails();
    } else {
      console.log('Invalid folder. Available folders:', this.folders.join(', '));
    }
  }

  async showMenu() {
    console.log('\n=== EMAIL CLIENT MENU ===');
    console.log('1. List folders');
    console.log('2. Select folder');
    console.log('3. Refresh emails');
    console.log('4. View email');
    console.log('5. Send email');
    console.log('6. Exit');
    
    return new Promise((resolve) => {
      this.rl.question('Choose an option (1-6): ', (answer) => {
        resolve(answer.trim());
      });
    });
  }

  async run() {
    console.log('Starting Email Client...');
    await this.loadFolders();
    await this.loadEmails();

    while (true) {
      const choice = await this.showMenu();
      
      switch (choice) {
        case '1':
          console.log('Available folders:', this.folders.join(', '));
          break;
        case '2':
          const folder = await this.askQuestion('Enter folder name: ');
          await this.selectFolder(folder);
          break;
        case '3':
          await this.loadEmails();
          break;
        case '4':
          const emailIndex = await this.askQuestion('Enter email number: ');
          await this.viewEmail(parseInt(emailIndex) - 1);
          break;
        case '5':
          await this.composeEmail();
          break;
        case '6':
          console.log('Goodbye!');
          this.rl.close();
          return;
        default:
          console.log('Invalid option');
      }
    }
  }

  async askQuestion(question) {
    return new Promise((resolve) => {
      this.rl.question(question, (answer) => {
        resolve(answer.trim());
      });
    });
  }

  async viewEmail(index) {
    if (index >= 0 && index < this.emails.length) {
      const email = this.emails[index];
      try {
        const fullEmail = await this.request(`/emails/${email.id}`, {
          folder: this.selectedFolder
        });
        
        console.log('\n=== EMAIL DETAILS ===');
        console.log(`Subject: ${fullEmail.subject}`);
        console.log(`From: ${fullEmail.from_address}`);
        console.log(`To: ${fullEmail.to_addresses.join(', ')}`);
        console.log(`Date: ${new Date(fullEmail.timestamp).toLocaleString()}`);
        console.log('\n--- Body ---');
        console.log(fullEmail.body.replace(/<[^>]*>/g, ''));
        
        if (fullEmail.attachments.length > 0) {
          console.log('\n--- Attachments ---');
          fullEmail.attachments.forEach(att => {
            console.log(`📎 ${att.filename} (${Math.round(att.size/1024)} KB)`);
          });
        }
      } catch (error) {
        console.error('Failed to load email details:', error.message);
      }
    } else {
      console.log('Invalid email number');
    }
  }

  async composeEmail() {
    const to = await this.askQuestion('To: ');
    const subject = await this.askQuestion('Subject: ');
    const body = await this.askQuestion('Body: ');
    
    try {
      await this.sendEmail({
        to: [to],
        subject: subject,
        body: body
      });
      console.log('Email sent successfully!');
    } catch (error) {
      console.error('Failed to send email:', error.message);
    }
  }
}

// Usage
const credentials = {
  email: 'user@gmail.com',
  password: 'app-password',
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587
};

const emailClient = new EmailClient(credentials);
emailClient.run().catch(error => {
  console.error('Email client error:', error.message);
});
```

### Node.js Email Dashboard Server

```javascript
const express = require('express');
const axios = require('axios');
const path = require('path');

class EmailDashboardServer {
  constructor(port = 3000) {
    this.app = express();
    this.port = port;
    this.baseUrl = 'http://localhost:8000';
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use(express.static('public'));
  }

  setupRoutes() {
    // API Routes
    this.app.post('/api/folders', this.getFolders.bind(this));
    this.app.post('/api/emails/:folder', this.getEmails.bind(this));
    this.app.post('/api/email/:id', this.getEmail.bind(this));
    this.app.post('/api/send', this.sendEmail.bind(this));
    this.app.post('/api/delete/:id', this.deleteEmail.bind(this));
    this.app.post('/api/archive/:id', this.archiveEmail.bind(this));
    
    // Dashboard route
    this.app.get('/', (req, res) => {
      res.send(this.getDashboardHTML());
    });
  }

  async apiCall(endpoint, data) {
    try {
      const response = await axios.post(`${this.baseUrl}${endpoint}`, data);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || error.message);
    }
  }

  async getFolders(req, res) {
    try {
      const result = await this.apiCall('/emails/folders', req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async getEmails(req, res) {
    try {
      const { folder } = req.params;
      const result = await this.apiCall(`/emails/${folder}`, req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async getEmail(req, res) {
    try {
      const { id } = req.params;
      const result = await this.apiCall(`/emails/${id}`, req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async sendEmail(req, res) {
    try {
      const result = await this.apiCall('/emails/send', req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async deleteEmail(req, res) {
    try {
      const { id } = req.params;
      const result = await this.apiCall(`/emails/${id}/delete`, req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  async archiveEmail(req, res) {
    try {
      const { id } = req.params;
      const result = await this.apiCall(`/emails/${id}/archive`, req.body);
      res.json(result);
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  }

  getDashboardHTML() {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .dashboard { display: flex; gap: 20px; }
            .sidebar { width: 200px; }
            .main-content { flex: 1; }
            .folder-btn { display: block; width: 100%; margin: 5px 0; padding: 10px; }
            .folder-btn.active { background: #007cba; color: white; }
            .email-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; }
            .email-item.unread { font-weight: bold; background: #f0f8ff; }
            .loading { text-align: center; padding: 20px; }
            .error { color: red; padding: 10px; background: #ffe6e6; }
        </style>
    </head>
    <body>
        <h1>Email Dashboard</h1>
        <div class="dashboard">
            <div class="sidebar">
                <h3>Folders</h3>
                <div id="folders"></div>
            </div>
            <div class="main-content">
                <div id="loading" class="loading" style="display: none;">Loading...</div>
                <div id="error" class="error" style="display: none;"></div>
                <div id="emails"></div>
            </div>
        </div>
        
        <script>
            const credentials = {
                email: 'user@gmail.com',
                password: 'app-password',
                imap_host: 'imap.gmail.com',
                imap_port: 993,
                smtp_host: 'smtp.gmail.com',
                smtp_port: 587
            };
            
            let selectedFolder = 'inbox';
            
            async function apiCall(endpoint, data = {}) {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ creds: credentials, ...data })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'API call failed');
                }
                
                return response.json();
            }
            
            function showLoading(show) {
                document.getElementById('loading').style.display = show ? 'block' : 'none';
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error');
                if (message) {
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                } else {
                    errorDiv.style.display = 'none';
                }
            }
            
            async function loadFolders() {
                try {
                    const result = await apiCall('/api/folders');
                    const foldersDiv = document.getElementById('folders');
                    foldersDiv.innerHTML = result.folders.map(folder => 
                        \`<button class="folder-btn \${folder === selectedFolder ? 'active' : ''}" 
                                 onclick="selectFolder('\${folder}')">
                            \${folder}
                         </button>\`
                    ).join('');
                } catch (error) {
                    showError('Failed to load folders: ' + error.message);
                }
            }
            
            async function loadEmails() {
                showLoading(true);
                showError(null);
                
                try {
                    const result = await apiCall(\`/api/emails/\${selectedFolder}\`);
                    const emailsDiv = document.getElementById('emails');
                    emailsDiv.innerHTML = result.items.map(email => 
                        \`<div class="email-item \${!email.is_read ? 'unread' : ''}">
                            <h4>\${email.subject}</h4>
                            <p>From: \${email.from_address}</p>
                            <p>Date: \${new Date(email.timestamp).toLocaleString()}</p>
                            \${email.has_attachments ? '<span>📎</span>' : ''}
                         </div>\`
                    ).join('');
                } catch (error) {
                    showError('Failed to load emails: ' + error.message);
                } finally {
                    showLoading(false);
                }
            }
            
            function selectFolder(folder) {
                selectedFolder = folder;
                loadFolders(); // Refresh to update active state
                loadEmails();
            }
            
            // Initialize dashboard
            loadFolders().then(() => loadEmails());
        </script>
    </body>
    </html>
    `;
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`Email Dashboard running at http://localhost:${this.port}`);
      console.log('Update the credentials in the HTML to match your email account');
    });
  }
}

// Usage
const dashboard = new EmailDashboardServer(3000);
dashboard.start();
```

---

## Summary

This Email Engine API provides comprehensive email management capabilities with:

- **Full CRUD Operations**: Create, read, update, and delete emails
- **Real-time Notifications**: WebSocket support for instant email alerts  
- **Multi-folder Support**: Inbox, Sent, Drafts, Trash, Archive, Spam
- **Attachment Handling**: Upload and download file attachments
- **Flexible Authentication**: Multiple authentication methods
- **Production Ready**: Error handling, rate limiting, and best practices

The API is designed for easy integration into web applications, mobile apps, and email clients with comprehensive examples for popular frameworks.

