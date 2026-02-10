"""User settings service package."""
from .service import (
    SettingsService,
    update_profile,
    change_password,
    get_api_keys_masked,
    upsert_api_key,
    delete_api_key,
)
from .exceptions import (
    SettingsError,
    EmailAlreadyTakenError,
    InvalidPasswordError,
)

__all__ = [
    "SettingsService",
    "update_profile",
    "change_password",
    "get_api_keys_masked",
    "upsert_api_key",
    "delete_api_key",
    "SettingsError",
    "EmailAlreadyTakenError",
    "InvalidPasswordError",
]
