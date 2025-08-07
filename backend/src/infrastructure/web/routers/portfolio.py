"""Portfolio management endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/")
async def get_portfolios():
    """Get user portfolios."""
    return {"message": "Portfolio endpoint working!", "portfolios": []}


@router.get("/health")
async def portfolio_health():
    """Portfolio service health check."""
    return {"status": "ok", "service": "portfolio"}
