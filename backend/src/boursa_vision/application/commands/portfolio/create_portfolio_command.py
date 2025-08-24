"""
Create Portfolio Command - Complete Financial Schema Support
==========================================================

Command for creating portfolios with complete financial tracking capabilities.
Leverages the expanded financial schema with all portfolio management fields.
"""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from boursa_vision.application.common import ICommand


@dataclass(frozen=True)
class CreatePortfolioCommand(ICommand):
    """
    Command to create a new portfolio with complete financial tracking.
    
    Utilizes the complete financial schema with all portfolio management
    capabilities including initial cash setup, default portfolio designation,
    and comprehensive financial field initialization.
    """

    user_id: UUID
    name: str
    description: str | None = None
    initial_cash_amount: Decimal = Decimal("0.0000")
    base_currency: str = "USD"
    is_default: bool = False
    is_active: bool = True

    def __post_init__(self):
        """Validate command parameters"""
        if not self.name.strip():
            raise ValueError("Portfolio name cannot be empty")
        
        if len(self.name) > 100:
            raise ValueError("Portfolio name cannot exceed 100 characters")
            
        if self.initial_cash_amount < 0:
            raise ValueError("Initial cash amount cannot be negative")
            
        if self.base_currency not in ["USD", "EUR", "GBP", "CAD", "JPY"]:
            raise ValueError(f"Unsupported currency: {self.base_currency}")


@dataclass(frozen=True)  
class UpdatePortfolioFinancialsCommand(ICommand):
    """
    Command to update portfolio financial metrics.
    
    Updates the complete financial tracking fields including P&L calculations,
    return percentages, and portfolio valuation based on current positions
    and market prices.
    """
    
    portfolio_id: UUID
    current_cash: Decimal | None = None
    total_invested: Decimal | None = None
    total_value: Decimal | None = None
    daily_pnl: Decimal | None = None
    total_pnl: Decimal | None = None
    daily_return_pct: Decimal | None = None
    total_return_pct: Decimal | None = None
    
    def __post_init__(self):
        """Validate financial metrics"""
        if self.current_cash is not None and self.current_cash < 0:
            raise ValueError("Current cash cannot be negative")
            
        if self.total_value is not None and self.total_value < 0:
            raise ValueError("Total value cannot be negative")


@dataclass(frozen=True)
class SetDefaultPortfolioCommand(ICommand):
    """
    Command to set a portfolio as the default portfolio for a user.
    
    Ensures only one portfolio is marked as default per user by updating
    the is_default flag across all user portfolios.
    """
    
    user_id: UUID
    portfolio_id: UUID
