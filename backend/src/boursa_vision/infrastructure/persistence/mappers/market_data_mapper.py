"""
Market Data Mapper - Domain/Persistence Mapping  
===============================================

Maps between Domain MarketData entities and SQLAlchemy MarketData models.
"""

from datetime import datetime
from decimal import Decimal

from boursa_vision.domain.entities.market_data import MarketData as DomainMarketData
from boursa_vision.infrastructure.persistence.models.market_data_archive import MarketDataArchive


class SimpleMarketDataMapper:
    """Simple mapper for MarketData entities and models."""

    @staticmethod
    def to_domain(model: MarketDataArchive | None) -> DomainMarketData | None:
        """Convert SQLAlchemy MarketDataArchive model to domain MarketData entity."""
        if model is None:
            return None

        # Create basic market data entity - adjust based on your domain model
        return DomainMarketData(
            symbol=model.symbol,
            timestamp=model.timestamp,
            open_price=float(model.open_price) if model.open_price else 0.0,
            high_price=float(model.high_price) if model.high_price else 0.0,
            low_price=float(model.low_price) if model.low_price else 0.0,
            close_price=float(model.close_price) if model.close_price else 0.0,
            volume=model.volume or 0,
            interval_type=model.interval_type,
        )

    @staticmethod
    def to_persistence(domain_data: DomainMarketData | None) -> MarketDataArchive | None:
        """Convert domain MarketData entity to SQLAlchemy MarketDataArchive model."""
        if domain_data is None:
            return None

        return MarketDataArchive(
            symbol=domain_data.symbol,
            timestamp=domain_data.timestamp,
            open_price=Decimal(str(domain_data.open_price)),
            high_price=Decimal(str(domain_data.high_price)),
            low_price=Decimal(str(domain_data.low_price)),
            close_price=Decimal(str(domain_data.close_price)),
            volume=domain_data.volume,
            interval_type=getattr(domain_data, 'interval_type', '1d'),
        )

    @classmethod
    def to_model(cls, domain_data: DomainMarketData | None) -> MarketDataArchive | None:
        """Alias for to_persistence for backward compatibility."""
        return cls.to_persistence(domain_data)
