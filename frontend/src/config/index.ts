import { EmailProvider } from '@/types';

export const config = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  ENABLE_DEBUG: import.meta.env.DEV,
  MAX_ATTACHMENT_SIZE: 25 * 1024 * 1024, // 25MB
  DEFAULT_PAGE_SIZE: 50,
  MAX_PAGE_SIZE: 200,
  SUPPORTED_PROVIDERS: ['gmail', 'outlook', 'yahoo', 'custom'] as const,
};

export const EMAIL_PROVIDERS: Record<string, EmailProvider> = {
  gmail: {
    name: 'Gmail',
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 465,
    oauth_supported: true,
  },
  outlook: {
    name: 'Outlook',
    imap_host: 'outlook.office365.com',
    imap_port: 993,
    smtp_host: 'smtp.office365.com',
    smtp_port: 587,
    oauth_supported: true,
  },
  yahoo: {
    name: 'Yahoo',
    imap_host: 'imap.mail.yahoo.com',
    imap_port: 993,
    smtp_host: 'smtp.mail.yahoo.com',
    smtp_port: 465,
    oauth_supported: false,
  },
  custom: {
    name: 'Custom',
    imap_host: '',
    imap_port: 993,
    smtp_host: '',
    smtp_port: 465,
    oauth_supported: false,
  },
};

export const FOLDER_ICONS = {
  inbox: 'Inbox',
  sent: 'Send',
  drafts: 'FileText',
  trash: 'Trash2',
  archive: 'Archive',
  spam: 'ShieldAlert',
} as const;

export const KEYBOARD_SHORTCUTS = {
  COMPOSE: 'c',
  SEARCH: '/',
  NEXT_EMAIL: 'j',
  PREV_EMAIL: 'k',
  SELECT: 'x',
  ARCHIVE: 'e',
  DELETE: '#',
  REPLY: 'r',
  REPLY_ALL: 'a',
  FORWARD: 'f',
  MARK_READ: 'i',
  STAR: 's',
} as const;
