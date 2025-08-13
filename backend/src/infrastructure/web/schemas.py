"""
API Schemas for the REST API
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseAPISchema(BaseModel):
    """Base schema for API models."""

    class Config:
        """Pydantic configuration."""

        from_attributes = True
        use_enum_values = True
        arbitrary_types_allowed = True


# Portfolio Schemas
class PortfolioCreate(BaseAPISchema):
    """Schema for creating a portfolio."""

    name: str = Field(..., description="Portfolio name", min_length=1, max_length=100)
    description: Optional[str] = Field(
        None, description="Portfolio description", max_length=500
    )
    currency: str = Field(..., description="Base currency", pattern="^[A-Z]{3}$")


class PortfolioUpdate(BaseAPISchema):
    """Schema for updating a portfolio."""

    name: Optional[str] = Field(
        None, description="Portfolio name", min_length=1, max_length=100
    )
    description: Optional[str] = Field(
        None, description="Portfolio description", max_length=500
    )


class PortfolioResponse(BaseAPISchema):
    """Schema for portfolio response."""

    id: UUID = Field(..., description="Portfolio ID")
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    currency: str = Field(..., description="Base currency")
    total_value: Decimal = Field(..., description="Total portfolio value")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PortfolioListResponse(BaseAPISchema):
    """Schema for portfolio list response."""

    portfolios: List[PortfolioResponse] = Field(..., description="List of portfolios")
    total: int = Field(..., description="Total number of portfolios")


# Investment Schemas
class InvestmentCreate(BaseAPISchema):
    """Schema for creating an investment."""

    symbol: str = Field(
        ..., description="Investment symbol", min_length=1, max_length=20
    )
    name: str = Field(..., description="Investment name", min_length=1, max_length=200)
    investment_type: str = Field(..., description="Type of investment")
    exchange: str = Field(..., description="Exchange name")
    currency: str = Field(..., description="Trading currency", pattern="^[A-Z]{3}$")


class InvestmentResponse(BaseAPISchema):
    """Schema for investment response."""

    id: UUID = Field(..., description="Investment ID")
    symbol: str = Field(..., description="Investment symbol")
    name: str = Field(..., description="Investment name")
    investment_type: str = Field(..., description="Type of investment")
    exchange: str = Field(..., description="Exchange name")
    currency: str = Field(..., description="Trading currency")
    current_price: Optional[Decimal] = Field(None, description="Current market price")
    created_at: datetime = Field(..., description="Creation timestamp")


class InvestmentRecommendation(BaseAPISchema):
    """Schema for investment recommendation."""

    investment: InvestmentResponse = Field(..., description="Investment details")
    recommendation: str = Field(
        ..., description="Recommendation type (BUY, SELL, HOLD)"
    )
    score: float = Field(..., description="Recommendation score", ge=0.0, le=1.0)
    reasons: List[str] = Field(..., description="Reasons for recommendation")
    risk_level: str = Field(..., description="Risk level assessment")


class InvestmentRecommendationsResponse(BaseAPISchema):
    """Schema for investment recommendations response."""

    recommendations: List[InvestmentRecommendation] = Field(
        ..., description="List of recommendations"
    )
    generated_at: datetime = Field(..., description="Generation timestamp")


# Market Data Schemas
class MarketDataPoint(BaseAPISchema):
    """Schema for a single market data point."""

    timestamp: datetime = Field(..., description="Data timestamp")
    open_price: Decimal = Field(..., description="Opening price")
    high_price: Decimal = Field(..., description="Highest price")
    low_price: Decimal = Field(..., description="Lowest price")
    close_price: Decimal = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")


class MarketDataResponse(BaseAPISchema):
    """Schema for market data response."""

    symbol: str = Field(..., description="Investment symbol")
    data: List[MarketDataPoint] = Field(..., description="Market data points")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional metadata"
    )


# WebSocket Schemas
class WebSocketMessage(BaseAPISchema):
    """Schema for WebSocket messages."""

    type: str = Field(..., description="Message type")
    data: Dict = Field(..., description="Message data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Message timestamp"
    )


class PriceUpdate(BaseAPISchema):
    """Schema for real-time price updates."""

    symbol: str = Field(..., description="Investment symbol")
    price: Decimal = Field(..., description="Current price")
    change: Decimal = Field(..., description="Price change")
    change_percent: float = Field(..., description="Price change percentage")
    timestamp: datetime = Field(..., description="Update timestamp")


# Error Schemas
class ErrorDetail(BaseAPISchema):
    """Schema for error details."""

    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict] = Field(None, description="Additional error details")


class ValidationErrorDetail(BaseAPISchema):
    """Schema for validation error details."""

    loc: List[str] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseAPISchema):
    """Schema for validation error response."""

    error: ErrorDetail = Field(..., description="Error information")
    details: List[ValidationErrorDetail] = Field(
        ..., description="Validation error details"
    )


# Health Check Schema
class HealthCheckResponse(BaseAPISchema):
    """Schema for health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment")


# Pagination Schemas
class PaginationParams(BaseAPISchema):
    """Schema for pagination parameters."""

    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(20, description="Items per page", ge=1, le=100)


class PaginatedResponse(BaseAPISchema):
    """Schema for paginated responses."""

    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    total_items: int = Field(..., description="Total number of items")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")
