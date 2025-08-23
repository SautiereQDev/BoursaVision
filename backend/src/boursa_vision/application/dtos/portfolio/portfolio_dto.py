from datetime import datetime
from uuid import UUID

from pydantic import Field

from ..__init__ import BaseDTO, MoneyDTO, PositionDTO


class PortfolioDTO(BaseDTO):
    """Portfolio entity DTO."""

    id: UUID = Field(..., description="Portfolio unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    description: str | None = Field(
        None, max_length=500, description="Portfolio description"
    )
    user_id: UUID = Field(..., description="User identifier")
    positions: list[PositionDTO] = Field(
        default_factory=list, description="Portfolio positions"
    )
    total_value: MoneyDTO | None = Field(None, description="Total portfolio value")
    currency: str = Field(..., description="Base currency")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
