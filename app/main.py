from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .api.routes.connect import router as connect_router
from .api.routes.emails import router as emails_router

settings = get_settings()
app = FastAPI(title=settings.APP_NAME)

# CORS Middleware
origins = settings.CORS_ORIGINS or []
if not origins and settings.DEBUG:
    origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(connect_router)
app.include_router(emails_router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}