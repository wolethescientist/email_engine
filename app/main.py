from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.routes.connect import router as connect_router
from .api.routes.emails import router as emails_router
from .db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield
    # Cleanup on shutdown (if needed)


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# CORS Middleware
# Configure allowed origins via env var CORS_ORIGINS (comma-separated).
# Example: CORS_ORIGINS=http://localhost:5173,https://connexxionengine.onrender.com
origins = settings.CORS_ORIGINS or []
if not origins and settings.DEBUG:
    # In development, allow common local origins if none provided
    origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],  # Allow all if no specific origins set
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Routers
app.include_router(connect_router)
app.include_router(emails_router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}