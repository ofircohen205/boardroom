# backend/services/exceptions.py
"""Service layer exceptions hierarchy."""


class ServiceError(Exception):
    """
    Base exception for all service layer errors.

    Used as a base for domain-specific service exceptions. Services should
    raise specific subclasses of ServiceError rather than generic exceptions.
    """

    pass
