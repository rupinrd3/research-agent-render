"""
API Exceptions

Custom exception classes for API error handling.
"""

from fastapi import HTTPException, status


class SessionNotFoundException(HTTPException):
    """Raised when a session ID is not found."""

    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )


class SessionAlreadyCompletedException(HTTPException):
    """Raised when trying to cancel a completed session."""

    def __init__(self, session_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session already completed: {session_id}",
        )


class InvalidConfigException(HTTPException):
    """Raised when configuration is invalid."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid configuration: {detail}",
        )


class ResearchInProgressException(HTTPException):
    """Raised when trying to start research while another is in progress."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="A research session is already in progress",
        )
