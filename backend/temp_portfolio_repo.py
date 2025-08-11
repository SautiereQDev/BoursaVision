"""
Temporary portfolio repository with all required methods.
"""

from typing import List, Optional
from uuid import UUID

from src.domain.entities.portfolio import Portfolio as DomainPortfolio
from src.domain.repositories.portfolio_repository import IPortfolioRepository


class TempPortfolioRepository(IPortfolioRepository):
    """Temporary implementation with basic functionality."""

    async def save(self, entity: DomainPortfolio) -> DomainPortfolio:
        """Save portfolio."""
        return entity

    async def find_by_id(self, portfolio_id: UUID) -> Optional[DomainPortfolio]:
        """Find by ID."""
        return None

    async def delete(self, entity: DomainPortfolio) -> None:
        """Delete entity."""
        pass

    async def find_by_user_id(self, user_id: UUID) -> List[DomainPortfolio]:
        """Find portfolios by user ID."""
        return []

    async def count_by_user(self, user_id: UUID) -> int:
        """Count portfolios by user."""
        return 0

    async def exists(self, portfolio_id: UUID) -> bool:
        """Check if portfolio exists."""
        return False

    async def exists_by_name(self, user_id: UUID, name: str) -> bool:
        """Check if portfolio exists by name."""
        return False

    async def find_all(
        self, limit: int = 100, offset: int = 0
    ) -> List[DomainPortfolio]:
        """Find all portfolios."""
        return []

    async def find_by_name(self, user_id: UUID, name: str) -> Optional[DomainPortfolio]:
        """Find portfolio by name."""
        return None
