"""
Global error handlers for the API
"""
import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog

from application.exceptions import (
    BoursaVisionError,
    PortfolioNotFoundError,
    InvalidSymbolError,
    PriceRangeError,
)
from .exceptions import APIException

logger = structlog.get_logger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    logger.warning(
        "API exception occurred",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI validation errors."""
    logger.warning(
        "Validation error occurred",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": exc.errors(),
            }
        },
    )


async def domain_exception_handler(
    request: Request, 
    exc: BoursaVisionError
) -> JSONResponse:
    """Handle domain layer exceptions."""
    logger.warning(
        "Domain exception occurred",
        path=request.url.path,
        method=request.method,
        exception=str(exc),
    )
    
    # Map domain exceptions to HTTP status codes
    if isinstance(exc, PortfolioNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (InvalidSymbolError, PriceRangeError)):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "status_code": status_code,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        "Unhandled exception occurred",
        path=request.url.path,
        method=request.method,
        exception=str(exc),
        traceback=traceback.format_exc(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }
        },
    )
