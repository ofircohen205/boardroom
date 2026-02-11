"""User settings service package."""
from .exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from .service import SettingsService

__all__ = [
    "EmailAlreadyTakenError",
    "InvalidPasswordError",
    "SettingsError",
    "SettingsService",
]
