# backend/services/notifications/email_service.py
"""Email notification service using SendGrid."""

from typing import Optional

from backend.shared.core.logging import get_logger
from backend.shared.core.settings import settings

logger = get_logger(__name__)


class EmailService:
    """
    Email service for sending notifications via SendGrid.

    This is a foundation stub for Phase 4b. Full implementation with actual
    SendGrid integration will be completed in a future phase.
    """

    def __init__(self):
        self.api_key = settings.sendgrid_api_key.get_secret_value()
        self.from_email = settings.sendgrid_from_email
        self.from_name = settings.sendgrid_from_name
        self.enabled = settings.email_notifications_enabled and bool(self.api_key)

        if not self.enabled:
            logger.info("Email notifications disabled (no API key or feature flag off)")

    async def send_price_alert_email(
        self,
        to_email: str,
        ticker: str,
        condition: str,
        target_value: float,
        current_price: float,
        market: str = "US",
    ) -> bool:
        """
        Send price alert notification email.

        Args:
            to_email: Recipient email address
            ticker: Stock ticker
            condition: Alert condition (above/below/change_pct)
            target_value: Target value
            current_price: Current stock price
            market: Market (US/TASE)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(
                f"Email notifications disabled, skipping price alert email for {ticker}"
            )
            return False

        subject = self._get_price_alert_subject(ticker, condition, target_value)
        html_content = self._get_price_alert_html(
            ticker=ticker,
            condition=condition,
            target_value=target_value,
            current_price=current_price,
            market=market,
        )

        return await self._send_email(to_email, subject, html_content)

    async def send_analysis_complete_email(
        self,
        to_email: str,
        ticker: str,
        action: str,
        confidence: float,
        vetoed: bool = False,
        veto_reason: Optional[str] = None,
    ) -> bool:
        """
        Send scheduled analysis completion notification email.

        Args:
            to_email: Recipient email address
            ticker: Stock ticker
            action: Recommended action (BUY/SELL/HOLD)
            confidence: Confidence score (0-1)
            vetoed: Whether decision was vetoed
            veto_reason: Veto reason if vetoed

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(
                f"Email notifications disabled, skipping analysis email for {ticker}"
            )
            return False

        if vetoed:
            subject = f"Analysis Complete: {ticker} - VETOED"
            html_content = self._get_veto_alert_html(ticker, veto_reason)
        else:
            subject = f"Analysis Complete: {ticker} - {action}"
            html_content = self._get_analysis_complete_html(ticker, action, confidence)

        return await self._send_email(to_email, subject, html_content)

    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send email via SendGrid.

        This is a stub implementation. Future implementation will use:
        - sendgrid.SendGridAPIClient
        - sendgrid.helpers.mail import Mail

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body

        Returns:
            True if sent successfully, False otherwise
        """
        # TODO: Implement actual SendGrid integration
        # For now, just log the email details
        logger.info(
            f"[EMAIL STUB] Would send email to {to_email}\n"
            f"Subject: {subject}\n"
            f"Content preview: {html_content[:100]}..."
        )

        # In production, this would be:
        # try:
        #     from sendgrid import SendGridAPIClient
        #     from sendgrid.helpers.mail import Mail
        #
        #     message = Mail(
        #         from_email=(self.from_email, self.from_name),
        #         to_emails=to_email,
        #         subject=subject,
        #         html_content=html_content
        #     )
        #     sg = SendGridAPIClient(self.api_key)
        #     response = sg.send(message)
        #     logger.info(f"Email sent successfully to {to_email}: {response.status_code}")
        #     return response.status_code in [200, 201, 202]
        # except Exception as e:
        #     logger.error(f"Failed to send email to {to_email}: {e}")
        #     return False

        return True  # Stub always returns success

    def _get_price_alert_subject(
        self, ticker: str, condition: str, target_value: float
    ) -> str:
        """Generate email subject for price alert."""
        if condition == "above":
            return f"🔔 {ticker} Above ${target_value}"
        elif condition == "below":
            return f"🔔 {ticker} Below ${target_value}"
        else:  # change_pct
            return f"🔔 {ticker} Changed by {target_value}%"

    def _get_price_alert_html(
        self,
        ticker: str,
        condition: str,
        target_value: float,
        current_price: float,
        market: str,
    ) -> str:
        """Generate HTML email template for price alert."""
        condition_text = {
            "above": f"risen above ${target_value:.2f}",
            "below": f"fallen below ${target_value:.2f}",
            "change_pct": f"changed by {target_value}% or more",
        }.get(condition, "triggered an alert")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .ticker {{ font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
                .price {{ font-size: 24px; color: #10b981; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Boardroom Alert</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Price Alert Triggered</p>
                </div>
                <div class="content">
                    <div class="ticker">{ticker} ({market})</div>
                    <p style="font-size: 16px; color: #374151;">
                        {ticker} has <strong>{condition_text}</strong>.
                    </p>
                    <div class="price">Current Price: ${current_price:.2f}</div>
                    <a href="https://boardroom.app/analyze/{ticker}" class="button">View Analysis</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Boardroom.</p>
                    <p>To manage your alerts, visit your <a href="https://boardroom.app/alerts">alerts dashboard</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_analysis_complete_html(
        self, ticker: str, action: str, confidence: float
    ) -> str:
        """Generate HTML email template for analysis completion."""
        action_colors = {"BUY": "#10b981", "SELL": "#ef4444", "HOLD": "#f59e0b"}
        action_color = action_colors.get(action, "#6b7280")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .ticker {{ font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
                .action {{ font-size: 36px; font-weight: bold; color: {action_color}; margin: 20px 0; }}
                .confidence {{ font-size: 18px; color: #6b7280; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">Boardroom Analysis</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Scheduled Analysis Complete</p>
                </div>
                <div class="content">
                    <div class="ticker">{ticker}</div>
                    <div class="action">{action}</div>
                    <div class="confidence">Confidence: {confidence:.0%}</div>
                    <p style="margin-top: 20px; color: #374151;">
                        Your scheduled analysis for {ticker} is complete. Our AI agents have analyzed fundamentals,
                        sentiment, technical indicators, and risk factors to provide this recommendation.
                    </p>
                    <a href="https://boardroom.app/analyze/{ticker}" class="button">View Full Report</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Boardroom.</p>
                    <p>To manage your schedules, visit your <a href="https://boardroom.app/schedules">schedules dashboard</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_veto_alert_html(self, ticker: str, veto_reason: Optional[str]) -> str:
        """Generate HTML email template for veto alert."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
                .ticker {{ font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
                .veto {{ font-size: 36px; font-weight: bold; color: #dc2626; margin: 20px 0; }}
                .reason {{ background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">⚠️ Boardroom Alert</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Analysis Vetoed</p>
                </div>
                <div class="content">
                    <div class="ticker">{ticker}</div>
                    <div class="veto">VETOED</div>
                    <p style="color: #374151;">
                        Your scheduled analysis for {ticker} was vetoed by the Risk Manager.
                    </p>
                    <div class="reason">
                        <strong>Reason:</strong><br>
                        {veto_reason or "Risk assessment detected concerning factors."}
                    </div>
                    <a href="https://boardroom.app/analyze/{ticker}" class="button">View Details</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from Boardroom.</p>
                </div>
            </div>
        </body>
        </html>
        """
