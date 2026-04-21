import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import get_settings
from .core.connection_pool import get_connection_pool
from .api.routes.connect import router as connect_router
from .api.routes.emails import router as emails_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('email_engine.log') if not get_settings().DEBUG else logging.NullHandler()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks"""
    # Startup
    settings = get_settings()
    
    # Start connection keepalive + cleanup task
    pool = get_connection_pool()
    keepalive_task = asyncio.create_task(
        connection_keepalive_worker(pool, settings.CONNECTION_CLEANUP_INTERVAL)
    )
    
    logging.info(f"Started {settings.APP_NAME} with connection pooling (keepalive every {settings.CONNECTION_CLEANUP_INTERVAL}s, evict after {getattr(settings, 'MAX_IDLE_TIME', 180)}s)")
    
    yield
    
    # Shutdown
    keepalive_task.cancel()
    await pool.close_all_connections()
    logging.info("Shutdown complete")

async def connection_keepalive_worker(pool, interval: int):
    """Background task to send keepalive NOOPs and evict dead connections.
    
    Runs every `interval` seconds and:
    1. Sends NOOP to connections idle > 2 min (keeps them alive)
    2. Evicts connections idle > max_idle_time (frees resources)
    """
    while True:
        try:
            await asyncio.sleep(interval)
            await pool.keepalive_idle_connections()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Connection keepalive error: {e}")

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


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
app.include_router(connect_router, prefix="/api")
app.include_router(emails_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation"""
    return {
        "message": "ConnexxionEngine Email API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/healthz")
def healthz():
    return {"status": "ok"}