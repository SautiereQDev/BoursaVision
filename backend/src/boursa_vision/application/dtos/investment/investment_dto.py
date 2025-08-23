from datetime import datetime
from uuid import UUID

from pydantic import Field

from ..__init__ import BaseDTO, MoneyDTO


class InvestmentDTO(BaseDTO):
    """Investment entity DTO."""

    id: UUID = Field(..., description="Investment unique identifier")
    symbol: str = Field(..., min_length=1, max_length=10, description="Asset symbol")
    name: str = Field(..., min_length=1, max_length=200, description="Investment name")
    investment_type: str = Field(..., description="Type of investment")
    sector: str = Field(..., description="Investment sector")
    market_cap: str = Field(..., description="Market capitalization category")
    currency: str = Field(..., description="Trading currency")
    exchange: str = Field(..., min_length=1, max_length=50, description="Exchange name")
    current_price: MoneyDTO | None = Field(None, description="Current market price")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
