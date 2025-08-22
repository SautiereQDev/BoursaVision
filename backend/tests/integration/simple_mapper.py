"""
Simple Investment Mapper for Integration Tests
==============================================

Mapper simplifié pour les tests d'intégration,
compatible avec InvestmentModel et les fixtures de test.
"""

from boursa_vision.domain.entities.investment import Investment
from boursa_vision.infrastructure.persistence.models.investment import InvestmentModel


class SimpleInvestmentMapper:
    """Mapper simplifié pour les tests d'intégration."""

    def to_domain(self, model: InvestmentModel) -> Investment:
        """Convert SQLAlchemy InvestmentModel to domain Investment."""
        return Investment.create(
            symbol=model.symbol,
            name=model.name,
            exchange=model.exchange,
            sector=model.sector or "Technology",  # Default pour les tests
            industry=model.industry or "Software",  # Default pour les tests
        )

    def to_persistence(self, entity: Investment) -> InvestmentModel:
        """Convert domain Investment to SQLAlchemy InvestmentModel."""
        return InvestmentModel(
            symbol=entity.symbol,
            name=entity.name,
            exchange=entity.exchange,
            sector=entity.sector.value if hasattr(entity.sector, "value") else str(entity.sector),
            industry=getattr(entity, "industry", None),
            market_cap=getattr(entity, "market_cap", None),
            description=getattr(entity, "description", None),
        )
