"""
FastAPI Main Application
=======================

Simple FastAPI application for Boursa Vision.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Create FastAPI app
app = FastAPI(
    title="Boursa Vision API",
    description="Investment portfolio management platform",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Boursa Vision API is running!"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Service is healthy"}


@app.get("/api/v1/portfolios")
async def get_portfolios():
    """Get user portfolios."""
    return {"message": "Portfolio endpoint working!", "portfolios": []}


@app.get("/api/v1/market")
async def get_market_data():
    """Get market data."""
    return {"message": "Market data endpoint working!", "data": []}


@app.get("/api/v1/analysis")
async def get_analysis():
    """Get portfolio analysis."""
    return {"message": "Analysis endpoint working!", "analysis": {}}
