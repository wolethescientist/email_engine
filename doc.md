# Email Engine API Documentation

Welcome to the Email Engine API documentation. This guide will help you understand how to interact with the API to manage emails, including sending, receiving, and organizing them.

## Authentication

Most endpoints require authentication. You can provide your email account credentials in the request body. The credentials object is required for most email operations.

### Credentials Object

```json
{
  "email": "user@example.com",
  "password": "your-password", // or access_token
  "access_token": "your-oauth-token", // if using OAuth
  "imap_host": "imap.example.com",
  "imap_port": 993,
  "smtp_host": "smtp.example.com",
  "smtp_port": 465
}
```

## Endpoints

### Connection

#### `POST /connect`

Validates IMAP/SMTP connectivity and credentials without saving or returning any tokens. This is useful for checking if the provided credentials are correct before proceeding with other operations.

**Request Body:**

Same as the `Credentials` object.

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

async function validateConnection() {
  try {
    const response = await axios.post(`${API_BASE_URL}/connect`, {
      email: 'user@example.com',
      password: 'your-password',
      imap_host: 'imap.example.com',
      imap_port: 993,
      smtp_host: 'smtp.example.com',
      smtp_port: 465,
    });

    if (response.data.success) {
      console.log('Connection validated successfully!');
    } else {
      console.error('Connection validation failed:', response.data.message);
    }
  } catch (error) {
    console.error('Error validating connection:', error.response?.data?.detail || error.message);
  }
}

validateConnection();
```

### Emails

#### `POST /emails/folders`

Lists all available folders in the email account (e.g., Inbox, Sent, Drafts).

**Request Body:**

```json
{
  "creds": { ... } // Credentials object
}
```

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

async function listFolders() {
  try {
    const response = await axios.post(`${API_BASE_URL}/emails/folders`, {
      creds: {
        email: 'user@example.com',
        password: 'your-password',
        imap_host: 'imap.example.com',
        imap_port: 993,
        smtp_host: 'smtp.example.com',
        smtp_port: 465,
      }
    });
    console.log('Folders:', response.data.folders);
  } catch (error) {
    console.error('Error listing folders:', error.response?.data?.detail || error.message);
  }
}

listFolders();
```


#### `POST /emails/compose`

Creates and saves a new draft email to the IMAP server's drafts folder.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "subject": "Draft Subject",
  "body": "This is the body of the draft.",
  "to": ["recipient1@example.com"],
  "cc": [],
  "bcc": [],
  "attachments": [
    {
      "filename": "document.pdf",
      "content_base64": "...", // Base64 encoded content
      "content_type": "application/pdf"
    }
  ]
}
```

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';
import fs from 'fs';

const API_BASE_URL = 'http://localhost:8000';

async function composeDraft() {
  try {
    const attachmentContent = fs.readFileSync('path/to/document.pdf').toString('base64');

    const response = await axios.post(`${API_BASE_URL}/emails/compose`, {
      creds: { /* ... */ },
      subject: 'My Draft',
      body: 'Hello, this is a draft.',
      to: ['test@example.com'],
      attachments: [
        {
          filename: 'document.pdf',
          content_base64: attachmentContent,
          content_type: 'application/pdf'
        }
      ]
    });

    if (response.data.success) {
      console.log('Draft saved successfully.');
    }
  } catch (error) {
    console.error('Error composing draft:', error.response?.data?.detail || error.message);
  }
}

composeDraft();
```

#### `POST /emails/send`

Sends an email. This can be a new email or an existing draft.

**Request Body:**

Same as `/emails/compose`, with an optional `draft_id`.

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

async function sendEmail() {
  try {
    const response = await axios.post(`${API_BASE_URL}/emails/send`, {
      creds: { /* ... */ },
      subject: 'Hello from API',
      body: 'This is the email body.',
      to: ['recipient@example.com']
    });
    console.log('Email sent:', response.data);
  } catch (error) {
    console.error('Error sending email:', error.response?.data?.detail || error.message);
  }
}

sendEmail();
```

#### `POST /emails/{folder}`

Lists emails in a specific folder (e.g., `inbox`, `sent`, `drafts`, `trash`, `archive`, `spam`).

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "page": 1,
  "size": 50
}
```

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

async function listInbox() {
  try {
    const response = await axios.post(`${API_BASE_URL}/emails/inbox`, {
      creds: { /* ... */ },
      page: 1,
      size: 10
    });
    console.log('Inbox emails:', response.data.items);
  } catch (error) {
    console.error('Error listing inbox:', error.response?.data?.detail || error.message);
  }
}

listInbox();
```

#### `POST /emails/{email_id}`

Retrieves the details of a specific email by its ID.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "inbox" // The folder where the email is located
}
```

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

async function getEmailDetails(emailId: number) {
  try {
    const response = await axios.post(`${API_BASE_URL}/emails/${emailId}`, {
      creds: { /* ... */ },
      folder: 'inbox'
    });
    console.log('Email details:', response.data);
  } catch (error) {
    console.error('Error getting email details:', error.response?.data?.detail || error.message);
  }
}

getEmailDetails(123); // Replace with a real email ID
```


#### `POST /emails/{email_id}/delete`

Moves an email to the trash folder.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "inbox" // The folder where the email is located
}
```

#### `POST /emails/{email_id}/archive`

Moves an email to the archive folder.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "inbox" // The folder where the email is located
}
```

#### `POST /emails/{email_id}/unarchive`

Moves an email from the archive folder back to the inbox.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "archive" // The folder where the email is located
}
```

#### `POST /emails/{email_id}/read`

Marks an email as read or unread.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "inbox",
  "read": true // or false
}
```

#### `POST /emails/{email_id}/attachments/{filename}`

Downloads an attachment from an email.

**Request Body:**

```json
{
  "creds": { ... }, // Credentials object
  "folder": "inbox"
}
```

**Example (Node.js/TypeScript with axios):**

```typescript
import axios from 'axios';
import fs from 'fs';

const API_BASE_URL = 'http://localhost:8000';

async function downloadAttachment(emailId: number, filename: string) {
  try {
    const response = await axios.post(`${API_BASE_URL}/emails/${emailId}/attachments/${filename}`, 
      { creds: { /* ... */ }, folder: 'inbox' },
      { responseType: 'stream' }
    );

    response.data.pipe(fs.createWriteStream(filename));

    console.log(`Attachment ${filename} downloaded.`);
  } catch (error) {
    console.error('Error downloading attachment:', error.response?.data?.detail || error.message);
  }
}

downloadAttachment(123, 'document.pdf');
```

### WebSocket for IDLE

#### `WS /ws/idle`

Establishes a WebSocket connection to monitor for new emails in real-time using the IMAP IDLE command. The server will push updates for new emails.

**Connection URL:**

`ws://localhost:8000/ws/idle?username=<email>&password=<password>&imap_host=<host>&imap_port=<port>`

You can also use headers: `X-Email`, `X-Password`, `X-IMAP-Host`, `X-IMAP-Port`.

**Example (Node.js/TypeScript with `ws` library):**

```typescript
import WebSocket from 'ws';

const email = encodeURIComponent('user@example.com');
const password = encodeURIComponent('your-password');
const imapHost = encodeURIComponent('imap.example.com');
const imapPort = 993;

const wsUrl = `ws://localhost:8000/ws/idle?username=${email}&password=${password}&imap_host=${imapHost}&imap_port=${imapPort}`;

const ws = new WebSocket(wsUrl);

ws.on('open', function open() {
  console.log('WebSocket connection established.');
});

ws.on('message', function incoming(data) {
  console.log('Received:', data.toString());
  // This will be a new email notification
});

ws.on('close', function close() {
  console.log('WebSocket connection closed.');
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
});
```
