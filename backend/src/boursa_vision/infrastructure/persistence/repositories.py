"""
Repository implementations for the trading platform.

This module provides concrete implementations of domain repository interfaces
using SQLAlchemy for PostgreSQL + TimescaleDB persistence.
"""

from uuid import UUID

from sqlalchemy import and_, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.entities.investment import Investment
from ...domain.entities.market_data import MarketData as DomainMarketData
from ...domain.entities.portfolio import Portfolio as DomainPortfolio
from ...domain.entities.user import User as DomainUser
from ...domain.repositories.investment_repository import IInvestmentRepository
from ...domain.repositories.market_data_repository import IMarketDataRepository
from ...domain.repositories.portfolio_repository import IPortfolioRepository
from ...domain.repositories.user_repository import IUserRepository
from .mappers_new import InvestmentMapper, MarketDataMapper, PortfolioMapper, UserMapper
from .models import Instrument, MarketData, Portfolio, User


class SqlAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of User repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, user_id: UUID) -> DomainUser | None:
        """Find user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def find_by_email(self, email: str) -> DomainUser | None:
        """Find user by email."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def find_by_username(self, username: str) -> DomainUser | None:
        """Find user by username."""
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def save(self, user: DomainUser) -> DomainUser:
        """Save user entity."""
        existing_stmt = select(User).where(User.id == user.id)
        result = await self._session.execute(existing_stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model:
            UserMapper.update_model(existing_model, user)
            model = existing_model
        else:
            model = UserMapper.to_persistence(user)
            self._session.add(model)

        await self._session.flush()
        return UserMapper.to_domain(model)

    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
        stmt = delete(User).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def find_all_active(self) -> list[DomainUser]:
        """Find all active users."""
        stmt = select(User).where(User.is_active.is_(True))
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [UserMapper.to_domain(model) for model in models]


class SqlAlchemyPortfolioRepository(IPortfolioRepository):
    """SQLAlchemy implementation of Portfolio repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, portfolio_id: UUID) -> DomainPortfolio | None:
        """Find portfolio by ID."""
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.positions))
            .where(Portfolio.id == portfolio_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return PortfolioMapper.to_domain(model) if model else None

    async def find_by_user_id(self, user_id: UUID) -> list[DomainPortfolio]:
        """Find portfolios by user ID."""
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.positions))
            .where(Portfolio.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [PortfolioMapper.to_domain(model) for model in models]

    async def save(self, portfolio: DomainPortfolio) -> DomainPortfolio:
        """Save portfolio entity."""
        existing_stmt = select(Portfolio).where(Portfolio.id == portfolio.id)
        result = await self._session.execute(existing_stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model:
            PortfolioMapper.update_model(existing_model, portfolio)
            model = existing_model
        else:
            model = PortfolioMapper.to_model(portfolio)
            self._session.add(model)

        await self._session.flush()
        return PortfolioMapper.to_domain(model)

    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete portfolio by ID."""
        stmt = delete(Portfolio).where(Portfolio.id == portfolio_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0


class SqlAlchemyMarketDataRepository(IMarketDataRepository):
    """SQLAlchemy implementation of MarketData repository with TimescaleDB optimizations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, market_data: DomainMarketData) -> DomainMarketData:
        """Save market data."""
        model = MarketDataMapper.to_model(market_data)

        # Use INSERT ON CONFLICT for TimescaleDB efficiency
        stmt = select(MarketData).where(
            and_(
                MarketData.time == model.time,
                MarketData.symbol == model.symbol,
                MarketData.interval_type == model.interval_type,
            )
        )
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model:
            # Update existing record
            existing_model.open_price = model.open_price
            existing_model.high_price = model.high_price
            existing_model.low_price = model.low_price
            existing_model.close_price = model.close_price
            existing_model.adjusted_close = model.adjusted_close
            existing_model.volume = model.volume
            existing_model.source = model.source
            model = existing_model
        else:
            self._session.add(model)

        await self._session.flush()
        return MarketDataMapper.to_domain(model)

    async def find_by_symbol_and_timerange(
        self,
        symbol: str,
        start_time,
        end_time,
        interval_type: str = "1d",
        limit: int | None = None,
    ) -> list[DomainMarketData]:
        """Find market data by symbol and time range (optimized for TimescaleDB)."""
        stmt = (
            select(MarketData)
            .where(
                and_(
                    MarketData.symbol == symbol,
                    MarketData.interval_type == interval_type,
                    MarketData.time >= start_time,
                    MarketData.time <= end_time,
                )
            )
            .order_by(MarketData.time.desc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [MarketDataMapper.to_domain(model) for model in models]

    async def find_latest_by_symbol(
        self, symbol: str, interval_type: str = "1d"
    ) -> DomainMarketData | None:
        """Find latest market data for symbol."""
        stmt = (
            select(MarketData)
            .where(
                and_(
                    MarketData.symbol == symbol,
                    MarketData.interval_type == interval_type,
                )
            )
            .order_by(desc(MarketData.time))
            .limit(1)
        )

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return MarketDataMapper.to_domain(model) if model else None

    async def find_by_symbols(
        self, symbols: list[str], interval_type: str = "1d", limit: int | None = None
    ) -> list[DomainMarketData]:
        """Find latest market data for multiple symbols."""
        stmt = (
            select(MarketData)
            .where(
                and_(
                    MarketData.symbol.in_(symbols),
                    MarketData.interval_type == interval_type,
                )
            )
            .order_by(MarketData.symbol, desc(MarketData.time))
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [MarketDataMapper.to_domain(model) for model in models]

    async def delete_old_data(self, days_to_keep: int) -> int:
        """Delete old market data (TimescaleDB cleanup)."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        stmt = delete(MarketData).where(MarketData.time < cutoff_date)
        result = await self._session.execute(stmt)
        return result.rowcount


class SqlAlchemyInvestmentRepository(IInvestmentRepository):
    """SQLAlchemy implementation of Investment repository."""

    def __init__(self, session: AsyncSession | None = None):
        self._session = session

    async def find_by_symbol(self, symbol: str) -> Investment | None:
        """Find investment by symbol."""
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(Instrument.symbol == symbol)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            return InvestmentMapper.to_domain(model, fundamental_data)
        return None

    async def find_by_exchange(self, exchange: str) -> list[Investment]:
        """Find investments by exchange."""
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(
                and_(Instrument.exchange == exchange, Instrument.is_active.is_(True))
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))

        return investments

    async def find_by_sector(self, sector: str) -> list[Investment]:
        """Find investments by sector."""
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(and_(Instrument.sector == sector, Instrument.is_active.is_(True)))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))

        return investments

    async def save(self, investment: Investment) -> Investment:
        """Save investment."""
        existing_stmt = select(Instrument).where(Instrument.symbol == investment.symbol)
        result = await self._session.execute(existing_stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model:
            InvestmentMapper.update_instrument_model(existing_model, investment)
            model = existing_model
        else:
            model = Instrument(
                symbol=investment.symbol,
                name=investment.name,
                instrument_type=investment.instrument_type,
                exchange=investment.exchange,
                currency=investment.currency.value,
                sector=investment.sector,
                industry=investment.industry,
                is_active=True,
            )
            self._session.add(model)

        await self._session.flush()
        return InvestmentMapper.to_domain(model)

    async def find_all_active(self) -> list[Investment]:
        """Find all active investments."""
        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(Instrument.is_active.is_(True))
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))

        return investments

    async def find_by_id(self, investment_id: str) -> Investment | None:
        """Find investment by ID."""
        if not self._session:
            raise ValueError("Session is not initialized")

        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(
                Instrument.symbol == investment_id
            )  # Assuming ID is the symbol for now
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            return InvestmentMapper.to_domain(model, fundamental_data)
        return None

    async def find_all(self) -> list[Investment]:
        """Find all investments."""
        if not self._session:
            raise ValueError("Session is not initialized")

        stmt = select(Instrument).options(selectinload(Instrument.fundamental_data))
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))
        return investments

    async def delete(self, investment: Investment) -> None:
        """Delete investment."""
        if not self._session:
            raise ValueError("Session is not initialized")

        stmt = delete(Instrument).where(Instrument.symbol == investment.symbol)
        await self._session.execute(stmt)
        await self._session.flush()

    async def find_by_market_cap(self, market_cap: str) -> list[Investment]:
        """Find investments by market cap."""
        if not self._session:
            raise ValueError("Session is not initialized")

        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .join(Instrument.fundamental_data)
            .where(
                and_(
                    # Assuming market_cap is stored in fundamental_data
                    # This is a placeholder implementation
                    Instrument.is_active.is_(True)
                )
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))
        return investments

    async def search_by_name(self, name_pattern: str) -> list[Investment]:
        """Search investments by name pattern."""
        if not self._session:
            raise ValueError("Session is not initialized")

        stmt = (
            select(Instrument)
            .options(selectinload(Instrument.fundamental_data))
            .where(
                and_(
                    Instrument.name.ilike(f"%{name_pattern}%"),
                    Instrument.is_active.is_(True),
                )
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        investments = []
        for model in models:
            fundamental_data = (
                model.fundamental_data[0] if model.fundamental_data else None
            )
            investments.append(InvestmentMapper.to_domain(model, fundamental_data))
        return investments
