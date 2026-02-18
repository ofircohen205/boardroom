# backend/services/auth/exceptions.py
"""Authentication service exceptions."""

from backend.shared.core.exceptions import BoardroomError


class UserAlreadyExistsError(BoardroomError):
    """Raised when trying to register with an existing email."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InvalidCredentialsError(BoardroomError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str):
        super().__init__(message, status_code=401)
