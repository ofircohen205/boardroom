class SettingsError(Exception):
    """Base settings error."""

    pass


class EmailAlreadyTakenError(SettingsError):
    """Raised when email is already in use by another user."""

    pass


class InvalidPasswordError(SettingsError):
    """Raised when current password is incorrect."""

    pass
