"""Unit tests for backend.shared.core.exceptions."""

import pytest

from backend.shared.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BoardroomError,
    NotFoundError,
    ValidationError,
)


class TestBoardroomError:
    def test_default_values(self):
        err = BoardroomError("Something went wrong")
        assert err.message == "Something went wrong"
        assert err.status_code == 500
        assert err.details == {}
        assert str(err) == "Something went wrong"

    def test_custom_status_code(self):
        err = BoardroomError("Bad request", status_code=400)
        assert err.status_code == 400

    def test_custom_details(self):
        err = BoardroomError("error", details={"field": "ticker"})
        assert err.details == {"field": "ticker"}

    def test_none_details_becomes_empty_dict(self):
        err = BoardroomError("error", details=None)
        assert err.details == {}

    def test_is_exception(self):
        err = BoardroomError("error")
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(BoardroomError) as exc_info:
            raise BoardroomError("fail", status_code=500, details={"key": "value"})
        assert exc_info.value.status_code == 500
        assert exc_info.value.details == {"key": "value"}


class TestNotFoundError:
    def test_status_code_is_404(self):
        err = NotFoundError("Resource not found")
        assert err.status_code == 404
        assert err.message == "Resource not found"

    def test_inherits_from_boardroom_error(self):
        err = NotFoundError("not found")
        assert isinstance(err, BoardroomError)

    def test_details_forwarded(self):
        err = NotFoundError("not found", details={"id": "abc"})
        assert err.details == {"id": "abc"}

    def test_can_be_raised(self):
        with pytest.raises(NotFoundError):
            raise NotFoundError("ticker AAPL not found")


class TestAuthorizationError:
    def test_status_code_is_403(self):
        err = AuthorizationError("Forbidden")
        assert err.status_code == 403

    def test_inherits_from_boardroom_error(self):
        assert isinstance(AuthorizationError("x"), BoardroomError)

    def test_details_forwarded(self):
        err = AuthorizationError("forbidden", details={"required_role": "admin"})
        assert err.details == {"required_role": "admin"}


class TestAuthenticationError:
    def test_status_code_is_401(self):
        err = AuthenticationError("Unauthorized")
        assert err.status_code == 401

    def test_inherits_from_boardroom_error(self):
        assert isinstance(AuthenticationError("x"), BoardroomError)

    def test_details_forwarded(self):
        err = AuthenticationError("bad token", details={"token": "expired"})
        assert err.details == {"token": "expired"}

    def test_can_be_raised(self):
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("invalid credentials")


class TestValidationError:
    def test_status_code_is_422(self):
        err = ValidationError("Invalid input")
        assert err.status_code == 422

    def test_inherits_from_boardroom_error(self):
        assert isinstance(ValidationError("x"), BoardroomError)

    def test_details_forwarded(self):
        err = ValidationError(
            "bad field", details={"field": "email", "reason": "invalid"}
        )
        assert err.details == {"field": "email", "reason": "invalid"}

    def test_can_be_raised_and_caught_as_boardroom_error(self):
        with pytest.raises(BoardroomError):
            raise ValidationError("bad data")
