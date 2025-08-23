"""
Base DTO and shared constants for Application DTOs
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# Import exceptions for DTO validation

# Constants to avoid string duplication
ASSET_SYMBOL_DESC = "Asset symbol"
INVESTMENT_NAME_DESC = "Investment name"
EXCHANGE_NAME_DESC = "Exchange name"
INVESTMENT_TYPE_DESC = "Type of investment"
INVESTMENT_SECTOR_DESC = "Investment sector"
MARKET_CAP_DESC = "Market capitalization category"
TRADING_CURRENCY_DESC = "Trading currency"
PORTFOLIO_NAME_DESC = "Portfolio name"
USER_ID_DESC = "User identifier"
AMOUNT_DESC = "Amount of money"
CURRENCY_CODE_DESC = "Currency code"
QUANTITY_DESC = "Quantity of the position"
AVERAGE_PRICE_DESC = "Average purchase price"
CURRENT_PRICE_DESC = "Current market price"


class BaseDTO(BaseModel):
    """Base DTO with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: float,
        },
    )
