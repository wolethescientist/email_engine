# ConnexxionEngine Email Client

Full-stack email client built with `FastAPI` + `React/TypeScript`.  
The backend talks directly to IMAP/SMTP providers (Gmail, Outlook, Yahoo, custom servers), and the frontend provides a modern inbox experience with compose, search, folders, and attachments.

> Status: actively developed, local/dev environment ready. Deployment is the next milestone.

## Why This Project

- Build a production-style email workflow on real protocols (IMAP/SMTP), not mock data
- Practice secure credential handling and safe HTML rendering
- Design a responsive frontend for heavy list + detail interactions
- Build clean service boundaries between API routes, business logic, and transport operations

## Core Features

- Email provider connection and validation (`IMAP` + `SMTP`)
- Inbox/sent/drafts/trash/archive/spam folder workflows
- Read/unread, star/unstar, move, archive, delete, restore actions
- Compose and draft support with attachments
- Search and filtering
- Virtualized email list rendering for performance
- Connection pooling and background keepalive for backend stability

## Tech Stack

### Backend
- `Python`, `FastAPI`, `Pydantic`
- `aioimaplib`, `aiosmtplib`
- `cryptography`, `PyJWT`

### Frontend
- `React 18`, `TypeScript`, `Vite`
- `Tailwind CSS`
- `@tanstack/react-query`, `@tanstack/react-virtual`
- `react-hook-form`, `zod`, `react-quill`

## Project Structure

```text
email_engine/
  app/
    api/routes/          # FastAPI endpoints
    core/                # config, security, connection pooling
    schemas/             # request/response models
    services/            # email domain logic (IMAP/SMTP orchestration)
    main.py              # app entrypoint
  frontend/
    src/components/      # UI components
    src/pages/           # route-level pages
    src/services/        # API client
    src/types/           # TypeScript models
```

## Local Development

### Prerequisites

- `Python 3.11+`
- `Node.js 18+`

### 1) Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:
- App: `http://localhost:5173`

## Environment Setup

Create `.env` in the project root (see `.env.example`):

```env
APP_NAME=ConnexxionEngine
DEBUG=true
AES_SECRET_KEY=your-base64-32-byte-key
JWT_SECRET_KEY=your-secret
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## API Surface (High Level)

- `POST /api/connect`
- `POST /api/emails/folders`
- `POST /api/emails/inbox`
- `POST /api/emails/send`
- `POST /api/emails/compose`
- `POST /api/emails/{id}`
- `POST /api/emails/{id}/read`
- `POST /api/emails/{id}/star`
- `POST /api/emails/{id}/delete`
- `POST /api/emails/{id}/archive`
- `POST /api/emails/{id}/restore`

## Challenges & Tradeoffs

### 1) Security vs UX
- **Challenge:** Users want quick reconnects, but persisting credentials increases risk.
- **Decision:** Favor security by keeping credentials ephemeral and encrypted, accepting extra reconnection friction.

### 2) Real-time Freshness vs Provider Limits
- **Challenge:** Frequent mailbox polling can hit provider limits and increase latency/cost.
- **Decision:** Use pooled connections and keepalive/cleanup intervals to balance freshness and stability.

### 3) Rich HTML Emails vs XSS Safety
- **Challenge:** Rendering full HTML emails can expose script/style attack vectors.
- **Decision:** Sanitize rendered HTML (DOMPurify) and restrict unsafe content, even if some emails lose original styling.

### 4) Feature Depth vs Delivery Speed
- **Challenge:** Email clients have huge scope (rules, offline sync, OAuth, threading, etc.).
- **Decision:** Prioritize core workflows (read, compose, move, search, attachments) before advanced features.

### 5) Simplicity vs Infra Complexity
- **Challenge:** Background jobs, websockets, and Redis would improve responsiveness.
- **Decision:** Keep architecture simple in this stage (single API service + frontend) and defer distributed infra until deployment.

## Current Limitations

- Not deployed yet (local/dev workflow currently)
- OAuth provider auth is planned but not complete
- No full end-to-end automated suite yet

## Next Milestones

- Deploy backend and frontend
- Add OAuth-based provider login
- Add integration and e2e tests
- Add production logging/metrics and CI pipeline
