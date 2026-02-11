# backend/services/analysis/service.py
"""Analysis service - manages analysis sessions and results."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Action, AgentType, Market
from backend.dao.analysis import AnalysisDAO
from backend.db.models import AgentReport, AnalysisSession, FinalDecision
from backend.services.base import BaseService

from .exceptions import AnalysisError, AnalysisSessionNotFoundError


class AnalysisService(BaseService):
    """Service for analysis session operations."""

    def __init__(self, analysis_dao: AnalysisDAO):
        """
        Initialize AnalysisService.

        Args:
            analysis_dao: DAO for analysis operations
        """
        self.analysis_dao = analysis_dao

    async def create_analysis_session(
        self,
        ticker: str,
        market: Market,
        user_id: Optional[UUID],
        db: AsyncSession,
    ) -> AnalysisSession:
        """
        Create a new analysis session.

        Args:
            ticker: Stock ticker symbol
            market: Market enum (US or TASE)
            user_id: Optional user ID for personalized analysis
            db: Database session

        Returns:
            Created AnalysisSession object

        Raises:
            AnalysisError: If creation fails
        """
        try:
            session = await self.analysis_dao.create_session(ticker, market, user_id)
            await db.commit()
            await db.refresh(session)
            return session
        except Exception as e:
            await db.rollback()
            raise AnalysisError(
                f"Failed to create analysis session for {ticker}: {e!s}"
            )

    async def save_agent_report(
        self,
        session_id: UUID,
        agent_type: AgentType,
        report_data: dict,
        db: AsyncSession,
    ) -> AgentReport:
        """
        Save an agent's report to a session.

        Args:
            session_id: Analysis session ID
            agent_type: Type of agent (fundamental, sentiment, etc.)
            report_data: Agent report data as dictionary
            db: Database session

        Returns:
            Created AgentReport object

        Raises:
            AnalysisSessionNotFoundError: If session doesn't exist
            AnalysisError: If operation fails
        """
        try:
            # Verify session exists
            session = await self.analysis_dao.get_by_id(session_id)
            if not session:
                raise AnalysisSessionNotFoundError(
                    f"Analysis session {session_id} not found"
                )

            report = await self.analysis_dao.add_report(
                session_id, agent_type, report_data
            )
            await db.commit()
            await db.refresh(report)
            return report
        except AnalysisSessionNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise AnalysisError(
                f"Failed to save {agent_type} report for session {session_id}: {e!s}"
            )

    async def save_final_decision(
        self,
        session_id: UUID,
        action: Action,
        confidence: float,
        rationale: str,
        vetoed: bool = False,
        veto_reason: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> FinalDecision:
        """
        Save the final trading decision for a session.

        Args:
            session_id: Analysis session ID
            action: Final action (BUY, SELL, HOLD)
            confidence: Confidence score (0-1)
            rationale: Text explanation of decision
            vetoed: Whether decision was vetoed by risk manager
            veto_reason: Reason for veto if applicable
            db: Database session

        Returns:
            Created FinalDecision object

        Raises:
            AnalysisSessionNotFoundError: If session doesn't exist
            AnalysisError: If operation fails
        """
        try:
            # Verify session exists
            session = await self.analysis_dao.get_by_id(session_id)
            if not session:
                raise AnalysisSessionNotFoundError(
                    f"Analysis session {session_id} not found"
                )

            decision = await self.analysis_dao.add_decision(
                session_id=session_id,
                action=action,
                confidence=confidence,
                rationale=rationale,
                vetoed=vetoed,
                veto_reason=veto_reason,
            )

            if db:
                await db.commit()
                await db.refresh(decision)

            return decision
        except AnalysisSessionNotFoundError:
            raise
        except Exception as e:
            if db:
                await db.rollback()
            raise AnalysisError(
                f"Failed to save final decision for session {session_id}: {e!s}"
            )

    async def get_analysis_session(self, session_id: UUID) -> AnalysisSession:
        """
        Get a specific analysis session.

        Args:
            session_id: Analysis session ID

        Returns:
            AnalysisSession object

        Raises:
            AnalysisSessionNotFoundError: If session doesn't exist
            AnalysisError: If operation fails
        """
        try:
            session = await self.analysis_dao.get_by_id(session_id)
            if not session:
                raise AnalysisSessionNotFoundError(
                    f"Analysis session {session_id} not found"
                )
            return session
        except AnalysisSessionNotFoundError:
            raise
        except Exception as e:
            raise AnalysisError(f"Failed to fetch analysis session {session_id}: {e!s}")

    async def get_user_analysis_history(
        self, user_id: UUID, limit: int = 50
    ) -> List[AnalysisSession]:
        """
        Get analysis history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of sessions to return

        Returns:
            List of AnalysisSession objects

        Raises:
            AnalysisError: If operation fails
        """
        try:
            return await self.analysis_dao.get_user_sessions(user_id, limit)
        except Exception as e:
            raise AnalysisError(
                f"Failed to fetch analysis history for user {user_id}: {e!s}"
            )

    async def get_recent_outcomes(self, limit: int = 50) -> List[AnalysisSession]:
        """
        Get recent analysis outcomes.

        Args:
            limit: Maximum number of outcomes to return

        Returns:
            List of recent AnalysisSession objects

        Raises:
            AnalysisError: If operation fails
        """
        try:
            return await self.analysis_dao.get_recent_outcomes(limit)
        except Exception as e:
            raise AnalysisError(f"Failed to fetch recent outcomes: {e!s}")
