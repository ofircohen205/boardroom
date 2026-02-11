# backend/services/analysis/exceptions.py
"""Analysis service exceptions."""

from backend.services.exceptions import ServiceError


class AnalysisError(ServiceError):
    """Base exception for analysis service errors."""

    pass


class AnalysisSessionNotFoundError(AnalysisError):
    """Raised when an analysis session is not found."""

    pass
