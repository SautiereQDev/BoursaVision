"""
Portfolio Mapper - Complete Financial Schema Mapping
==================================================

Maps between Domain Portfolio entities and SQLAlchemy Portfolio models
with full financial tracking capabilities.
"""

from decimal import Decimal

from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.value_objects.money import Currency, Money
from boursa_vision.infrastructure.persistence.models.portfolios import (
    Portfolio as PortfolioModel,
)


class CompletePortfolioMapper:
    """Complete mapper for Portfolio entities with all financial fields."""

    @staticmethod
    def to_domain(model: PortfolioModel | None) -> DomainPortfolio | None:
        """Convert SQLAlchemy Portfolio model to domain Portfolio entity."""
        if model is None:
            return None

        # Map current_cash to cash_balance for domain entity
        cash_balance = Money(
            amount=getattr(model, "current_cash", Decimal("0.0000")),
            currency=Currency(getattr(model, "base_currency", "USD")),
        )

        return DomainPortfolio(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            base_currency=getattr(model, "base_currency", "USD"),
            cash_balance=cash_balance,
            created_at=model.created_at,
        )

    @staticmethod
    def to_persistence(
        domain_portfolio: DomainPortfolio | None,
    ) -> PortfolioModel | None:
        """Convert domain Portfolio entity to SQLAlchemy Portfolio model."""
        if domain_portfolio is None:
            return None

        # Map cash_balance to current_cash and set defaults for financial fields
        return PortfolioModel(
            id=domain_portfolio.id,
            user_id=domain_portfolio.user_id,
            name=domain_portfolio.name,
            base_currency=domain_portfolio.base_currency,
            description=getattr(domain_portfolio, "description", None),
            # Financial fields - set defaults for new portfolios
            initial_cash=float(domain_portfolio.cash_balance.amount),
            current_cash=float(domain_portfolio.cash_balance.amount),
            total_invested=Decimal("0.0000"),
            total_value=float(domain_portfolio.cash_balance.amount),
            daily_pnl=Decimal("0.0000"),
            total_pnl=Decimal("0.0000"),
            daily_return_pct=Decimal("0.0000"),
            total_return_pct=Decimal("0.0000"),
            is_default=False,
            is_active=getattr(domain_portfolio, "is_active", True),
            created_at=domain_portfolio.created_at,
        )

    @staticmethod
    def update_model(model: PortfolioModel, domain_portfolio: DomainPortfolio) -> None:
        """Update existing SQLAlchemy model with domain entity data."""
        model.name = domain_portfolio.name
        model.base_currency = domain_portfolio.base_currency
        model.description = getattr(domain_portfolio, "description", model.description)
        model.current_cash = float(domain_portfolio.cash_balance.amount)
        model.is_active = getattr(domain_portfolio, "is_active", model.is_active)
        # Note: Don't update created_at, but updated_at will be updated automatically

    @classmethod
    def to_model(
        cls, domain_portfolio: DomainPortfolio | None
    ) -> PortfolioModel | None:
        """Alias for to_persistence for backward compatibility."""
        return cls.to_persistence(domain_portfolio)


# Backward compatibility alias
SimplePortfolioMapper = CompletePortfolioMapper
