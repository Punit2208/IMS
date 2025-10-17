"""User management and activity logging."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import ActivityLog, User


class UserService:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session

    @property
    def session(self) -> Session:
        if self._external_session is None:
            raise RuntimeError("Session is only available within context manager")
        return self._external_session

    def __enter__(self) -> "UserService":
        if self._external_session is None:
            self._manager = session_scope()
            self._external_session = self._manager.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if hasattr(self, "_manager"):
            self._manager.__exit__(exc_type, exc, tb)
            self._external_session = None

    def create_user(self, username: str, full_name: Optional[str], role: str) -> User:
        user = User(username=username, full_name=full_name, role=role)
        self.session.add(user)
        return user

    def list_users(self) -> list[User]:
        return list(self.session.scalars(select(User)))

    def log_activity(self, user_id: Optional[int], action: str, details: Optional[str] = None) -> ActivityLog:
        log = ActivityLog(user_id=user_id, action=action, details=details)
        self.session.add(log)
        return log

    def activity_feed(self, limit: int = 100) -> list[ActivityLog]:
        stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
        return list(self.session.scalars(stmt))


__all__ = ["UserService"]
