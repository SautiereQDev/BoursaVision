"""
Repository Interfaces (Ports) for Domain Layer
==============================================

Abstract interfaces defining how the domain layer accesses data.
These are implemented by the infrastructure layer following the
Dependency Inversion Principle.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.investment import Investment
from ..entities.portfolio import Portfolio
from ..value_objects.money import Money


class IPortfolioRepository(ABC):
    """Interface for portfolio data access"""

    @abstractmethod
    async def find_by_id(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Find portfolio by ID"""


    @abstractmethod
    async def find_by_user_id(self, user_id: UUID) -> List[Portfolio]:
        """Find all portfolios for a user"""


    @abstractmethod
    async def save(self, portfolio: Portfolio) -> Portfolio:
        """Save or update portfolio"""


    @abstractmethod
    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete portfolio"""


    @abstractmethod
    async def exists(self, portfolio_id: UUID) -> bool:
        """Check if portfolio exists"""



class IInvestmentRepository(ABC):
    """Interface for investment data access"""

    @abstractmethod
    async def find_by_id(self, investment_id: UUID) -> Optional[Investment]:
        """Find investment by ID"""


    @abstractmethod
    async def find_by_symbol(self, symbol: str) -> Optional[Investment]:
        """Find investment by symbol"""


    @abstractmethod
    async def find_by_symbols(self, symbols: List[str]) -> List[Investment]:
        """Find multiple investments by symbols"""


    @abstractmethod
    async def search(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> List[Investment]:
        """Search investments by name or symbol"""


    @abstractmethod
    async def save(self, investment: Investment) -> Investment:
        """Save or update investment"""


    @abstractmethod
    async def delete(self, investment_id: UUID) -> bool:
        """Delete investment"""



class IMarketDataRepository(ABC):
    """Interface for market data access"""

    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[Money]:
        """Get current price for symbol"""

    @abstractmethod
    async def get_current_prices(self, symbols: List[str]) -> dict[str, Money]:
        """Get current prices for multiple symbols"""

    @abstractmethod
    async def get_historical_prices(self, symbol: str, days: int = 252) -> List[Money]:
        """Get historical prices for symbol"""

    @abstractmethod
    async def get_historical_returns(self, symbol: str, days: int = 252) -> List[float]:
        """Get historical returns for symbol"""

    @abstractmethod
    async def save_price(self, symbol: str, price: Money) -> None:
        """Save price data"""


class IUserRepository(ABC):
    """Interface for user data access"""

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[dict]:
        """Find user by ID"""

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[dict]:
        """Find user by email"""

    @abstractmethod
    async def save(self, user: dict) -> dict:
        """Save or update user"""


class IUnitOfWork(ABC):
    """Interface for unit of work pattern"""

    portfolios: IPortfolioRepository
    investments: IInvestmentRepository
    market_data: IMarketDataRepository
    users: IUserRepository

    @abstractmethod
    async def __aenter__(self):
        """Enter async context"""

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""

    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction"""

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction"""
