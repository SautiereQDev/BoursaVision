"""
Core exceptions for Boursa Vision application.
"""


class BoursaVisionError(Exception):
    """Base exception for Boursa Vision application."""

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(BoursaVisionError):
    """Raised when there's a configuration issue."""
    pass


class DatabaseError(BoursaVisionError):
    """Raised when there's a database-related issue."""
    pass


class ExternalServiceError(BoursaVisionError):
    """Raised when an external service fails."""
    pass


class DataValidationError(BoursaVisionError):
    """Raised when data validation fails."""
    pass


class ArchivingError(BoursaVisionError):
    """Raised when archiving operations fail."""
    pass


class RecommendationError(BoursaVisionError):
    """Raised when recommendation generation fails."""
    pass
