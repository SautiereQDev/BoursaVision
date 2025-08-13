"""
Market data endpoints
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
import structlog

from ..dependencies import Container, CurrentUserOptional
from ..exceptions import NotFoundError, ExternalServiceError
from ..schemas import MarketDataResponse

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/market-data",
    tags=["market-data"],
    responses={
        404: {"description": "Symbol not found"},
        503: {"description": "External service unavailable"},
    },
)


@router.get(
    "/{symbol}",
    response_model=MarketDataResponse,
    summary="Get market data for symbol",
    description="Retrieve market data for a specific symbol with optional time range."
)
async def get_market_data(
    symbol: str,
    container: Container,
    current_user: CurrentUserOptional,
    period: Optional[str] = Query(
        "1d",
        description="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
        regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"
    ),
    interval: Optional[str] = Query(
        "1h",
        description="Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)",
        regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$"
    ),
) -> MarketDataResponse:
    """Get market data for a specific symbol."""
    try:
        symbol = symbol.upper()
        
        logger.info(
            "Fetching market data",
            symbol=symbol,
            period=period,
            interval=interval,
            user_id=current_user.id if current_user else None,
        )
        
        # TODO: Implement actual market data fetching
        # market_data_service = container.get_market_data_service()
        # data = await market_data_service.get_market_data(
        #     symbol=symbol,
        #     period=period,
        #     interval=interval
        # )
        
        # Mock response for now
        return MarketDataResponse(
            symbol=symbol,
            data=[],
            metadata={
                "period": period,
                "interval": interval,
                "source": "yfinance"
            }
        )
        
    except ValueError as exc:
        logger.warning("Invalid symbol format", symbol=symbol, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid symbol format: {symbol}"
        ) from exc
    except Exception as exc:
        logger.error("Failed to fetch market data", symbol=symbol, error=str(exc))
        raise ExternalServiceError("Market Data Provider", str(exc)) from exc


@router.get(
    "/{symbol}/latest",
    summary="Get latest price for symbol",
    description="Get the latest price information for a specific symbol."
)
async def get_latest_price(
    symbol: str,
    container: Container,
    current_user: CurrentUserOptional,
):
    """Get latest price for a symbol."""
    try:
        symbol = symbol.upper()
        
        logger.info(
            "Fetching latest price",
            symbol=symbol,
            user_id=current_user.id if current_user else None,
        )
        
        # TODO: Implement actual latest price fetching
        # market_data_service = container.get_market_data_service()
        # price_data = await market_data_service.get_latest_price(symbol)
        
        # Mock response for now
        from datetime import datetime
        from decimal import Decimal
        
        return {
            "symbol": symbol,
            "price": Decimal("100.00"),
            "change": Decimal("1.50"),
            "change_percent": 1.52,
            "timestamp": datetime.utcnow(),
            "volume": 1000000,
            "market_cap": Decimal("1000000000.00")
        }
        
    except ValueError as exc:
        logger.warning("Invalid symbol format", symbol=symbol, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid symbol format: {symbol}"
        ) from exc
    except Exception as exc:
        logger.error("Failed to fetch latest price", symbol=symbol, error=str(exc))
        raise ExternalServiceError("Market Data Provider", str(exc)) from exc


@router.get(
    "/search/{query}",
    summary="Search for symbols",
    description="Search for investment symbols by name or ticker."
)
async def search_symbols(
    query: str,
    container: Container,
    current_user: CurrentUserOptional,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Search for symbols by query."""
    try:
        logger.info(
            "Searching symbols",
            query=query,
            limit=limit,
            user_id=current_user.id if current_user else None,
        )
        
        # TODO: Implement actual symbol search
        # market_data_service = container.get_market_data_service()
        # results = await market_data_service.search_symbols(query, limit)
        
        # Mock response for now
        return {
            "query": query,
            "results": [],
            "total": 0
        }
        
    except Exception as exc:
        logger.error("Failed to search symbols", query=query, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search symbols"
        ) from exc


@router.get(
    "/health",
    summary="Market data service health check",
    description="Check the health of the market data service."
)
async def market_data_health():
    """Market data service health check."""
    return {"status": "ok", "service": "market-data", "timestamp": "2024-01-01T00:00:00Z"}
