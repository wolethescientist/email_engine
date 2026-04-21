Email-Engine required update

Highlights
 	Added mailbox search and filtering (text, starred, read state).
 	Added star/important flag APIs and spam/unspam/restore moves.
 	Improved attachment detection and downloading (exact, Content-ID, case- insensitive).
 	More robust folder resolution and batched fetch for faster listings.  	Better timestamps and importance inference in listings/details.
 	Improved draft saving and sent-copy behavior for broader provider compatibility.

API Schema Changes (app/schemas/email.py)
 	Email item metadata:
   Change: Add timestamp, has_attachments, is_flagged to EmailItem and EmailDetail.
   Rationale: Enable richer list UI (sort/indicators) and parity with detail view.
 	List filters:
   Change: Add search_text (full-text), is_starred, read_status to ListRequest.
 
   Rationale: Server-side filtering for performance and better UX.  	
   Star toggle:
   Change: Add StarEmailRequest schema.
   Rationale: Support “star/importantˮ operations as first-class actions.

API Routes (app/api/routes/emails.py)
 	Listing with filters:
   Change: List endpoints now accept search_text, is_starred, read_status; internal call passes these to the service.
   Rationale: Deliver filtered, paginated results without client-side scanning.
 	Star/important:
   Change: Add POST /emails/{email_id}/star to set/unset the IMAP
\Flagged flag.
   Rationale: Bring “starredˮ status in line with common email clients.
 	Spam/unspam and restore:
   Change: Add POST /emails/{id}/spam, /unspam, /restore (Trash→Inbox).
   Rationale: Round out mailbox move operations for typical workflows.
 	Simplified refresh:
   Change: Removed ad-hoc refresh parameter handling in list routes; defaults to real-time current view.
   Rationale: Reduce API surface area and ambiguity; IMAP NOOP is handled service-side when needed.
 	Attachments endpoint unchanged in shape, but benefits from service improvements (see below).

Service Engine (app/services/email_service.py)
 	Faster, richer listing:
   Change: Add _build_search_query to construct IMAP queries for text/starred/read; switched to batched UID FETCH (FLAGS,
 
INTERNALDATE,
BODYSTRUCTURE, selected headers) where possible.
   Rationale: Better performance at page-level, enable server-side filtering, and expose has_attachments, is_flagged, timestamp without fetching full bodies.
Search and internationalization:
   Change: UTF‑8 charset is used for non‑ASCII searches; special character handling and safe quoting for TEXT queries.
   Rationale: Reliable search across international mailboxes and providers. Accurate timestamps:
   Change: Parse INTERNALDATE with robust fallbacks to ISO strings.
   Rationale: Consistent, sortable timestamps across providers/timezones. Importance inference:
   Change: If not server‑flagged, infer importance from headers (X- Priority: 1/2, Importance: high/urgent) and surface as is_flagged.
  Rationale: Catch priority semantics that some clients encode via headers instead of flags.
Star flagging:
   Change: Add set_flagged_status_imap (+/-FLAGS.SILENT \Flagged).   Rationale: Implement the new star toggle endpoint.
Move operations (archive/spam/trash/inbox):
   Change: Same robust multi‑candidate resolution, with improved alias coverage; prefer UID MOVE, fallback to COPY + \Deleted + EXPUNGE.
   Rationale: Work across servers with and without MOVE, minimize user‑visible failures.
Attachment handling:
   Change: Broader detection via BODYSTRUCTURE, dispositions, and filenames; download supports exact filename, Content‑ID (inline media), and case‑insensitive matches; returns content + type + safe filename.
   Rationale: Make attachment display/download reliable across message formats.
 
 	Email bodies and content type:
   Change: send_email and append_draft_imap now set HTML content (set_content(..., subtype='html')) instead of plain text.
   Rationale: Ensure rich‑text composition renders as intended in recipientsʼ clients.
 	Draft saving robustness:
   Change: append_draft_imap tries without flags/timestamp first (common servers reject \Draft); retries without timestamp, logs folder diagnostics on failure.
   Rationale: Improve compatibility with diverse servers (Gmail/Outlook/custom).
 	Observability:
   Change: Add structured logging and telemetry around key flows (listing, detail, attachments).
   Rationale: Easier diagnosis in staging/production without affecting API shape.

App Entrypoint (app/main.py)
 	Logging configuration:
  Change: Add logging.basicConfig with format and optional DEBUG for app.services.email_service.
   Rationale: Improve visibility during staging/deployments; toggleable for prod.


Rationalized Behavior Changes (Why this matters)
 
    Interop and resilience: Broader folder resolution, attachment detection, and     draft handling reduce provider‑specific breakage.
Performance and UX: Batched fetch, server-side filtering, and accurate metadata yield snappier lists and richer UI states.
Feature completeness: Star, spam/unspam, and restore round out mailbox operations expected by users.
Operability: Better logs and stable healthchecks make staging/prod behavior easier to monitor and recover.
