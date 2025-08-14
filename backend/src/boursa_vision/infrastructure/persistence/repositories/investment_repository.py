"""
SQLAlchemy Investment Repository Implementation
===============================================

SQLAlchemy implementation of the investment repository interface.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.investment import Investment
from ....domain.repositories.investment_repository import IInvestmentRepository
from ..mappers_new import InvestmentMapper
from ..models.investment import InvestmentModel


class SQLAlchemyInvestmentRepository(IInvestmentRepository):
    """SQLAlchemy implementation of investment repository."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = InvestmentMapper()

    async def find_by_symbol(self, symbol: str) -> Optional[Investment]:
        """Find investment by symbol."""
        stmt = select(InvestmentModel).where(InvestmentModel.symbol == symbol)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._mapper.to_domain(model)

    async def find_by_exchange(self, exchange: str) -> List[Investment]:
        """Find investments by exchange."""
        stmt = select(InvestmentModel).where(InvestmentModel.exchange == exchange)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def find_by_sector(self, sector: str) -> List[Investment]:
        """Find investments by sector."""
        stmt = select(InvestmentModel).where(InvestmentModel.sector == sector)
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in models]

    async def save(self, investment: Investment) -> None:
        """Save investment to database."""
        model = self._mapper.to_persistence(investment)
        self._session.add(model)

    async def delete(self, investment: Investment) -> None:
        """Delete investment from database."""
        stmt = select(InvestmentModel).where(
            InvestmentModel.symbol == investment.symbol
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is not None:
            await self._session.delete(model)
