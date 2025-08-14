from datetime import datetime
from typing import Dict, Optional, Union

from pydantic import Field

from ..__init__ import BaseDTO


class SignalDTO(BaseDTO):
    """Trading signal DTO."""

    symbol: str = Field(..., description="Asset symbol")
    action: str = Field(..., description="Signal action (BUY/SELL/HOLD)")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence score")
    price: Optional[float] = Field(None, description="Recommended price")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    reason: str = Field(..., description="Signal reasoning")
    metadata: Dict[str, Union[str, float, int]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(..., description="Signal timestamp")

    @property
    def reasoning(self) -> str:
        """Alias for reason for backward compatibility."""
        return self.reason
