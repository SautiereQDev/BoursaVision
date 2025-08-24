"""
Investment Mapper - Domain/Persistence Mapping
=============================================

Maps between Domain Investment entities and SQLAlchemy Investment models.
"""

from boursa_vision.domain.entities.investment import Investment as DomainInvestment
from boursa_vision.infrastructure.persistence.models.investment import InvestmentModel


class SimpleInvestmentMapper:
    """Simple mapper for Investment entities and models."""

    @staticmethod
    def to_domain(model: InvestmentModel | None) -> DomainInvestment | None:
        """Convert SQLAlchemy Investment model to domain Investment entity."""
        if model is None:
            return None

        # Create basic investment entity - adjust based on your domain model
        return DomainInvestment(
            id=model.id,
            portfolio_id=model.portfolio_id,
            symbol=model.symbol,
            quantity=model.quantity,
            average_price=model.average_price,
            created_at=model.created_at,
        )

    @staticmethod
    def to_persistence(domain_investment: DomainInvestment | None) -> InvestmentModel | None:
        """Convert domain Investment entity to SQLAlchemy Investment model."""
        if domain_investment is None:
            return None

        return InvestmentModel(
            id=domain_investment.id,
            portfolio_id=domain_investment.portfolio_id,
            symbol=domain_investment.symbol,
            quantity=domain_investment.quantity,
            average_price=domain_investment.average_price,
            created_at=domain_investment.created_at,
        )

    @classmethod
    def to_model(cls, domain_investment: DomainInvestment | None) -> InvestmentModel | None:
        """Alias for to_persistence for backward compatibility."""
        return cls.to_persistence(domain_investment)
