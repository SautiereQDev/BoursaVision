"""
Portfolio Mapper - Domain/Persistence Mapping
=============================================

Maps between Domain Portfolio entities and SQLAlchemy Portfolio models.
"""

from typing import Optional

from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.value_objects.money import Money, Currency
from boursa_vision.infrastructure.persistence.models.portfolios import Portfolio as PortfolioModel


class SimplePortfolioMapper:
    """Simple mapper for Portfolio entities and models."""

    @staticmethod
    def to_domain(model: Optional[PortfolioModel]) -> Optional[DomainPortfolio]:
        """Convert SQLAlchemy Portfolio model to domain Portfolio entity."""
        if model is None:
            return None

        # Create Money object for cash balance with default values
        cash_balance = Money(
            amount=getattr(model, 'cash_balance', 0.0), 
            currency=Currency(getattr(model, 'base_currency', 'USD'))
        )
        
        return DomainPortfolio(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            base_currency=getattr(model, 'base_currency', 'USD'),
            cash_balance=cash_balance,
            created_at=model.created_at,
        )

    @staticmethod
    def to_persistence(domain_portfolio: Optional[DomainPortfolio]) -> Optional[PortfolioModel]:
        """Convert domain Portfolio entity to SQLAlchemy Portfolio model."""
        if domain_portfolio is None:
            return None

        return PortfolioModel(
            id=domain_portfolio.id,
            user_id=domain_portfolio.user_id,
            name=domain_portfolio.name,
            base_currency=domain_portfolio.base_currency,
            cash_balance=float(domain_portfolio.cash_balance.amount),
            created_at=domain_portfolio.created_at,
        )

    @classmethod
    def to_model(cls, domain_portfolio: Optional[DomainPortfolio]) -> Optional[PortfolioModel]:
        """Alias for to_persistence for test compatibility."""
        return cls.to_persistence(domain_portfolio)
