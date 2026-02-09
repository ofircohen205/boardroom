# backend/core/exceptions.py
"""Base exceptions and error handlers for the application."""
from typing import Any, Dict, Optional


class BoardroomException(Exception):
    """Base exception for all Boardroom application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(BoardroomException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class AuthorizationError(BoardroomException):
    """Exception raised when a user is not authorized to perform an action."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class AuthenticationError(BoardroomException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class ValidationError(BoardroomException):
    """Exception raised when validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)
