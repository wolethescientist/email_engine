from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from ..core.config import get_settings

Base = declarative_base()

_settings = get_settings()
engine = create_engine(
    _settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db():
    """Initialize database tables"""
    # Import all models to ensure they are registered with Base
    from ..db.models.user import User  # noqa: F401
    from ..db.models.email import Email, Attachment  # noqa: F401
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    with session_scope() as s:
        yield s