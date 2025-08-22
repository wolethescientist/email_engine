# Email Engine Frontend

React + TypeScript + Vite + Tailwind client for the FastAPI Email Engine.

## Scripts
- `npm install`
- `npm run dev` (http://localhost:5173)

Vite proxy forwards `/api/*` → `http://localhost:8000/*`.

## Env/Config
- Backend base URL is proxied via Vite dev server. For production, set `baseURL` in `src/api/api.ts` as needed or configure reverse proxy.

## Features
- Connect to backend via `/connect` → stores JWT in localStorage
- Mailbox tabs: Inbox, Sent, Drafts, Trash, Archive
- Email detail with actions (read/unread, archive, delete)
- Compose with attachments (base64)
