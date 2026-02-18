# backend/dao/alerts.py
"""Data Access Objects for alerts and notifications."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Market
from backend.shared.db.models import (
    AlertFrequency,
    Notification,
    NotificationType,
    PriceAlert,
    ScheduledAnalysis,
)

from .base import BaseDAO


class PriceAlertDAO(BaseDAO[PriceAlert]):
    """DAO for price alert operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PriceAlert)

    async def get_user_alerts(
        self, user_id: UUID, active_only: bool = True
    ) -> list[PriceAlert]:
        """
        Get all alerts for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active alerts

        Returns:
            List of PriceAlert objects
        """
        query = select(PriceAlert).where(PriceAlert.user_id == user_id)

        if active_only:
            query = query.where(PriceAlert.active)

        query = query.order_by(PriceAlert.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_alerts_for_ticker(
        self, ticker: str, market: Market
    ) -> list[PriceAlert]:
        """
        Get all active, non-triggered alerts for a specific ticker.
        Filters out alerts that are in cooldown period.

        Args:
            ticker: Stock ticker symbol
            market: Market enum (US or TASE)

        Returns:
            List of PriceAlert objects ready to be checked
        """
        now = datetime.now()

        query = select(PriceAlert).where(
            and_(
                PriceAlert.ticker == ticker,
                PriceAlert.market == market,
                PriceAlert.active,
                ~PriceAlert.triggered,
                or_(
                    PriceAlert.cooldown_until.is_(None),
                    PriceAlert.cooldown_until <= now,
                ),
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_active_tickers(self) -> list[tuple[str, Market]]:
        """
        Get unique (ticker, market) pairs for all active alerts.
        Used by the alert checker job to batch fetch prices.

        Returns:
            List of (ticker, market) tuples
        """
        now = datetime.now()

        query = (
            select(PriceAlert.ticker, PriceAlert.market)
            .where(
                and_(
                    PriceAlert.active,
                    ~PriceAlert.triggered,
                    or_(
                        PriceAlert.cooldown_until.is_(None),
                        PriceAlert.cooldown_until <= now,
                    ),
                )
            )
            .distinct()
        )

        result = await self.session.execute(query)
        return list(result.all())

    async def reset_alert(self, alert_id: UUID) -> Optional[PriceAlert]:
        """
        Reset a triggered alert to re-enable it.

        Args:
            alert_id: Alert ID to reset

        Returns:
            Updated PriceAlert or None if not found
        """
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None

        alert.triggered = False
        alert.triggered_at = None
        alert.cooldown_until = None

        return await self.update(alert)

    async def count_user_alerts(self, user_id: UUID) -> int:
        """
        Count total alerts for a user (for rate limiting).

        Args:
            user_id: User ID

        Returns:
            Count of alerts
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(PriceAlert)
            .where(PriceAlert.user_id == user_id)
        )
        return result.scalar() or 0


class NotificationDAO(BaseDAO[Notification]):
    """DAO for notification operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def get_user_notifications(
        self, user_id: UUID, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return

        Returns:
            List of Notification objects
        """
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(not Notification.read)

        query = query.order_by(Notification.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(and_(Notification.user_id == user_id, not Notification.read))
        )
        return result.scalar() or 0

    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID

        Returns:
            Updated Notification or None if not found
        """
        notification = await self.get_by_id(notification_id)
        if not notification:
            return None

        notification.read = True
        return await self.update(notification)

    async def mark_all_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User ID

        Returns:
            Number of notifications marked as read
        """

        result = await self.session.execute(
            update(Notification)
            .where(and_(Notification.user_id == user_id, not Notification.read))
            .values(read=True)
        )
        await self.session.flush()
        return result.rowcount or 0

    async def find_recent_by_ticker(
        self,
        user_id: UUID,
        notification_type: "NotificationType",
        ticker: str,
        minutes: int = 15,
    ) -> Optional[Notification]:
        """
        Find a recent notification for the same ticker within a time window.
        Used for notification grouping to prevent spam.

        Args:
            user_id: User ID
            notification_type: Notification type
            ticker: Stock ticker
            minutes: Time window in minutes (default 15)

        Returns:
            Most recent matching Notification or None
        """
        from sqlalchemy import String, cast

        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        query = (
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.type == notification_type,
                    cast(Notification.data["ticker"], String) == ticker,
                    Notification.created_at >= cutoff_time,
                )
            )
            .order_by(Notification.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ScheduledAnalysisDAO(BaseDAO[ScheduledAnalysis]):
    """DAO for scheduled analysis operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ScheduledAnalysis)

    async def get_user_schedules(self, user_id: UUID) -> list[ScheduledAnalysis]:
        """
        Get all schedules for a user.

        Args:
            user_id: User ID

        Returns:
            List of ScheduledAnalysis objects
        """
        query = (
            select(ScheduledAnalysis)
            .where(ScheduledAnalysis.user_id == user_id)
            .order_by(ScheduledAnalysis.created_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_due_schedules(self) -> list[ScheduledAnalysis]:
        """
        Get all schedules that are due to run.
        Filters by active=True and next_run <= now.

        Returns:
            List of ScheduledAnalysis objects ready to run
        """
        now = datetime.now()

        query = select(ScheduledAnalysis).where(
            and_(
                ScheduledAnalysis.active,
                ScheduledAnalysis.next_run is not None,
                ScheduledAnalysis.next_run <= now,
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_run_times(
        self, schedule_id: UUID, last_run: datetime, next_run: datetime
    ) -> Optional[ScheduledAnalysis]:
        """
        Update the last_run and next_run times for a schedule.

        Args:
            schedule_id: Schedule ID
            last_run: Timestamp of last run
            next_run: Timestamp of next scheduled run

        Returns:
            Updated ScheduledAnalysis or None if not found
        """
        schedule = await self.get_by_id(schedule_id)
        if not schedule:
            return None

        schedule.last_run = last_run
        schedule.next_run = next_run

        return await self.update(schedule)

    async def count_user_schedules(self, user_id: UUID) -> int:
        """
        Count total schedules for a user (for rate limiting).

        Args:
            user_id: User ID

        Returns:
            Count of schedules
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(ScheduledAnalysis)
            .where(ScheduledAnalysis.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_by_ticker_market_frequency(
        self, user_id: UUID, ticker: str, market: Market, frequency: AlertFrequency
    ) -> Optional[ScheduledAnalysis]:
        """
        Get a schedule by ticker, market, and frequency for a user.
        Used to check for duplicates before creation.

        Args:
            user_id: User ID
            ticker: Stock ticker
            market: Market enum
            frequency: Schedule frequency enum

        Returns:
            ScheduledAnalysis if found, None otherwise
        """
        query = select(ScheduledAnalysis).where(
            and_(
                ScheduledAnalysis.user_id == user_id,
                ScheduledAnalysis.ticker == ticker.upper(),
                ScheduledAnalysis.market == market,
                ScheduledAnalysis.frequency == frequency,
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()
