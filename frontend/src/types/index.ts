// Core API Types
export interface Credentials {
  email: string;
  password?: string;
  access_token?: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
}

export interface EmailItem {
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

export interface EmailDetail extends EmailItem {
  body?: string;
  cc_addresses: string[];
  bcc_addresses: string[];
  attachments: string[];
}

export interface PaginatedEmails {
  page: number;
  size: number;
  total: number;
  items: EmailItem[];
}

export interface AttachmentIn {
  filename: string;
  content_base64: string;
  content_type?: string;
}

// Request Types
export interface ListRequest {
  creds: Credentials;
  page?: number;
  size?: number;
  search_text?: string;
  is_starred?: boolean;
  read_status?: boolean;
}

export interface EmailComposeRequest {
  creds: Credentials;
  subject?: string;
  body?: string;
  to: string[];
  cc: string[];
  bcc: string[];
  attachments: AttachmentIn[];
}

export interface SendEmailRequest extends EmailComposeRequest {
  draft_id?: number;
}

export interface ModifyEmailRequest {
  creds: Credentials;
  folder: string;
  read?: boolean;
  starred?: boolean;
}

// Response Types
export interface ConnectResponse {
  success: boolean;
  message?: string;
}

export interface Folder {
  name: string;
  display_name: string;
  type: string;
}

export interface FoldersResponse {
  folders: Folder[];
}

export interface DraftResponse {
  success: boolean;
  id?: number;
  message?: string;
}

export interface ErrorResponse {
  detail: string;
}

// UI Types
export interface SearchFilters {
  folder?: string;
  is_starred?: boolean;
  read_status?: boolean;
  has_attachments?: boolean;
  date_range?: {
    start: Date;
    end: Date;
  };
}

export interface EmailProvider {
  name: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  oauth_supported: boolean;
}

export interface Theme {
  mode: 'light' | 'dark';
}

// Folder types
export type FolderType = 'inbox' | 'sent' | 'drafts' | 'trash' | 'archive' | 'spam';

// Email actions
export type EmailAction = 'read' | 'unread' | 'star' | 'unstar' | 'delete' | 'archive' | 'unarchive' | 'spam' | 'unspam' | 'restore';

// Bulk actions
export interface BulkAction {
  action: EmailAction;
  emailIds: number[];
}
