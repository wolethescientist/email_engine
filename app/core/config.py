from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

# Resolve repo root and .env path robustly
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
try:
    # Prefer pydantic v2 settings if available
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    class Settings(BaseSettings):
        # App
        APP_NAME: str = "ConnexxionEngine"
        DEBUG: bool = False

        # Security
        AES_SECRET_KEY: str = Field(..., description="AES encryption key for secrets")
        JWT_SECRET_KEY: str = Field(..., description="JWT signing key")

        # SMTP
        SMTP_USE_SSL: bool = True
        SMTP_TIMEOUT_SECONDS: int = 30

        # IMAP
        IMAP_USE_SSL: bool = True
        IMAP_TIMEOUT_SECONDS: int = 30

        # Connection Pool
        MAX_CONNECTIONS: int = Field(default=50, description="Maximum connections per pool")
        MAX_IDLE_TIME: int = Field(default=180, description="Max idle time in seconds before eviction")
        CONNECTION_CLEANUP_INTERVAL: int = Field(default=30, description="Keepalive/cleanup interval in seconds")

        # AI
        GEMINI_API_KEY: Optional[str] = Field(default=None, description="Gemini API key")
        GEMINI_MODEL: str = Field(default="gemini-3-flash-preview", description="Gemini model name")

        # CORS  
        CORS_ORIGINS: Optional[List[str]] = Field(default=None, description="Allowed CORS origins")

        model_config = SettingsConfigDict(
            env_file=str(ENV_PATH),
            env_file_encoding="utf-8",
            env_ignore_empty=True,
            extra="ignore",
        )

    @lru_cache()
    def get_settings() -> "Settings":
        return Settings()  # type: ignore

except Exception:
    # Fallback if pydantic_settings is unavailable: load .env explicitly then read from os.getenv
    import os
    from dotenv import load_dotenv

    # Ensure .env is loaded from repo root
    load_dotenv(dotenv_path=str(ENV_PATH), override=False)

    class Settings(BaseModel):
        AES_SECRET_KEY: str = os.getenv("AES_SECRET_KEY", "")
        JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
        JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
        SMTP_TIMEOUT_SECONDS: int = int(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))
        IMAP_TIMEOUT_SECONDS: int = int(os.getenv("IMAP_TIMEOUT_SECONDS", "15"))
        SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
        IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
        GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        APP_NAME: str = os.getenv("APP_NAME", "ConnexxionEngine")
        DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        # Comma-separated list of origins, e.g. http://localhost:5173,http://localhost:3000
        CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    _settings = Settings()

    @lru_cache()
    def get_settings() -> "Settings":
        return _settings