"""Analysis endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/")
async def get_analysis():
    """Get portfolio analysis."""
    return {"message": "Analysis endpoint working!", "analysis": {}}


@router.get("/health")
async def analysis_health():
    """Analysis service health check."""
    return {"status": "ok", "service": "analysis"}
