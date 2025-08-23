"""
SQLAlchemy repository implementations following the Repository pattern.
Implements domain repository interfaces with async SQLAlchemy.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
from boursa_vision.infrastructure.persistence.mappers import PortfolioMapper
from boursa_vision.infrastructure.persistence.models.portfolios import Portfolio
from boursa_vision.infrastructure.persistence.sqlalchemy.database import get_db_session


class SQLAlchemyPortfolioRepository(IPortfolioRepository):
    """SQLAlchemy implementation of portfolio repository."""

    # Class-level mapper for test mocking compatibility
    _mapper = PortfolioMapper()

    def __init__(self, session: Optional[AsyncSession] = None):
        self._mapper = PortfolioMapper()
        self._session = session  # Optional injected session for testing

    def _get_session(self):
        """Get session - either injected one (for tests) or from db session factory."""
        if self._session:
            return self._session
        return get_db_session()

    async def find_by_id(self, portfolio_id: UUID) -> Optional[DomainPortfolio]:
        """Find portfolio by ID."""
        if self._session:
            # Use injected session (testing mode)
            query = select(Portfolio).where(Portfolio.id == portfolio_id)
            result = await self._session.execute(query)
            portfolio_model = result.scalar_one_or_none()

            if portfolio_model is None:
                return None

            return self._mapper.to_domain(portfolio_model)
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(Portfolio).where(Portfolio.id == portfolio_id)
                result = await session.execute(query)
                portfolio_model = result.scalar_one_or_none()

                if portfolio_model is None:
                    return None

                return self._mapper.to_domain(portfolio_model)

    async def find_by_user_id(self, user_id: UUID) -> List[DomainPortfolio]:
        """Find portfolios by user ID."""
        if self._session:
            # Use injected session (testing mode)
            query = select(Portfolio).where(Portfolio.user_id == user_id)
            result = await self._session.execute(query)
            portfolio_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in portfolio_models]
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(Portfolio).where(Portfolio.user_id == user_id)
                result = await session.execute(query)
                portfolio_models = result.scalars().all()

                return [self._mapper.to_domain(model) for model in portfolio_models]

    async def save(self, portfolio: DomainPortfolio) -> DomainPortfolio:
        """Save portfolio."""
        if self._session:
            # Use injected session (test mode)
            session = self._session

            # Check if portfolio exists
            existing = await session.get(Portfolio, portfolio.id)

            if existing:
                # Update existing portfolio
                self._mapper.update_model(existing, portfolio)
                portfolio_model = existing
            else:
                # Create new portfolio
                portfolio_model = self._mapper.to_model(portfolio)
                session.add(portfolio_model)

            await session.flush()
            await session.refresh(portfolio_model)

            return self._mapper.to_domain(portfolio_model)
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                # Check if portfolio exists
                existing = await session.get(Portfolio, portfolio.id)

                if existing:
                    # Update existing portfolio
                    self._mapper.update_model(existing, portfolio)
                    portfolio_model = existing
                else:
                    # Create new portfolio
                    portfolio_model = self._mapper.to_model(portfolio)
                    session.add(portfolio_model)

                await session.flush()
                await session.refresh(portfolio_model)

                return self._mapper.to_domain(portfolio_model)

    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete portfolio."""
        if self._session:
            # Use injected session (testing mode)
            portfolio_model = await self._session.get(Portfolio, portfolio_id)

            if portfolio_model is None:
                return False

            await self._session.delete(portfolio_model)
            await self._session.flush()

            return True
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                portfolio_model = await session.get(Portfolio, portfolio_id)

                if portfolio_model is None:
                    return False

                await session.delete(portfolio_model)
                await session.flush()

                return True

    async def find_by_name(self, user_id: UUID, name: str) -> Optional[DomainPortfolio]:
        """Find portfolio by user and name."""
        async with get_db_session() as session:
            query = select(Portfolio).where(
                and_(Portfolio.user_id == user_id, Portfolio.name == name)
            )
            result = await session.execute(query)
            portfolio_model = result.scalar_one_or_none()

            if portfolio_model is None:
                return None

            return self._mapper.to_domain(portfolio_model)

    async def exists(self, portfolio_id: UUID) -> bool:
        """Check if portfolio exists."""
        async with get_db_session() as session:
            query = select(func.count(Portfolio.id)).where(Portfolio.id == portfolio_id)
            result = await session.execute(query)
            count = result.scalar()
            return (count or 0) > 0

    async def exists_by_name(self, user_id: UUID, name: str) -> bool:
        """Check if portfolio with name exists for user."""
        async with get_db_session() as session:
            query = select(func.count(Portfolio.id)).where(
                and_(Portfolio.user_id == user_id, Portfolio.name == name)
            )
            result = await session.execute(query)
            count = result.scalar()
            return (count or 0) > 0

    async def count_by_user(self, user_id: UUID) -> int:
        """Count portfolios for user."""
        async with get_db_session() as session:
            query = select(func.count(Portfolio.id)).where(Portfolio.user_id == user_id)
            result = await session.execute(query)
            return result.scalar() or 0

    async def find_all(
        self, offset: int = 0, limit: int = 100
    ) -> List[DomainPortfolio]:
        """Find all portfolios with pagination."""
        async with get_db_session() as session:
            query = select(Portfolio).offset(offset).limit(limit)
            result = await session.execute(query)
            portfolio_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in portfolio_models]
