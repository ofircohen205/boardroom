"""User settings service package."""
from .exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from .service import (
    SettingsService,
    change_password,
    delete_api_key,
    get_api_keys_masked,
    update_profile,
    upsert_api_key,
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
