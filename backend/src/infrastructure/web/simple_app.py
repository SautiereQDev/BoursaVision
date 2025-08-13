"""
Simple API version with basic functionality
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Boursa Vision API",
    description="Investment portfolio management platform",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Boursa Vision API is running!",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "boursa-vision-api"}


@app.get("/api/v1/portfolios")
async def get_portfolios():
    """Get user portfolios."""
    return {
        "portfolios": [],
        "total": 0,
        "message": "Portfolio endpoint working!"
    }


@app.post("/api/v1/portfolios")
async def create_portfolio():
    """Create a new portfolio."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Portfolio",
        "total_value": 0.0,
        "currency": "USD",
        "message": "Portfolio creation endpoint working!"
    }


@app.get("/api/v1/investments/recommendations")
async def get_investment_recommendations():
    """Get investment recommendations."""
    return {
        "recommendations": [],
        "generated_at": "2024-01-01T00:00:00Z",
        "message": "Investment recommendations endpoint working!"
    }


@app.get("/api/v1/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol."""
    return {
        "symbol": symbol.upper(),
        "data": [],
        "metadata": {
            "period": "1d",
            "interval": "1h",
            "source": "yfinance"
        },
        "message": f"Market data for {symbol.upper()} endpoint working!"
    }


@app.websocket("/api/v1/ws/real-time")
async def websocket_endpoint():
    """WebSocket endpoint for real-time updates."""
    # This is a placeholder - actual WebSocket logic would go here
    pass
