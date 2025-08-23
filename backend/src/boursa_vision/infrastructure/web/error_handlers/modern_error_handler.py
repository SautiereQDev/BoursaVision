"""
Modern Error Handler using Python 3.13 Pattern Matching
========================================================

Demonstrates advanced Python 3.13 features:
- Pattern matching for error handling
- Structured error responses
- Type-safe error classification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel

from boursa_vision.application.exceptions import (
    BoursaVisionError,
    InvalidSymbolError,
    PortfolioNotFoundError,
    PriceRangeError,
    RateLimitError,
)


# Modern Python 3.12+ type aliases
type ErrorCode = Literal["VALIDATION", "NOT_FOUND", "RATE_LIMIT", "INTERNAL"]
type ErrorLevel = Literal["ERROR", "WARNING", "INFO"]


@dataclass(slots=True)
class ErrorDetail:
    """Enhanced error details with Python 3.13 optimization"""
    
    code: ErrorCode
    message: str
    level: ErrorLevel = "ERROR"
    error_field: str | None = None  # Renamed to avoid shadowing
    context: dict[str, Any] = field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Structured error response following API standards"""
    
    error: ErrorDetail
    request_id: str | None = None
    timestamp: str
    
    class Config:
        from_attributes = True


class ModernErrorHandler:
    """
    Python 3.13 Error Handler using Pattern Matching
    
    Features:
    - Exhaustive pattern matching for type safety
    - Structured error responses
    - Automatic HTTP status code mapping
    - Contextual error details
    """
    
    @staticmethod
    def handle_application_error(error: Exception) -> HTTPException:
        """
        Handle application errors using Python 3.13 pattern matching
        
        This demonstrates the power of structural pattern matching
        introduced in Python 3.10 and enhanced in 3.13
        """
        from datetime import datetime
        
        # Pattern matching with guard conditions and value extraction
        match error:
            # Validation errors with field extraction
            case InvalidSymbolError() as e:
                detail = ErrorDetail(
                    code="VALIDATION",
                    message=f"Invalid symbol format: {e}",
                    level="ERROR",
                    error_field="symbol",
                    context={"error_type": "symbol_validation"}
                )
                status_code = status.HTTP_400_BAD_REQUEST
                
            case PriceRangeError() as e:
                detail = ErrorDetail(
                    code="VALIDATION",
                    message=f"Invalid price range: {e}",
                    level="ERROR",
                    error_field="price_range",
                    context={"error_type": "price_validation"}
                )
                status_code = status.HTTP_400_BAD_REQUEST
                
            # Not found errors
            case PortfolioNotFoundError() as e:
                detail = ErrorDetail(
                    code="NOT_FOUND",
                    message=f"Portfolio not found: {e}",
                    level="WARNING",
                    context={"resource": "portfolio"}
                )
                status_code = status.HTTP_404_NOT_FOUND
                
            # Rate limiting
            case RateLimitError() as e:
                detail = ErrorDetail(
                    code="RATE_LIMIT",
                    message="Rate limit exceeded",
                    level="WARNING",
                    context={
                        "retry_after": getattr(e, 'retry_after', 60),
                        "error_type": "rate_limiting"
                    }
                )
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
                
            # Generic business errors
            case BoursaVisionError() as e:
                detail = ErrorDetail(
                    code="VALIDATION",
                    message=str(e),
                    level="ERROR",
                    context={"error_type": "business_rule"}
                )
                status_code = status.HTTP_400_BAD_REQUEST
                
            # System errors - catch-all
            case _:
                detail = ErrorDetail(
                    code="INTERNAL",
                    message="An internal error occurred",
                    level="ERROR",
                    context={
                        "original_error": type(error).__name__,
                        "error_type": "system"
                    }
                )
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Create structured response
        error_response = ErrorResponse(
            error=detail,
            timestamp=datetime.now().isoformat()
        )
        
        return HTTPException(
            status_code=status_code,
            detail=error_response.model_dump()
        )
    
    @staticmethod
    def create_validation_response(error_field: str, message: str) -> HTTPException:
        """Create a structured validation error response"""
        detail = ErrorDetail(
            code="VALIDATION",
            message=message,
            error_field=error_field,
            level="ERROR"
        )
        
        error_response = ErrorResponse(
            error=detail,
            timestamp=datetime.now().isoformat()
        )
        
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.model_dump()
        )
    
    @staticmethod
    def analyze_error_pattern(error: Exception) -> str:
        """
        Analyze error patterns using advanced pattern matching
        Returns categorization for monitoring/metrics
        """
        match error:
            case InvalidSymbolError() | PriceRangeError():
                return "validation.input"
                
            case PortfolioNotFoundError():
                return "business.not_found"
                
            case RateLimitError():
                return "system.rate_limit"
                
            case BoursaVisionError():
                return "business.rule_violation"
                
            case ConnectionError() | TimeoutError():
                return "system.connectivity"
                
            case _:
                return "system.unknown"


# Example usage demonstrating Python 3.13 features
async def handle_error_with_context(error: Exception, request_id: str | None = None) -> HTTPException:
    """
    Enhanced error handler with request context
    Shows modern Python 3.13 type annotations and async patterns
    """
    handler = ModernErrorHandler()
    http_error = handler.handle_application_error(error)
    
    # Add request context if available
    if request_id and isinstance(http_error.detail, dict):
        http_error.detail["request_id"] = request_id
    
    return http_error
