"""FastAPI dependencies for database sessions and services."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from ..database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for the request lifecycle."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


