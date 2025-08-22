"""
SQLAlchemy Investment Repository Implementation
===============================================

SQLAlchemy implementation of the investment repository interface.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, delete as sql_delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.investment import Investment
from ....domain.repositories.investment_repository import IInvestmentRepository
from ..models.investment import InvestmentModel
from ..sqlalchemy.database import get_db_session


class SimpleInvestmentMapper:
    """Simple mapper for Investment domain entity ↔ InvestmentModel."""

    def to_domain(self, model: InvestmentModel) -> Investment:
        """Convert SQLAlchemy InvestmentModel to domain Investment."""
        from boursa_vision.domain.entities.investment import MarketCap, InvestmentSector, InvestmentType
        from boursa_vision.domain.value_objects.money import Currency
        
        # Mapper market_cap numérique vers enum MarketCap
        market_cap_enum = MarketCap.LARGE  # Valeur par défaut
        if model.market_cap is not None:
            market_cap_value = float(str(model.market_cap))
            # Mapping inverse des valeurs numériques vers enum
            if market_cap_value < 0.05:  # < $50M
                market_cap_enum = MarketCap.NANO
            elif market_cap_value < 0.3:  # $50M - $300M
                market_cap_enum = MarketCap.MICRO
            elif market_cap_value < 2:  # $300M - $2B
                market_cap_enum = MarketCap.SMALL
            elif market_cap_value < 10:  # $2B - $10B
                market_cap_enum = MarketCap.MID
            elif market_cap_value < 200:  # $10B - $200B
                market_cap_enum = MarketCap.LARGE
            else:  # > $200B
                market_cap_enum = MarketCap.MEGA

        # Mapper sector string vers enum
        sector_enum = InvestmentSector.TECHNOLOGY  # Valeur par défaut
        if model.sector:
            try:
                sector_enum = InvestmentSector(model.sector)
            except ValueError:
                pass  # Garde la valeur par défaut

        return Investment(
            symbol=model.symbol,
            name=model.name,
            exchange=model.exchange,
            currency=Currency(model.currency) if model.currency else Currency.USD,
            sector=sector_enum,
            market_cap=market_cap_enum,
            investment_type=InvestmentType.STOCK,  # Valeur par défaut
            # Les champs suivants n'existent pas dans le domain Investment
            # price=Decimal(str(model.current_price)) if model.current_price else None,
            description=None,  # L'entité n'a pas ce champ
        )

    def to_persistence(self, investment: Investment) -> InvestmentModel:
        """Convert domain Investment to SQLAlchemy InvestmentModel."""
        # Mapper market_cap enum vers valeur numérique
        market_cap_mapping = {
            "NANO": 0.05,
            "MICRO": 0.25,
            "SMALL": 2.0,
            "MID": 10.0,
            "LARGE": 50.0,
            "MEGA": 500.0,
        }
        
        market_cap_numeric = market_cap_mapping.get(investment.market_cap.value, 50.0)

        return InvestmentModel(
            symbol=investment.symbol,
            name=investment.name,
            exchange=investment.exchange,
            currency=investment.currency.value,
            sector=investment.sector.value,
            market_cap=market_cap_numeric,
            # Valeurs par défaut pour les champs requis non mappés
            current_price=None,
            description=None,
        )


class SQLAlchemyInvestmentRepository(IInvestmentRepository):
    """SQLAlchemy implementation of investment repository."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self._mapper = SimpleInvestmentMapper()
        self._session = session  # Optional injected session for testing

    async def _execute_with_session(self, stmt, method_name="query"):
        """Execute statement with either injected session or get_db_session."""
        if self._session:
            # Use injected session (testing mode)
            result = await self._session.execute(stmt)
            return result
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                result = await session.execute(stmt)
                return result

    async def find_by_symbol(self, symbol: str) -> Optional[Investment]:
        """Find investment by symbol."""
        stmt = select(InvestmentModel).where(InvestmentModel.symbol == symbol)
        result = await self._execute_with_session(stmt)
        model = result.scalar_one_or_none()
        return self._mapper.to_domain(model) if model else None

    async def find_by_id(self, investment_id: str) -> Optional[Investment]:
        """Find investment by ID."""
        stmt = select(InvestmentModel).where(InvestmentModel.id == investment_id)
        result = await self._execute_with_session(stmt)
        model = result.scalar_one_or_none()
        return self._mapper.to_domain(model) if model else None

    async def find_by_exchange(self, exchange: str) -> List[Investment]:
        """Find investments by exchange."""
        stmt = select(InvestmentModel).where(InvestmentModel.exchange == exchange)
        result = await self._execute_with_session(stmt)
        models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in models]

    async def find_by_sector(self, sector: str) -> List[Investment]:
        """Find investments by sector."""
        stmt = select(InvestmentModel).where(InvestmentModel.sector == sector)
        result = await self._execute_with_session(stmt)
        models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in models]

    async def find_all_active(self) -> List[Investment]:
        """Find all active investments."""
        stmt = select(InvestmentModel)
        result = await self._execute_with_session(stmt)
        models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in models]

    async def save(self, investment: Investment) -> Investment:
        """Save investment to database."""
        if self._session:
            # Use injected session (testing mode)
            # Check if investment exists
            stmt = select(InvestmentModel).where(InvestmentModel.symbol == investment.symbol)
            result = await self._session.execute(stmt)
            existing_model = result.scalar_one_or_none()

            if existing_model:
                # Delete old version
                delete_stmt = sql_delete(InvestmentModel).where(
                    InvestmentModel.symbol == investment.symbol
                )
                await self._session.execute(delete_stmt)
                await self._session.flush()

            # Create new investment
            model = self._mapper.to_persistence(investment)
            self._session.add(model)
            await self._session.flush()
            return self._mapper.to_domain(model)
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                # Check if investment exists
                stmt = select(InvestmentModel).where(InvestmentModel.symbol == investment.symbol)
                result = await session.execute(stmt)
                existing_model = result.scalar_one_or_none()

                if existing_model:
                    # Delete old version
                    delete_stmt = sql_delete(InvestmentModel).where(
                        InvestmentModel.symbol == investment.symbol
                    )
                    await session.execute(delete_stmt)
                    await session.flush()

                # Create new investment
                model = self._mapper.to_persistence(investment)
                session.add(model)
                await session.flush()
                return self._mapper.to_domain(model)

    async def find_all(self) -> List[Investment]:
        """Find all investments (alias for find_all_active)."""
        return await self.find_all_active()
    
    async def find_by_market_cap(self, market_cap: str) -> List[Investment]:
        """Find investments by market cap."""
        # Convert market cap enum to numeric value for filtering
        market_cap_mapping = {
            'NANO': 0.05,
            'MICRO': 0.25,
            'SMALL': 2.0,
            'MID': 10.0,
            'LARGE': 50.0,
            'MEGA': 500.0,
        }
        
        target_value = market_cap_mapping.get(market_cap, 50.0)
        # Search with tolerance range
        stmt = select(InvestmentModel).where(
            InvestmentModel.market_cap.between(target_value * 0.1, target_value * 10)
        )
        result = await self._execute_with_session(stmt)
        models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in models]
    
    async def search_by_name(self, name_pattern: str) -> List[Investment]:
        """Search investments by name pattern."""
        stmt = select(InvestmentModel).where(
            InvestmentModel.name.ilike(f"%{name_pattern}%")
        )
        result = await self._execute_with_session(stmt)
        models = result.scalars().all()
        return [self._mapper.to_domain(model) for model in models]

    async def delete(self, investment: Investment) -> None:
        """Delete investment."""
        if self._session:
            # Use injected session (testing mode)
            stmt = sql_delete(InvestmentModel).where(InvestmentModel.symbol == investment.symbol)
            await self._session.execute(stmt)
            await self._session.flush()
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                stmt = sql_delete(InvestmentModel).where(InvestmentModel.symbol == investment.symbol)
                await session.execute(stmt)
                await session.flush()
