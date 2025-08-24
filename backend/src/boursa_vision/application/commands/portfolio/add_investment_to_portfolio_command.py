"""
Portfolio Investment Commands - Complete Financial Schema Support
================================================================

Commands for managing portfolio investments with complete position tracking,
financial calculations, and integration with the expanded financial schema.
"""
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from boursa_vision.application.common import ICommand


@dataclass(frozen=True)
class AddInvestmentToPortfolioCommand(ICommand):
    """
    Command to add an investment position to a portfolio.
    
    Creates a new position in the portfolio with complete tracking including
    quantity, pricing, and side information. Automatically updates portfolio
    financial metrics including total invested and cash balance.
    """

    portfolio_id: UUID
    symbol: str
    quantity: Decimal
    purchase_price: Decimal
    side: str = "long"  # "long" or "short"
    notes: str | None = None
    
    def __post_init__(self):
        """Validate investment parameters"""
        if not self.symbol.strip():
            raise ValueError("Symbol cannot be empty")
            
        if len(self.symbol) > 20:
            raise ValueError("Symbol cannot exceed 20 characters")
            
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        if self.purchase_price <= 0:
            raise ValueError("Purchase price must be positive")
            
        if self.side not in ["long", "short"]:
            raise ValueError("Side must be 'long' or 'short'")
            
        # Calculate investment amount
        investment_amount = self.quantity * self.purchase_price
        if investment_amount <= 0:
            raise ValueError("Investment amount must be positive")


@dataclass(frozen=True)
class UpdatePositionCommand(ICommand):
    """
    Command to update an existing position.
    
    Updates position details including market price, quantity adjustments,
    and recalculates portfolio financial metrics based on the changes.
    """
    
    position_id: UUID
    quantity: Decimal | None = None
    market_price: Decimal | None = None
    status: str | None = None  # "active", "closed", "pending"
    notes: str | None = None
    
    def __post_init__(self):
        """Validate update parameters"""
        if self.quantity is not None and self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
            
        if self.market_price is not None and self.market_price <= 0:
            raise ValueError("Market price must be positive")
            
        if self.status is not None and self.status not in ["active", "closed", "pending"]:
            raise ValueError("Status must be 'active', 'closed', or 'pending'")


@dataclass(frozen=True)
class RemoveInvestmentFromPortfolioCommand(ICommand):
    """
    Command to remove/close an investment position from a portfolio.
    
    Closes a position and updates portfolio financial metrics including
    realized P&L, cash balance, and total invested amounts.
    """
    
    position_id: UUID
    sale_price: Decimal | None = None
    notes: str | None = None
    
    def __post_init__(self):
        """Validate removal parameters"""
        if self.sale_price is not None and self.sale_price <= 0:
            raise ValueError("Sale price must be positive")


@dataclass(frozen=True)
class RebalancePortfolioCommand(ICommand):
    """
    Command to rebalance a portfolio based on target allocations.
    
    Calculates required position adjustments to meet target allocations
    and generates the necessary buy/sell orders while maintaining
    complete financial tracking.
    """
    
    portfolio_id: UUID
    target_allocations: dict[str, Decimal]  # symbol -> target_percentage
    rebalance_cash: bool = True
    max_deviation_pct: Decimal = Decimal("5.0")
    
    def __post_init__(self):
        """Validate rebalancing parameters"""
        if not self.target_allocations:
            raise ValueError("Target allocations cannot be empty")
            
        total_allocation = sum(self.target_allocations.values())
        if abs(total_allocation - Decimal("100.0")) > Decimal("0.01"):
            raise ValueError("Target allocations must sum to 100%")
            
        for symbol, allocation in self.target_allocations.items():
            if allocation < 0 or allocation > 100:
                raise ValueError(f"Invalid allocation for {symbol}: {allocation}%")
                
        if self.max_deviation_pct < 0:
            raise ValueError("Maximum deviation percentage cannot be negative")
