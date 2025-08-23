"""This module defines custom exception classes for the Boursa Vision application.

Each exception class inherits from the base `BoursaVisionError` class, allowing
for unified error handling throughout the application. These exceptions are
designed to represent specific error scenarios that may occur during the
operation of the application.

Classes:
    BoursaVisionError:

    PortfolioNotFoundError:
        Raised when a portfolio is not found.

    InvalidSymbolError:
        Raised when a symbol is invalid.

    PriceRangeError:
        Raised when max_price is not greater than min_price.

    FactoryProviderError:
        Raised when no factory provider is registered.

    DatabaseNotInitializedError:
        Raised when the database is not initialized.

    RateLimitError:
        Raised when a rate limit is exceeded.

    TemporaryFailureError:
        Raised for temporary failures.

    AnalysisFailedError:
        Raised when an analysis operation fails."""


class BoursaVisionError(Exception):
    """
    Base exception class for the Boursa Vision application.

    This class serves as the parent for all custom exceptions
    defined within the Boursa Vision application. It can be used
    to catch and handle errors specific to the application in a
    unified manner.

    Attributes:
        None
    """


class PortfolioNotFoundError(BoursaVisionError):
    """Raised when a portfolio is not found."""

    def __init__(self, portfolio_id):
        super().__init__(f"Portfolio {portfolio_id} not found")


class InvalidSymbolError(BoursaVisionError):
    """Raised when a symbol is invalid."""

    def __init__(self, symbol):
        super().__init__(f"Symbol '{symbol}' must be alphanumeric")


class PriceRangeError(BoursaVisionError):
    """Raised when max_price is not greater than min_price."""

    def __init__(self):
        super().__init__("max_price must be greater than min_price")


class FactoryProviderError(BoursaVisionError):
    """Raised when no factory provider is registered."""

    def __init__(self):
        super().__init__("No factory provider registered")


class DatabaseNotInitializedError(BoursaVisionError):
    """Raised when the database is not initialized."""

    def __init__(self):
        super().__init__("Database not initialized. Call initialize() first.")


class RateLimitError(BoursaVisionError):
    """Raised when a rate limit is exceeded."""

    def __init__(self, symbol):
        super().__init__(f"Rate limit exceeded for {symbol}")


class TemporaryFailureError(BoursaVisionError):
    """Raised for temporary failures."""

    def __init__(self, message):
        super().__init__(message)


class AnalysisFailedError(BoursaVisionError):
    """Raised when an analysis operation fails."""

    def __init__(self, message="Analysis failed"):
        super().__init__(message)
