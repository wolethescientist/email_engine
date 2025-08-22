# 📧 Email Engine - Product Requirements Document (PRD)

## 1. Overview

The **Email Engine** is a FastAPI-based backend service for the iGov
platform. It enables users to compose, send, receive, and manage
government emails securely, eliminating reliance on paper-based
workflows. The system will act as a webmail engine connected to SMTP and
IMAP servers.

------------------------------------------------------------------------

## 2. Goals & Objectives

-   Provide a secure, government-grade email API service.
-   Enable composing, sending, receiving, and organizing emails through
    the iGov frontend.
-   Ensure compliance with security and audit requirements.
-   Support scalability and performance for thousands of government
    employees.

------------------------------------------------------------------------

## 3. Features

### Core Features

1.  **Compose Mail**
    -   Create drafts with subject, body, recipients (To, CC, BCC).
    -   Add attachments.
2.  **Send Mail**
    -   Deliver email via SMTP.
    -   Move message to "Sent" folder.
3.  **Receive Mail**
    -   Fetch messages from IMAP Inbox.
    -   Parse headers, body, and attachments.
4.  **Inbox**
    -   List inbox emails.
    -   View single email details.
    -   Mark emails as read/unread.
5.  **Drafts**
    -   Save and retrieve drafts.
    -   Edit and resend.
6.  **Sent**
    -   Retrieve sent messages from IMAP "Sent" folder.
7.  **Trash**
    -   Move emails to Trash folder.
    -   Retrieve trashed messages.
    -   Restore messages.
8.  **Archive**
    -   Move messages to Archive folder.
    -   Retrieve archived messages.

------------------------------------------------------------------------

## 4. API Endpoints (High-Level)

### Auth & Connection

-   `POST /connect` → Validate IMAP/SMTP connection.

### Email Management

-   `POST /emails/compose` → Save draft.
-   `POST /emails/send` → Send email.

### Mailboxes

-   `GET /emails/inbox` → Fetch inbox emails.
-   `GET /emails/sent` → Fetch sent emails.
-   `GET /emails/drafts` → Fetch drafts.
-   `GET /emails/trash` → Fetch trashed emails.
-   `GET /emails/archive` → Fetch archived emails.
-   `GET /emails/{id}` → Fetch single email.

### Email Actions

-   `DELETE /emails/{id}` → Move to Trash.
-   `PATCH /emails/{id}/archive` → Archive email.
-   `PATCH /emails/{id}/read` → Mark read/unread.

------------------------------------------------------------------------

## 5. Architecture

### Components

-   **FastAPI Service** → Exposes REST API.
-   **SMTP Client** → Sends emails.
-   **IMAP Client** → Fetches and manages emails.
-   **Database (PostgreSQL)** → Stores drafts, cached emails, logs.
-   Redis For caching 


### Tech Stack

-   Language: Python 3.11+
-   Framework: FastAPI
-   Libraries:
    -   `smtplib` (SMTP)
    -   `imaplib` / `imap-tools` (IMAP)
    -   `email` (MIME parsing)
    -   `SQLAlchemy` (ORM)


------------------------------------------------------------------------

## 6. Database Schema (Simplified)

### `users`

-   id (PK)
-   email (unique)
-   encrypted_password
-   imap_host
-   smtp_host
-   imap_port
-   smtp_port

### `emails`

-   id (PK)
-   user_id (FK)
-   folder (Inbox, Sent, Drafts, Trash, Archive)
-   subject
-   body
-   from_address
-   to_addresses (JSON)
-   cc_addresses (JSON)
-   bcc_addresses (JSON)
-   is_read (boolean)
-   created_at
-   updated_at

### `attachments`

-   id (PK)
-   email_id (FK)
-   filename
-   filepath or binary

------------------------------------------------------------------------

## 7. Security Considerations

-   Enforce TLS for SMTP/IMAP.
-   Encrypt credentials (AES).
-   Ensure role-based access (RBAC).

------------------------------------------------------------------------

## 8. Performance Considerations

-   Implement caching layer for frequently accessed folders.
-   Use background jobs for syncing large mailboxes.
-   Paginate email list responses.
-   Index database tables for fast lookups.

------------------------------------------------------------------------

## 9. Non-Functional Requirements

-   **Scalability:** Support thousands of users simultaneously.
-   **Availability:** 99.9% uptime SLA.
-   **Security:** Government-grade encryption and compliance.
-   **Observability:** Centralized logging.

------------------------------------------------------------------------

## 10. Deliverables

-   FastAPI service with all endpoints implemented.
-   PostgreSQL database integration.
-   API documentation (OpenAPI auto-generated).
-   
------------------------------------------------------------------------

## 11. Future Enhancements

-   Push notifications for new mail.
-   OAuth2 authentication with government SSO.
-   AI-powered spam filtering and smart categorization.
-   Email search with full-text indexing.

------------------------------------------------------------------------

## 12. Conclusion

The **Email Engine** will provide a robust, secure, and scalable email
solution integrated into the iGov platform, fully replacing paper-based
communications and improving government workflow efficiency.
