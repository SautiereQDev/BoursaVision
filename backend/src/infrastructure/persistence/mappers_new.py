"""
Domain to Persistence mappers for the trading platform.

This module provides mapping between domain entities and SQLAlchemy models,
ensuring clean separation between business logic and persistence concerns.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from ...domain.entities.investment import Investment
from ...domain.entities.market_data import MarketData as DomainMarketData
from ...domain.entities.portfolio import Portfolio as DomainPortfolio
from ...domain.entities.portfolio import Position as DomainPosition
from ...domain.entities.user import User as DomainUser
from ...domain.entities.user import UserRole
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.price import Price
from .models import Instrument, MarketData, Portfolio, Position, User


class UserMapper:
    """Mapper for User domain entity ↔ SQLAlchemy model."""

    @staticmethod
    def to_domain(model: User) -> DomainUser:
        """Convert SQLAlchemy User model to domain User entity."""
        return DomainUser(
            id=model.id,
            email=model.email,
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            role=UserRole(model.role.lower()) if model.role else UserRole.VIEWER,
            preferred_currency=Currency.USD,  # Default for now
            is_active=model.is_active,
            email_verified=model.is_verified,
            created_at=model.created_at,
            last_login=model.last_login_at,
        )

    @staticmethod
    def to_persistence(entity: DomainUser) -> User:
        """Convert domain User entity to SQLAlchemy User model."""
        return User(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role.value.upper(),
            password_hash=(
                "$2b$12$dummy.hash.for.development.purposes.only"
            ),  # Default hash for development
            is_active=entity.is_active,
            is_verified=entity.email_verified,
            created_at=entity.created_at,
            last_login_at=entity.last_login,
        )

    @staticmethod
    def update_model(model: User, entity: DomainUser) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.email = entity.email
        model.username = entity.username
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.role = entity.role
        model.preferred_currency = entity.preferred_currency.value
        model.is_active = entity.is_active
        model.email_verified = entity.email_verified
        model.two_factor_enabled = entity.two_factor_enabled
        model.last_login = entity.last_login


class PortfolioMapper:
    """Mapper for Portfolio domain entity ↔ SQLAlchemy model."""

    @staticmethod
    def to_domain(model: Portfolio) -> DomainPortfolio:
        """Convert SQLAlchemy Portfolio model to domain Portfolio entity."""
        # Only pass supported arguments to Portfolio.create
        return DomainPortfolio.create(
            user_id=model.user_id,
            name=model.name,
            base_currency=Currency(model.base_currency),
            initial_cash=Money(model.initial_cash, Currency(model.base_currency)),
        )

    @staticmethod
    def to_model(entity: DomainPortfolio) -> Portfolio:
        """Convert domain Portfolio entity to SQLAlchemy Portfolio model."""
        return Portfolio(
            id=entity.id,
            user_id=entity.user_id,
            name=entity.name,
            description=entity.description,
            base_currency=entity.base_currency.value,
            initial_cash=entity.initial_cash.amount,
            current_cash=entity.current_cash.amount,
            total_invested=entity.total_invested.amount,
            total_value=entity.total_value.amount,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def update_model(model: Portfolio, entity: DomainPortfolio) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.name = entity.name
        model.description = entity.description
        model.base_currency = entity.base_currency.value
        model.initial_cash = entity.initial_cash.amount
        model.current_cash = entity.current_cash.amount
        model.total_invested = entity.total_invested.amount
        model.total_value = entity.total_value.amount
        model.updated_at = entity.updated_at


class MarketDataMapper:
    """Mapper for MarketData domain entity ↔ SQLAlchemy model."""

    @staticmethod
    def to_domain(model: MarketData) -> DomainMarketData:
        """Convert SQLAlchemy MarketData model to domain MarketData entity."""
        currency = Currency.USD  # Default currency, should be retrieved from instrument
        from ...domain.entities.market_data import MarketDataArgs, Timeframe, DataSource
        args = MarketDataArgs(
            symbol=model.symbol,
            timestamp=model.time,
            open_price=model.open_price,
            high_price=model.high_price,
            low_price=model.low_price,
            close_price=model.close_price,
            volume=model.volume,
            timeframe=Timeframe.DAY_1 if not hasattr(model, 'interval_type') else Timeframe(model.interval_type),
            source=DataSource.YAHOO_FINANCE if not hasattr(model, 'source') else DataSource(model.source),
            currency=currency,
            adjusted_close=getattr(model, 'adjusted_close', None),
            dividend_amount=getattr(model, 'dividend_amount', None),
            split_coefficient=getattr(model, 'split_coefficient', None),
        )
        return DomainMarketData.create(args)

    @staticmethod
    def to_model(entity: DomainMarketData) -> MarketData:
        """Convert domain MarketData entity to SQLAlchemy MarketData model."""
        return MarketData(
            time=entity.timestamp,
            symbol=entity.symbol,
            interval_type=entity.interval_type,
            open_price=entity.open_price.amount,
            high_price=entity.high_price.amount,
            low_price=entity.low_price.amount,
            close_price=entity.close_price.amount,
            adjusted_close=entity.close_price.amount,  # Assuming same as close for simplicity
            volume=entity.volume,
            source=entity.source,
        )


class InvestmentMapper:
    """Mapper for Investment domain entity ↔ SQLAlchemy models."""

    @staticmethod
    def to_domain(instrument_model: Instrument, fundamental_data=None) -> Investment:
        """Convert SQLAlchemy models to domain Investment entity."""
        return Investment.create(
            symbol=instrument_model.symbol,
            name=instrument_model.name,
            instrument_type=instrument_model.instrument_type,
            exchange=instrument_model.exchange,
            currency=Currency(instrument_model.currency)
            if instrument_model.currency
            else Currency.USD,
            sector=instrument_model.sector,
            industry=instrument_model.industry,
        )

    @staticmethod
    def to_persistence(entity: Investment) -> "InvestmentModel":
        """Convert domain Investment entity to SQLAlchemy InvestmentModel."""
        from .models.investment import InvestmentModel
        return InvestmentModel(
            symbol=entity.symbol,
            name=entity.name,
            exchange=entity.exchange,
            sector=entity.sector.value if hasattr(entity.sector, 'value') else str(entity.sector),
            industry=getattr(entity, 'industry', None),
            market_cap=getattr(entity, 'market_cap', None),
            description=getattr(entity, 'description', None),
        )

    @staticmethod
    def update_instrument_model(model: Instrument, entity: Investment) -> None:
        """Update SQLAlchemy Instrument model from domain Investment entity."""
        model.symbol = entity.symbol
        model.name = entity.name
        model.instrument_type = entity.instrument_type
        model.exchange = entity.exchange
        model.currency = entity.currency.value
        model.sector = entity.sector
        model.industry = entity.industry
        model.is_active = True  # Assume active when updating from domain
