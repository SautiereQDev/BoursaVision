"""Market data endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/market", tags=["market_data"])


@router.get("/")
async def get_market_data():
    """Get market data."""
    return {"message": "Market data endpoint working!", "data": []}


@router.get("/health")
async def market_health():
    """Market data service health check."""
    return {"status": "ok", "service": "market_data"}
