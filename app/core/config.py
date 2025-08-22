from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel

# Resolve repo root and .env path robustly
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
try:
    # Prefer pydantic v2 settings if available
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    class Settings(BaseSettings):
        # Point to absolute .env to avoid CWD issues
        model_config = SettingsConfigDict(env_file=str(ENV_PATH), env_file_encoding="utf-8", case_sensitive=False)
        # Database & Cache
        DATABASE_URL: str
        REDIS_URL: str

        # Security
        AES_SECRET_KEY: str  # Base64-encoded 32-byte key for AES-GCM
        JWT_SECRET_KEY: str  # HS256 secret
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRES_MINUTES: int = 60

        # SMTP/IMAP defaults
        SMTP_TIMEOUT_SECONDS: int = 15
        IMAP_TIMEOUT_SECONDS: int = 15
        SMTP_USE_SSL: bool = True
        IMAP_USE_SSL: bool = True

        # App
        APP_NAME: str = "ConnexxionEngine"
        DEBUG: bool = False

        # CORS
        CORS_ORIGINS: list[str] = []

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
        DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        REDIS_URL: str = os.getenv("REDIS_URL", "")
        AES_SECRET_KEY: str = os.getenv("AES_SECRET_KEY", "")
        JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
        JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
        SMTP_TIMEOUT_SECONDS: int = int(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))
        IMAP_TIMEOUT_SECONDS: int = int(os.getenv("IMAP_TIMEOUT_SECONDS", "15"))
        SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
        IMAP_USE_SSL: bool = os.getenv("IMAP_USE_SSL", "true").lower() == "true"
        APP_NAME: str = os.getenv("APP_NAME", "ConnexxionEngine")
        DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        # Comma-separated list of origins, e.g. http://localhost:5173,http://localhost:3000
        CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

    _settings = Settings()

    @lru_cache()
    def get_settings() -> "Settings":
        return _settings