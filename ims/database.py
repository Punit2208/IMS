"""Database configuration utilities for the Inventory Management System."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Use SQLite for simplicity. Database file stored in project directory.
DATABASE_PATH = Path(__file__).resolve().parent / "ims.sqlite3"

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)

Base = declarative_base()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
