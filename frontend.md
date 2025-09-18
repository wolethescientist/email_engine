# ConnexxionEngine Frontend Integration Guide

## Overview

ConnexxionEngine is a secure, professional email API service built with FastAPI that provides encrypted email management over a RESTful API. This guide provides comprehensive documentation for frontend engineers to integrate with the backend API and create a beautiful, functional email client interface.

## Table of Contents

1. [API Base Information](#api-base-information)
2. [Authentication & Security](#authentication--security)
3. [Core API Endpoints](#core-api-endpoints)
4. [Data Models](#data-models)
5. [Frontend UI Components Guide](#frontend-ui-components-guide)
6. [Error Handling](#error-handling)
7. [Real-time Features](#real-time-features)
8. [Best Practices](#best-practices)
9. [Example Integration](#example-integration)

## API Base Information

### Base URL
```
http://localhost:8000/api  # Development
https://your-domain.com/api  # Production
```

### Content Type
All requests should use `Content-Type: application/json`

### CORS Configuration
The API supports CORS with configurable origins. Default development origins:
- `http://localhost:5173` (Vite)
- `http://localhost:3000` (React/Next.js)

## Authentication & Security

### Authentication Methods
The API supports multiple authentication methods (in order of preference):

1. **Request Body Credentials** (Recommended)
2. **HTTP Headers**
3. **Query Parameters**
4. **OAuth2 Access Tokens**

### Credential Structure
```typescript
interface Credentials {
  email: string;           // User's email address
  password?: string;       // Email account password (encrypted)
  access_token?: string;   // OAuth2 access token for XOAUTH2
  imap_host: string;       // IMAP server hostname
  imap_port: number;       // IMAP port (default: 993)
  smtp_host: string;       // SMTP server hostname
  smtp_port: number;       // SMTP port (default: 465)
}
```

### Security Features
- **AES-256-GCM Encryption**: All passwords are encrypted before storage
- **JWT Tokens**: Secure token-based authentication
- **SSL/TLS**: All connections use encrypted protocols
- **Stateless Operation**: No database required, works directly with IMAP/SMTP

## Core API Endpoints

### 1. Connection Validation

#### POST `/api/connect`
Validate IMAP/SMTP connectivity and credentials.

**Request:**
```typescript
interface ConnectRequest {
  email: string;
  password?: string;
  access_token?: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
}
```

**Response:**
```typescript
interface ConnectResponse {
  success: boolean;
  message?: string;
}
```

**UI Implementation:**
- Create a connection setup form with fields for all credential parameters
- Include preset configurations for popular providers (Gmail, Outlook, etc.)
- Show real-time validation feedback
- Display success/error messages clearly

### 2. Email Operations

#### POST `/api/emails/folders`
List available mailbox folders.

**Request:**
```typescript
interface ListRequest {
  creds: Credentials;
}
```

**Response:**
```typescript
interface FoldersResponse {
  folders: string[];  // ["inbox", "sent", "drafts", "trash", "archive", "spam"]
}
```

#### POST `/api/emails/inbox` (and similar for sent, drafts, trash, archive, spam)
Get paginated email list from specific folder.

**Request:**
```typescript
interface ListRequest {
  creds: Credentials;
  page: number;        // Default: 1
  size: number;        // Default: 50, max: 200
  search_text?: string;
  is_starred?: boolean;
  read_status?: boolean;
}
```

**Response:**
```typescript
interface PaginatedEmails {
  page: number;
  size: number;
  total: number;
  items: EmailItem[];
}

interface EmailItem {
  id: number;
  folder: string;
  subject?: string;
  from_address?: string;
  to_addresses: string[];
  is_read: boolean;
  timestamp?: string;
  has_attachments: boolean;
  is_flagged: boolean;
}
```

#### POST `/api/emails/{email_id}`
Get detailed email content.

**Request:**
```typescript
interface EmailDetailRequest {
  creds: Credentials;
  folder: string;  // Default: "inbox"
}
```

**Response:**
```typescript
interface EmailDetail {
  id?: number;
  folder: string;
  subject?: string;
  body?: string;
  from_address?: string;
  to_addresses: string[];
  cc_addresses: string[];
  bcc_addresses: string[];
  is_read: boolean;
  timestamp?: string;
  has_attachments: boolean;
  is_flagged: boolean;
  attachments: string[];  // List of filenames
}
```

#### POST `/api/emails/compose`
Save email as draft.

**Request:**
```typescript
interface EmailComposeRequest {
  creds: Credentials;
  subject?: string;
  body?: string;
  to: string[];
  cc: string[];
  bcc: string[];
  attachments: AttachmentIn[];
}

interface AttachmentIn {
  filename: string;
  content_base64: string;  // Base64-encoded file content
  content_type?: string;
}
```

**Response:**
```typescript
interface DraftResponse {
  success: boolean;
  id?: number;
  message?: string;
}
```

#### POST `/api/emails/send`
Send email.

**Request:**
```typescript
interface SendEmailRequest extends EmailComposeRequest {
  draft_id?: number;  // Optional: send existing draft
}
```

**Response:**
```typescript
interface EmailDetail {
  // Same as EmailDetail above
}
```

### 3. Email Management Operations

#### POST `/api/emails/{email_id}/delete`
Move email to trash.

#### POST `/api/emails/{email_id}/archive`
Archive email.

#### POST `/api/emails/{email_id}/unarchive`
Move email from archive to inbox.

#### POST `/api/emails/{email_id}/read`
Mark email as read/unread.

**Request:**
```typescript
interface ModifyEmailRequest {
  creds: Credentials;
  folder: string;
  read: boolean;  // true to mark as read, false for unread
}
```

#### POST `/api/emails/{email_id}/star`
Star/unstar email.

**Request:**
```typescript
interface StarEmailRequest {
  creds: Credentials;
  folder: string;
  starred: boolean;  // true to star, false to unstar
}
```

#### POST `/api/emails/{email_id}/spam`
Mark email as spam.

#### POST `/api/emails/{email_id}/unspam`
Remove email from spam folder.

#### POST `/api/emails/{email_id}/restore`
Restore email from trash to inbox.

### 4. Attachment Handling

#### POST `/api/emails/{email_id}/attachments/{filename}`
Download email attachment.

**Request:**
```typescript
interface AttachmentDownloadRequest {
  creds: Credentials;
  folder: string;
}
```

**Response:** Binary file content with appropriate headers.

## Data Models

### TypeScript Interfaces

```typescript
// Core Models
interface Credentials {
  email: string;
  password?: string;
  access_token?: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
}

interface EmailItem {
  id: number;
  folder: string;
  subject?: string;
  from_address?: string;
  to_addresses: string[];
  is_read: boolean;
  timestamp?: string;
  has_attachments: boolean;
  is_flagged: boolean;
}

interface EmailDetail extends EmailItem {
  body?: string;
  cc_addresses: string[];
  bcc_addresses: string[];
  attachments: string[];
}

interface PaginatedEmails {
  page: number;
  size: number;
  total: number;
  items: EmailItem[];
}

interface AttachmentIn {
  filename: string;
  content_base64: string;
  content_type?: string;
}

// Request/Response Models
interface ListRequest {
  creds: Credentials;
  page?: number;
  size?: number;
  search_text?: string;
  is_starred?: boolean;
  read_status?: boolean;
}

interface EmailComposeRequest {
  creds: Credentials;
  subject?: string;
  body?: string;
  to: string[];
  cc: string[];
  bcc: string[];
  attachments: AttachmentIn[];
}

interface SendEmailRequest extends EmailComposeRequest {
  draft_id?: number;
}
```

## Frontend UI Components Guide

### 1. Authentication Components

#### Connection Setup Form
```typescript
interface ConnectionFormProps {
  onConnect: (credentials: Credentials) => void;
  loading: boolean;
  error?: string;
}
```

**Features to implement:**
- Provider presets (Gmail, Outlook, Yahoo, Custom)
- Form validation with real-time feedback
- Password visibility toggle
- OAuth2 flow integration
- Connection testing with loading states

#### Provider Presets
```typescript
const EMAIL_PROVIDERS = {
  gmail: {
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 465,
    oauth_supported: true
  },
  outlook: {
    imap_host: 'outlook.office365.com',
    imap_port: 993,
    smtp_host: 'smtp.office365.com',
    smtp_port: 587,
    oauth_supported: true
  },
  yahoo: {
    imap_host: 'imap.mail.yahoo.com',
    imap_port: 993,
    smtp_host: 'smtp.mail.yahoo.com',
    smtp_port: 465,
    oauth_supported: false
  }
};
```

### 2. Email List Components

#### Email List View
```typescript
interface EmailListProps {
  emails: PaginatedEmails;
  selectedEmails: number[];
  onEmailSelect: (emailId: number) => void;
  onEmailOpen: (emailId: number) => void;
  onBulkAction: (action: string, emailIds: number[]) => void;
  loading: boolean;
}
```

**Features to implement:**
- Virtual scrolling for performance
- Multi-select with checkboxes
- Bulk actions (delete, archive, mark as read)
- Search and filter controls
- Pagination controls
- Drag and drop for folder management
- Keyboard navigation (j/k for up/down, x for select)

#### Email List Item
```typescript
interface EmailItemProps {
  email: EmailItem;
  selected: boolean;
  onSelect: () => void;
  onOpen: () => void;
}
```

**Visual indicators:**
- Unread emails (bold text, colored dot)
- Starred emails (star icon)
- Attachments (paperclip icon)
- Priority indicators
- Sender avatars
- Timestamp formatting (relative time)

### 3. Email Composition

#### Compose Email Form
```typescript
interface ComposeFormProps {
  initialData?: Partial<EmailComposeRequest>;
  onSend: (email: SendEmailRequest) => void;
  onSaveDraft: (email: EmailComposeRequest) => void;
  onDiscard: () => void;
}
```

**Features to implement:**
- Rich text editor (WYSIWYG)
- Auto-save drafts
- Recipient validation and suggestions
- File attachment with drag-and-drop
- CC/BCC toggle
- Send later scheduling
- Email templates
- Signature management

#### Attachment Handler
```typescript
interface AttachmentProps {
  attachments: AttachmentIn[];
  onAdd: (files: File[]) => void;
  onRemove: (index: number) => void;
  maxSize: number;
  allowedTypes: string[];
}
```

### 4. Email Detail View

#### Email Reader
```typescript
interface EmailReaderProps {
  email: EmailDetail;
  onReply: () => void;
  onReplyAll: () => void;
  onForward: () => void;
  onDelete: () => void;
  onArchive: () => void;
  onStar: () => void;
}
```

**Features to implement:**
- HTML email rendering with security
- Attachment preview and download
- Print functionality
- Email actions toolbar
- Thread view (if implementing conversations)
- Security warnings for external content

### 5. Folder Navigation

#### Sidebar Navigation
```typescript
interface SidebarProps {
  folders: string[];
  currentFolder: string;
  unreadCounts: Record<string, number>;
  onFolderSelect: (folder: string) => void;
}
```

**Features to implement:**
- Collapsible folder tree
- Unread count badges
- Drag and drop email organization
- Custom folder creation
- Search within folders

### 6. Search and Filters

#### Search Component
```typescript
interface SearchProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  suggestions: string[];
  recentSearches: string[];
}

interface SearchFilters {
  folder?: string;
  is_starred?: boolean;
  read_status?: boolean;
  has_attachments?: boolean;
  date_range?: {
    start: Date;
    end: Date;
  };
}
```

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation errors, missing credentials)
- `404`: Not Found (email not found)
- `500`: Internal Server Error
- `502`: Bad Gateway (IMAP/SMTP connection issues)

### Error Response Format
```typescript
interface ErrorResponse {
  detail: string;
}
```

### Frontend Error Handling Strategy
```typescript
const handleApiError = (error: any) => {
  if (error.response?.status === 400) {
    // Show validation errors to user
    showToast(error.response.data.detail, 'error');
  } else if (error.response?.status === 404) {
    // Handle not found
    showToast('Email not found', 'warning');
  } else if (error.response?.status >= 500) {
    // Server errors
    showToast('Server error. Please try again later.', 'error');
  } else {
    // Network errors
    showToast('Connection error. Check your internet.', 'error');
  }
};
```

## Real-time Features

### Connection Pooling
The backend uses connection pooling for optimal performance:
- Automatic connection reuse
- Idle connection cleanup
- Connection health monitoring

### Performance Considerations
- Implement request debouncing for search
- Use virtual scrolling for large email lists
- Cache email content locally
- Implement optimistic updates for actions

## Best Practices

### 1. Security
- Never store credentials in localStorage
- Use secure session storage for temporary tokens
- Implement proper CSRF protection
- Validate all user inputs
- Sanitize HTML content in emails

### 2. User Experience
- Implement loading states for all async operations
- Provide clear feedback for user actions
- Use skeleton screens while loading
- Implement keyboard shortcuts
- Support offline mode with cached data

### 3. Performance
- Implement pagination for large datasets
- Use lazy loading for email content
- Compress images and attachments
- Implement request caching
- Use service workers for background sync

### 4. Accessibility
- Implement proper ARIA labels
- Support keyboard navigation
- Provide high contrast mode
- Use semantic HTML elements
- Include screen reader support

## Example Integration

### React/TypeScript Example

```typescript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

interface EmailClientProps {
  credentials: Credentials;
}

const EmailClient: React.FC<EmailClientProps> = ({ credentials }) => {
  const [emails, setEmails] = useState<PaginatedEmails | null>(null);
  const [currentFolder, setCurrentFolder] = useState('inbox');
  const [loading, setLoading] = useState(false);

  const fetchEmails = async (folder: string, page = 1) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/emails/${folder}`, {
        creds: credentials,
        page,
        size: 50
      });
      setEmails(response.data);
    } catch (error) {
      handleApiError(error);
    } finally {
      setLoading(false);
    }
  };

  const sendEmail = async (emailData: SendEmailRequest) => {
    try {
      const response = await axios.post(`${API_BASE}/emails/send`, emailData);
      showToast('Email sent successfully!', 'success');
      return response.data;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  };

  const markAsRead = async (emailId: number, read: boolean) => {
    try {
      await axios.post(`${API_BASE}/emails/${emailId}/read`, {
        creds: credentials,
        folder: currentFolder,
        read
      });
      // Update local state optimistically
      setEmails(prev => prev ? {
        ...prev,
        items: prev.items.map(email => 
          email.id === emailId ? { ...email, is_read: read } : email
        )
      } : null);
    } catch (error) {
      handleApiError(error);
    }
  };

  useEffect(() => {
    fetchEmails(currentFolder);
  }, [currentFolder]);

  return (
    <div className="email-client">
      <Sidebar 
        currentFolder={currentFolder}
        onFolderSelect={setCurrentFolder}
      />
      <EmailList 
        emails={emails}
        loading={loading}
        onMarkAsRead={markAsRead}
      />
      <ComposeModal 
        onSend={sendEmail}
        credentials={credentials}
      />
    </div>
  );
};
```

### Vue.js Example

```typescript
<template>
  <div class="email-client">
    <EmailSidebar 
      :current-folder="currentFolder"
      @folder-select="setCurrentFolder"
    />
    <EmailList 
      :emails="emails"
      :loading="loading"
      @email-action="handleEmailAction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useEmailApi } from '@/composables/useEmailApi';

const props = defineProps<{
  credentials: Credentials;
}>();

const { fetchEmails, sendEmail, markAsRead } = useEmailApi(props.credentials);

const emails = ref<PaginatedEmails | null>(null);
const currentFolder = ref('inbox');
const loading = ref(false);

const handleEmailAction = async (action: string, emailId: number) => {
  switch (action) {
    case 'markRead':
      await markAsRead(emailId, true);
      break;
    case 'delete':
      await deleteEmail(emailId);
      break;
    // Handle other actions
  }
};

watch(currentFolder, async (newFolder) => {
  loading.value = true;
  emails.value = await fetchEmails(newFolder);
  loading.value = false;
});

onMounted(() => {
  fetchEmails(currentFolder.value);
});
</script>
```

## Testing Recommendations

### Unit Tests
- Test all API service functions
- Mock API responses for consistent testing
- Test error handling scenarios
- Validate data transformations

### Integration Tests
- Test complete user workflows
- Test authentication flows
- Test email operations end-to-end
- Test error recovery

### E2E Tests
- Test critical user journeys
- Test across different browsers
- Test responsive design
- Test accessibility features

## Deployment Considerations

### Environment Configuration
```typescript
const config = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api',
  ENABLE_DEBUG: process.env.NODE_ENV === 'development',
  MAX_ATTACHMENT_SIZE: 25 * 1024 * 1024, // 25MB
  SUPPORTED_PROVIDERS: ['gmail', 'outlook', 'yahoo', 'custom']
};
```

### Build Optimization
- Enable code splitting
- Optimize bundle size
- Implement service worker caching
- Use CDN for static assets

This comprehensive guide should provide frontend engineers with everything needed to create a beautiful, functional email client that integrates seamlessly with the ConnexxionEngine backend API.
