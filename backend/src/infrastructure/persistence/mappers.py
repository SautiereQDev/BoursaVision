"""
Domain to Persistence mappers following the Repository pattern.
Implements Clean Architecture principles with SQLAlchemy models.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.investment import Investment
from src.domain.entities.market_data import MarketData as DomainMarketData
from src.domain.entities.portfolio import Portfolio as DomainPortfolio
from src.domain.entities.portfolio import Position as DomainPosition
from src.domain.entities.user import User as DomainUser
from src.domain.value_objects.money import Currency, Money
from src.domain.value_objects.price import Price
from src.infrastructure.persistence.models.instruments import Instrument
from src.infrastructure.persistence.models.market_data import (
    MarketData,
    TechnicalIndicator,
)
from src.infrastructure.persistence.models.portfolios import Portfolio, Position
from src.infrastructure.persistence.models.users import User


class BaseMapper(ABC):
    """Base mapper interface for domain to persistence conversion."""

    @abstractmethod
    def to_domain(self, persistence_model):
        """Convert persistence model to domain entity."""
        pass

    @abstractmethod
    def to_persistence(self, domain_entity):
        """Convert domain entity to persistence model."""
        pass


class UserMapper(BaseMapper):
    """Mapper for User entity and model."""

    def to_domain(self, user_model: User) -> DomainUser:
        """Convert User model to domain entity."""
        from src.domain.entities.user import UserRole

        return DomainUser.create(
            email=user_model.email,
            username=user_model.username or "",
            first_name=user_model.first_name or "",
            last_name=user_model.last_name or "",
            role=UserRole(user_model.role) if user_model.role else UserRole.VIEWER,
            preferred_currency=Currency(user_model.preferred_currency)
            if user_model.preferred_currency
            else Currency.USD,
        )

    def to_persistence(self, user: DomainUser) -> Dict:
        """Convert domain User to persistence data."""
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "preferred_currency": user.preferred_currency.value,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "created_at": user.created_at,
            "last_login": user.last_login,
        }


class PortfolioMapper(BaseMapper):
    """Mapper for Portfolio entity and model."""

    def to_domain(self, portfolio_model: Portfolio) -> DomainPortfolio:
        """Convert Portfolio model to domain entity."""
        return DomainPortfolio.create(
            user_id=portfolio_model.user_id,
            name=portfolio_model.name,
            base_currency=Currency(portfolio_model.base_currency),
            initial_cash=Money(
                amount=portfolio_model.initial_cash,
                currency=Currency(portfolio_model.base_currency),
            ),
        )

    def to_persistence(self, portfolio: DomainPortfolio) -> Dict:
        """Convert domain Portfolio to persistence data."""
        return {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "description": getattr(portfolio, "description", None),
            "base_currency": portfolio.base_currency.value,
            "initial_cash": portfolio.initial_cash.amount,
            "current_cash": portfolio.current_cash.amount,
            "total_invested": Decimal("0.0000"),  # Calculate from positions
            "total_value": Decimal("0.0000"),  # Calculate from positions + cash
            "created_at": portfolio.created_at,
            "updated_at": getattr(portfolio, "updated_at", datetime.utcnow()),
        }


class PositionMapper(BaseMapper):
    """Mapper for Position entity and model."""

    def to_domain(self, position_model: Position) -> DomainPosition:
        """Convert Position model to domain entity."""
        return DomainPosition(
            portfolio_id=position_model.portfolio_id,
            instrument_id=position_model.instrument_id,
            symbol=position_model.symbol,
            quantity=position_model.quantity,
            average_cost=Money(
                amount=position_model.average_cost,
                currency=Currency(position_model.currency),
            ),
            current_price=Money(
                amount=position_model.current_price or Decimal("0"),
                currency=Currency(position_model.currency),
            ),
        )

    def to_persistence(self, position: DomainPosition) -> Dict:
        """Convert domain Position to persistence data."""
        return {
            "portfolio_id": position.portfolio_id,
            "instrument_id": position.instrument_id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_cost": position.average_cost.amount,
            "current_price": position.current_price.amount
            if position.current_price
            else None,
            "currency": position.average_cost.currency.value,
            "market_value": position.calculate_market_value().amount
            if position.current_price
            else None,
            "unrealized_pnl": position.calculate_unrealized_pnl().amount
            if position.current_price
            else None,
            "updated_at": datetime.utcnow(),
        }


class MarketDataMapper(BaseMapper):
    """Mapper for MarketData entity and model."""

    def to_domain(self, market_data_model: MarketData) -> DomainMarketData:
        """Convert MarketData model to domain entity."""
        return DomainMarketData.create(
            symbol=market_data_model.symbol,
            timestamp=market_data_model.time,
            prices={
                "open": Price(market_data_model.open_price, Currency.USD),
                "high": Price(market_data_model.high_price, Currency.USD),
                "low": Price(market_data_model.low_price, Currency.USD),
                "close": Price(market_data_model.close_price, Currency.USD),
                "adjusted_close": Price(market_data_model.adjusted_close, Currency.USD),
            },
            volume=int(market_data_model.volume or 0),
            source=market_data_model.source or "unknown",
        )

    def to_persistence(self, market_data: DomainMarketData) -> Dict:
        """Convert domain MarketData to persistence data."""
        return {
            "time": market_data.timestamp,
            "symbol": market_data.symbol,
            "interval_type": getattr(market_data, "interval_type", "1d"),
            "open_price": market_data.prices["open"].amount,
            "high_price": market_data.prices["high"].amount,
            "low_price": market_data.prices["low"].amount,
            "close_price": market_data.prices["close"].amount,
            "adjusted_close": market_data.prices["adjusted_close"].amount,
            "volume": market_data.volume,
            "source": market_data.source,
            "created_at": datetime.utcnow(),
        }


class InvestmentMapper(BaseMapper):
    """Mapper for Investment entity and model."""

    def to_domain(self, instrument_model: Instrument) -> Investment:
        """Convert Instrument model to domain Investment entity."""
        return Investment.create(
            symbol=instrument_model.symbol,
            name=instrument_model.name or "",
            instrument_type=instrument_model.instrument_type,
            exchange=instrument_model.exchange or "",
            currency=Currency(instrument_model.currency)
            if instrument_model.currency
            else Currency.USD,
        )

    def to_persistence(self, investment: Investment) -> Dict:
        """Convert domain Investment to persistence Instrument data."""
        return {
            "id": investment.id,
            "symbol": investment.symbol,
            "name": investment.name,
            "instrument_type": investment.instrument_type,
            "exchange": investment.exchange,
            "currency": investment.currency.value,
            "sector": getattr(investment, "sector", None),
            "industry": getattr(investment, "industry", None),
            "country": getattr(investment, "country", None),
            "description": getattr(investment, "description", None),
            "is_active": True,
            "created_at": getattr(investment, "created_at", datetime.utcnow()),
            "updated_at": datetime.utcnow(),
        }


# Mapper factory for dependency injection
class MapperFactory:
    """Factory for creating mappers."""

    _mappers = {
        "user": UserMapper(),
        "portfolio": PortfolioMapper(),
        "position": PositionMapper(),
        "market_data": MarketDataMapper(),
        "investment": InvestmentMapper(),
    }

    @classmethod
    def get_mapper(cls, entity_type: str) -> BaseMapper:
        """Get mapper for entity type."""
        if entity_type not in cls._mappers:
            raise ValueError(f"No mapper found for entity type: {entity_type}")
        return cls._mappers[entity_type]

    @classmethod
    def register_mapper(cls, entity_type: str, mapper: BaseMapper) -> None:
        """Register a new mapper."""
        cls._mappers[entity_type] = mapper
