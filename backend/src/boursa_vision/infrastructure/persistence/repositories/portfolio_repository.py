"""
SQLAlchemy repository implementations following the Repository pattern.
Implements domain repository interfaces with async SQLAlchemy.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
from boursa_vision.infrastructure.persistence.mappers import MapperFactory
from boursa_vision.infrastructure.persistence.models.portfolios import Portfolio
from boursa_vision.infrastructure.persistence.sqlalchemy.database import get_db_session


class SQLAlchemyPortfolioRepository(IPortfolioRepository):
    """SQLAlchemy implementation of portfolio repository."""

    def __init__(self):
        self._mapper = MapperFactory.get_mapper("portfolio")

    async def find_by_id(self, portfolio_id: UUID) -> Optional[DomainPortfolio]:
        """Find portfolio by ID."""
        async with get_db_session() as session:
            query = select(Portfolio).where(Portfolio.id == portfolio_id)
            result = await session.execute(query)
            portfolio_model = result.scalar_one_or_none()

            if portfolio_model is None:
                return None

            return self._mapper.to_domain(portfolio_model)

    async def find_by_user_id(self, user_id: UUID) -> List[DomainPortfolio]:
        """Find portfolios by user ID."""
        async with get_db_session() as session:
            query = select(Portfolio).where(Portfolio.user_id == user_id)
            result = await session.execute(query)
            portfolio_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in portfolio_models]

    async def save(self, portfolio: DomainPortfolio) -> DomainPortfolio:
        """Save portfolio."""
        async with get_db_session() as session:
            portfolio_data = self._mapper.to_persistence(portfolio)

            # Check if portfolio exists
            existing = await session.get(Portfolio, portfolio.id)

            if existing:
                # Update existing
                for key, value in portfolio_data.items():
                    if key != "id":
                        setattr(existing, key, value)
                portfolio_model = existing
            else:
                # Create new
                portfolio_model = Portfolio(**portfolio_data)
                session.add(portfolio_model)

            await session.flush()
            await session.refresh(portfolio_model)

            return self._mapper.to_domain(portfolio_model)

    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete portfolio."""
        async with get_db_session() as session:
            portfolio_model = await session.get(Portfolio, portfolio_id)

            if portfolio_model is None:
                return False

            await session.delete(portfolio_model)
            await session.flush()

            return True
