"""
Simple minimal FastAPI application for testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Boursa Vision API",
    description="Financial portfolio management and market data API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Boursa Vision API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.get("/api/v1/portfolios")
async def get_portfolios():
    """Get user portfolios."""
    return {
        "portfolios": [
            {
                "id": "portfolio1",
                "name": "My Portfolio",
                "total_value": 10000.0,
                "cash_balance": 500.0,
            }
        ],
        "total_count": 1,
    }


@app.get("/api/v1/market-data/price/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol."""
    return {
        "symbol": symbol,
        "current_price": 150.0,
        "change_amount": 2.5,
        "change_percent": 1.69,
        "volume": 1000000,
    }


@app.get("/api/v1/investments/recommendations")
async def get_recommendations():
    """Get investment recommendations."""
    return {
        "recommendations": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "recommendation_type": "BUY",
                "target_price": 180.0,
                "current_price": 175.0,
                "confidence_score": 0.85,
            }
        ],
        "total_count": 1,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
