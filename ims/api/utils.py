"""Utility helpers for API responses."""
from __future__ import annotations

from fastapi import HTTPException, status


def map_service_error(error: ValueError) -> HTTPException:
    """Map a ValueError raised by the service layer to an HTTPException."""
    message = str(error)
    status_code = status.HTTP_400_BAD_REQUEST
    if "not found" in message.lower():
        status_code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=status_code, detail=message)


