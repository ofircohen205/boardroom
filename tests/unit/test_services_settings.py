# tests/unit/test_services_settings.py
"""Unit tests for SettingsService."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.domains.settings.services.exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from backend.domains.settings.services.service import SettingsService
from backend.shared.core.security import get_password_hash

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user_dao():
    dao = MagicMock()
    dao.get_by_id = AsyncMock()
    dao.find_by_email = AsyncMock(return_value=None)
    return dao


@pytest.fixture
def settings_service(mock_user_dao):
    return SettingsService(mock_user_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.password_hash = get_password_hash(
        "correctpassword"
    )  # pragma: allowlist secret
    user.created_at = None
    return user


# ---------------------------------------------------------------------------
# update_profile tests
# ---------------------------------------------------------------------------


class TestUpdateProfile:
    """Tests for SettingsService.update_profile."""

    async def test_update_profile_success(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """User found; first_name and last_name updated; db flushed, refreshed, committed; dict returned."""
        mock_user_dao.get_by_id.return_value = sample_user

        result = await settings_service.update_profile(
            user_id=sample_user.id,
            db=mock_db,
            first_name="NewFirst",
            last_name="NewLast",
        )

        assert sample_user.first_name == "NewFirst"
        assert sample_user.last_name == "NewLast"
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(sample_user)
        mock_db.commit.assert_awaited_once()

        assert result["id"] == str(sample_user.id)
        assert result["email"] == sample_user.email
        assert result["first_name"] == sample_user.first_name
        assert result["last_name"] == sample_user.last_name
        assert "created_at" in result

    async def test_update_profile_user_not_found(
        self, settings_service, mock_user_dao, mock_db
    ):
        """get_by_id returns None → SettingsError('User not found')."""
        mock_user_dao.get_by_id.return_value = None

        with pytest.raises(SettingsError, match="User not found"):
            await settings_service.update_profile(
                user_id=uuid4(),
                db=mock_db,
                first_name="Any",
            )

        mock_db.flush.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_update_profile_email_already_taken(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """Email differs from user's current email and is taken → EmailAlreadyTakenError."""
        mock_user_dao.get_by_id.return_value = sample_user
        other_user = MagicMock()
        other_user.id = uuid4()
        mock_user_dao.find_by_email.return_value = other_user

        with pytest.raises(EmailAlreadyTakenError):
            await settings_service.update_profile(
                user_id=sample_user.id,
                db=mock_db,
                email="taken@example.com",
            )

        mock_user_dao.find_by_email.assert_awaited_once_with("taken@example.com")
        mock_db.flush.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_update_profile_same_email_no_conflict(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """Email equals user's current email → find_by_email NOT called, no error."""
        mock_user_dao.get_by_id.return_value = sample_user

        result = await settings_service.update_profile(
            user_id=sample_user.id,
            db=mock_db,
            email=sample_user.email,  # same email — should not trigger conflict check
        )

        mock_user_dao.find_by_email.assert_not_awaited()
        assert result["email"] == sample_user.email
        mock_db.commit.assert_awaited_once()

    async def test_update_profile_only_last_name(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """Updating only last_name leaves first_name unchanged."""
        original_first_name = sample_user.first_name
        mock_user_dao.get_by_id.return_value = sample_user

        result = await settings_service.update_profile(
            user_id=sample_user.id,
            db=mock_db,
            last_name="OnlyLastChanged",
        )

        assert sample_user.last_name == "OnlyLastChanged"
        # first_name was not passed as non-None, so mock attribute should remain unchanged
        assert sample_user.first_name == original_first_name
        assert result["last_name"] == sample_user.last_name

    async def test_update_profile_none_fields_skipped(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """None values for first_name/last_name must not overwrite existing values."""
        mock_user_dao.get_by_id.return_value = sample_user
        original_first = sample_user.first_name
        original_last = sample_user.last_name

        # Explicitly pass None — service should skip assignment
        await settings_service.update_profile(
            user_id=sample_user.id,
            db=mock_db,
            first_name=None,
            last_name=None,
        )

        # The mock attributes should not have been set to None
        assert sample_user.first_name == original_first
        assert sample_user.last_name == original_last

    async def test_update_profile_new_email_accepted(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """New email that is not taken → user.email updated, no error raised."""
        mock_user_dao.get_by_id.return_value = sample_user
        mock_user_dao.find_by_email.return_value = None  # email available

        result = await settings_service.update_profile(
            user_id=sample_user.id,
            db=mock_db,
            email="new@example.com",
        )

        assert sample_user.email == "new@example.com"
        mock_user_dao.find_by_email.assert_awaited_once_with("new@example.com")
        assert result["email"] == "new@example.com"
        mock_db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# change_password tests
# ---------------------------------------------------------------------------


class TestChangePassword:
    """Tests for SettingsService.change_password."""

    async def test_change_password_success(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """Correct current password → hash updated, flush+commit called."""
        mock_user_dao.get_by_id.return_value = sample_user
        old_hash = sample_user.password_hash

        await settings_service.change_password(
            user_id=sample_user.id,
            current_password="correctpassword",  # pragma: allowlist secret
            new_password="newpassword123",  # pragma: allowlist secret
            db=mock_db,
        )

        # password_hash must have been replaced with a new hash
        assert sample_user.password_hash != old_hash
        mock_db.flush.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    async def test_change_password_user_not_found(
        self, settings_service, mock_user_dao, mock_db
    ):
        """get_by_id returns None → SettingsError('User not found')."""
        mock_user_dao.get_by_id.return_value = None

        with pytest.raises(SettingsError, match="User not found"):
            await settings_service.change_password(
                user_id=uuid4(),
                current_password="any",  # pragma: allowlist secret
                new_password="any",  # pragma: allowlist secret
                db=mock_db,
            )

        mock_db.flush.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_change_password_wrong_current_password(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """Wrong current password → InvalidPasswordError('Current password is incorrect')."""
        mock_user_dao.get_by_id.return_value = sample_user

        with pytest.raises(InvalidPasswordError, match="Current password is incorrect"):
            await settings_service.change_password(
                user_id=sample_user.id,
                current_password="wrongpassword",  # pragma: allowlist secret
                new_password="newpassword123",  # pragma: allowlist secret
                db=mock_db,
            )

        mock_db.flush.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_change_password_new_hash_is_valid(
        self, settings_service, mock_user_dao, mock_db, sample_user
    ):
        """After successful change, stored hash can verify the new password."""
        from backend.shared.core.security import verify_password

        mock_user_dao.get_by_id.return_value = sample_user

        await settings_service.change_password(
            user_id=sample_user.id,
            current_password="correctpassword",  # pragma: allowlist secret
            new_password="mynewsecret",  # pragma: allowlist secret
            db=mock_db,
        )

        assert verify_password(
            "mynewsecret", sample_user.password_hash
        )  # pragma: allowlist secret
