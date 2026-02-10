# tests/test_email_service.py
"""Tests for email service stub (Phase 4b)."""
from unittest.mock import patch

import pytest

from backend.services.email import EmailService, get_email_service


class TestEmailService:
    """Test email service foundation."""

    def test_service_disabled_without_api_key(self):
        """Service should be disabled when no API key is configured."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()

            assert service.enabled is False

    def test_service_disabled_when_feature_flag_off(self):
        """Service should be disabled when feature flag is off."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = False
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()

            assert service.enabled is False

    def test_service_enabled_with_api_key_and_flag(self):
        """Service should be enabled when API key and feature flag are set."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()

            assert service.enabled is True

    @pytest.mark.asyncio
    async def test_price_alert_email_disabled_returns_false(self):
        """Price alert email should return False when disabled."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = ""
            mock_settings.email_notifications_enabled = False
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            result = await service.send_price_alert_email(
                to_email="user@example.com",
                ticker="AAPL",
                condition="above",
                target_value=200.0,
                current_price=205.0,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_price_alert_email_above_subject(self):
        """Price alert above should generate correct subject."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            subject = service._get_price_alert_subject("AAPL", "above", 200.0)

            assert "AAPL" in subject
            assert "200" in subject
            assert "Above" in subject

    @pytest.mark.asyncio
    async def test_price_alert_email_below_subject(self):
        """Price alert below should generate correct subject."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            subject = service._get_price_alert_subject("AAPL", "below", 150.0)

            assert "AAPL" in subject
            assert "150" in subject
            assert "Below" in subject

    @pytest.mark.asyncio
    async def test_price_alert_email_change_pct_subject(self):
        """Price alert change_pct should generate correct subject."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            subject = service._get_price_alert_subject("AAPL", "change_pct", 5.0)

            assert "AAPL" in subject
            assert "5" in subject
            assert "Changed" in subject

    @pytest.mark.asyncio
    async def test_price_alert_email_html_contains_ticker(self):
        """Price alert HTML should contain ticker."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            html = service._get_price_alert_html(
                ticker="AAPL",
                condition="above",
                target_value=200.0,
                current_price=205.0,
                market="US",
            )

            assert "AAPL" in html
            assert "205.00" in html
            assert "risen above" in html

    @pytest.mark.asyncio
    async def test_analysis_complete_email_buy_action(self):
        """Analysis complete email for BUY should be formatted correctly."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            html = service._get_analysis_complete_html("AAPL", "BUY", 0.85)

            assert "AAPL" in html
            assert "BUY" in html
            assert "85%" in html

    @pytest.mark.asyncio
    async def test_veto_alert_email_contains_reason(self):
        """Veto alert email should contain veto reason."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            html = service._get_veto_alert_html("AAPL", "High sector concentration")

            assert "AAPL" in html
            assert "VETOED" in html
            assert "High sector concentration" in html

    @pytest.mark.asyncio
    async def test_send_email_stub_returns_true(self):
        """Send email stub should return True (success)."""
        with patch("backend.services.email.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test_key"
            mock_settings.email_notifications_enabled = True
            mock_settings.sendgrid_from_email = "noreply@boardroom.app"
            mock_settings.sendgrid_from_name = "Boardroom"

            service = EmailService()
            result = await service._send_email(
                to_email="user@example.com",
                subject="Test",
                html_content="<html>Test</html>",
            )

            # Stub always returns True
            assert result is True

    def test_get_email_service_singleton(self):
        """get_email_service should return singleton instance."""
        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2
