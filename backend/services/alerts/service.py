# backend/services/alerts/service.py
"""Business logic for alerts and notifications."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.core.logging import get_logger
from backend.dao.alerts import NotificationDAO, PriceAlertDAO
from backend.db.models import AlertCondition, Notification, NotificationType, PriceAlert
from backend.services.base import BaseService

logger = get_logger(__name__)

# Business rules
MAX_ALERTS_PER_USER = 50
ALERT_COOLDOWN_MINUTES = 60


class AlertValidationError(Exception):
    """Raised when alert validation fails."""

    pass


class AlertService(BaseService):
    """Service for alert and notification operations."""

    def __init__(
        self, price_alert_dao: PriceAlertDAO, notification_dao: NotificationDAO
    ):
        """
        Initialize AlertService.

        Args:
            price_alert_dao: DAO for price alert operations
            notification_dao: DAO for notification operations
        """
        self.price_alert_dao = price_alert_dao
        self.notification_dao = notification_dao

    async def create_price_alert(
        self,
        db: AsyncSession,
        user_id: UUID,
        ticker: str,
        market: Market,
        condition: AlertCondition,
        target_value: float,
    ) -> PriceAlert:
        """
        Create a new price alert for a user.

        Args:
            db: Database session
            user_id: User ID
            ticker: Stock ticker symbol
            market: Market enum
            condition: Alert condition (above/below/change_pct)
            target_value: Target price or percentage

        Returns:
            Created PriceAlert

        Raises:
            AlertValidationError: If validation fails
        """
        # Rate limiting: max 50 alerts per user
        alert_count = await self.price_alert_dao.count_user_alerts(user_id)
        if alert_count >= MAX_ALERTS_PER_USER:
            raise AlertValidationError(
                f"Maximum {MAX_ALERTS_PER_USER} alerts per user exceeded"
            )

        # Validate target value
        if target_value <= 0:
            raise AlertValidationError("Target value must be greater than 0")

        if condition == AlertCondition.CHANGE_PCT:
            if target_value < 0.1 or target_value > 100:
                raise AlertValidationError(
                    "Change percentage must be between 0.1 and 100"
                )

        # Fetch baseline price for change_pct alerts
        baseline_price = None
        if condition == AlertCondition.CHANGE_PCT:
            try:
                from backend.ai.tools.market_data import get_market_data_client

                market_data_client = get_market_data_client()
                stock_data = await market_data_client.get_stock_data(
                    ticker.upper(), market
                )
                baseline_price = stock_data.get("current_price")
                logger.info(f"Fetched baseline price for {ticker}: ${baseline_price}")
            except Exception as e:
                logger.warning(f"Failed to fetch baseline price for {ticker}: {e}")
                # Continue without baseline - alert won't trigger until baseline is set

        # Create alert
        alert = await self.price_alert_dao.create(
            user_id=user_id,
            ticker=ticker.upper(),
            market=market,
            condition=condition,
            target_value=target_value,
            baseline_price=baseline_price,
            triggered=False,
            active=True,
        )

        logger.info(
            f"Created price alert {alert.id} for user {user_id}: {ticker} {condition.value} {target_value} (baseline: {baseline_price})"
        )
        return alert

    async def trigger_alert(
        self, db: AsyncSession, alert: PriceAlert, current_price: float
    ) -> Notification:
        """
        Trigger an alert and create a notification.

        Implements notification grouping: if a similar notification for the same ticker
        exists within the last 15 minutes, updates that notification instead of creating
        a new one to prevent spam.

        Args:
            db: Database session
            alert: PriceAlert to trigger
            current_price: Current stock price that triggered the alert

        Returns:
            Created or updated Notification
        """
        # Local import to ensure availability in test context
        from datetime import datetime, timedelta

        # Update alert status
        alert.triggered = True
        alert.triggered_at = datetime.now()
        alert.cooldown_until = datetime.now() + timedelta(
            minutes=ALERT_COOLDOWN_MINUTES
        )
        await self.price_alert_dao.update(alert)

        # Check for recent notification to group with (within 15 minutes)
        recent_notification = await self.notification_dao.find_recent_by_ticker(
            user_id=alert.user_id,
            notification_type=NotificationType.PRICE_ALERT,
            ticker=alert.ticker,
            minutes=15,
        )

        if recent_notification:
            # Update existing notification (grouping)
            grouped_count = recent_notification.data.get("grouped_count", 1) + 1

            # Update title and body to show grouped count
            if alert.condition == AlertCondition.ABOVE:
                title = f"{alert.ticker} Above ${alert.target_value} ({grouped_count}x)"
                body = f"{alert.ticker} has triggered {grouped_count} alerts. Latest: ${current_price:.2f}"
            elif alert.condition == AlertCondition.BELOW:
                title = f"{alert.ticker} Below ${alert.target_value} ({grouped_count}x)"
                body = f"{alert.ticker} has triggered {grouped_count} alerts. Latest: ${current_price:.2f}"
            else:  # CHANGE_PCT
                title = f"{alert.ticker} Changed by {alert.target_value}% ({grouped_count}x)"
                body = f"{alert.ticker} has triggered {grouped_count} alerts. Latest: ${current_price:.2f}"

            # Update notification
            recent_notification.title = title
            recent_notification.body = body
            recent_notification.data = {
                **recent_notification.data,
                "current_price": current_price,
                "grouped_count": grouped_count,
                "last_alert_id": str(alert.id),
                "last_updated": datetime.now().isoformat(),
            }
            recent_notification.read = False  # Mark as unread again
            recent_notification.created_at = (
                datetime.now()
            )  # Update timestamp to show recent

            notification = await self.notification_dao.update(recent_notification)
            logger.info(
                f"Grouped alert {alert.id} into notification {notification.id} (count: {grouped_count})"
            )

        else:
            # Create new notification (no recent one to group with)
            # Format notification message based on condition
            if alert.condition == AlertCondition.ABOVE:
                title = f"{alert.ticker} Above ${alert.target_value}"
                body = f"{alert.ticker} has risen above ${alert.target_value:.2f}. Current price: ${current_price:.2f}"
            elif alert.condition == AlertCondition.BELOW:
                title = f"{alert.ticker} Below ${alert.target_value}"
                body = f"{alert.ticker} has fallen below ${alert.target_value:.2f}. Current price: ${current_price:.2f}"
            else:  # CHANGE_PCT
                title = f"{alert.ticker} Changed by {alert.target_value}%"
                body = f"{alert.ticker} has changed by {alert.target_value}% or more. Current price: ${current_price:.2f}"

            notification = await self.notification_dao.create(
                user_id=alert.user_id,
                type=NotificationType.PRICE_ALERT,
                title=title,
                body=body,
                data={
                    "ticker": alert.ticker,
                    "market": alert.market.value,
                    "condition": alert.condition.value,
                    "target_value": alert.target_value,
                    "current_price": current_price,
                    "alert_id": str(alert.id),
                    "grouped_count": 1,
                },
                read=False,
            )
            logger.info(
                f"Triggered alert {alert.id} and created notification {notification.id}"
            )

        # Send WebSocket notification to all user's connections
        try:
            # Lazy import to avoid circular dependency
            from backend.api.websocket.connection_manager import connection_manager

            await connection_manager.send_notification(
                user_id=alert.user_id,
                notification={
                    "id": str(notification.id),
                    "type": notification.type.value,
                    "title": notification.title,
                    "body": notification.body,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                },
            )
            logger.debug(f"WebSocket notification sent for alert {alert.id}")
        except Exception as e:
            logger.error(
                f"Failed to send WebSocket notification for alert {alert.id}: {e}"
            )
            # Don't fail the whole operation if WebSocket fails

        return notification

    async def create_analysis_notification(
        self,
        db: AsyncSession,
        user_id: UUID,
        ticker: str,
        action: str,
        confidence: float,
        vetoed: bool = False,
        veto_reason: str | None = None,
    ) -> Notification:
        """
        Create a notification for completed scheduled analysis.

        Args:
            db: Database session
            user_id: User ID
            ticker: Stock ticker
            action: BUY/SELL/HOLD
            confidence: Confidence score
            vetoed: Whether the decision was vetoed
            veto_reason: Veto reason if vetoed

        Returns:
            Created Notification
        """
        if vetoed:
            title = f"{ticker} Analysis Complete - VETOED"
            body = f"Analysis for {ticker} was vetoed by Risk Manager. Reason: {veto_reason}"
            notification_type = NotificationType.VETO_ALERT
        else:
            title = f"{ticker} Analysis Complete - {action}"
            body = f"Recommendation: {action} {ticker} (Confidence: {confidence:.0%})"
            notification_type = NotificationType.ANALYSIS_COMPLETE

        notification = await self.notification_dao.create(
            user_id=user_id,
            type=notification_type,
            title=title,
            body=body,
            data={
                "ticker": ticker,
                "action": action,
                "confidence": confidence,
                "vetoed": vetoed,
                "veto_reason": veto_reason,
            },
            read=False,
        )

        # Send WebSocket notification
        try:
            # Lazy import to avoid circular dependency
            from backend.api.websocket.connection_manager import connection_manager

            await connection_manager.send_notification(
                user_id=user_id,
                notification={
                    "id": str(notification.id),
                    "type": notification.type.value,
                    "title": notification.title,
                    "body": notification.body,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")

        return notification
