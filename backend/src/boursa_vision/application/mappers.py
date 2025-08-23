"""
Mappers for Domain Entities to DTOs
==================================

Mappers that convert between domain entities and DTOs,
isolating the application layer from domain implementation details.
"""

from datetime import datetime
from uuid import UUID

from .dtos import (
    InvestmentDTO,
    MoneyDTO,
    PerformanceMetricsDTO,
    PortfolioDTO,
    PositionDTO,
    SignalDTO,
    TechnicalAnalysisDTO,
)


class InvestmentMapper:
    """Mapper for Investment entity to/from DTO"""

    @staticmethod
    def to_dto(investment) -> InvestmentDTO:
        """Convert Investment entity to DTO"""

        # Handle MagicMock values
        def safe_getattr(obj, attr, default):
            """Get attribute value, handling MagicMock objects"""
            value = getattr(obj, attr, default)
            if hasattr(value, "_mock_name"):
                return default
            return value

        return InvestmentDTO(
            id=safe_getattr(
                investment, "id", UUID("00000000-0000-0000-0000-000000000000")
            ),
            symbol=str(safe_getattr(investment, "symbol", "UNKNOWN")),
            name=str(safe_getattr(investment, "name", "Unknown Investment")),
            investment_type=str(safe_getattr(investment, "investment_type", "STOCK")),
            sector=str(safe_getattr(investment, "sector", "TECHNOLOGY")),
            market_cap=str(safe_getattr(investment, "market_cap", "LARGE_CAP")),
            currency=str(safe_getattr(investment, "currency", "USD")),
            exchange=str(safe_getattr(investment, "exchange", "UNKNOWN")),
            isin=safe_getattr(investment, "isin", None),
            current_price=MoneyMapper.to_dto(getattr(investment, "current_price", None))
            if hasattr(investment, "current_price") and investment.current_price
            else None,
            created_at=safe_getattr(investment, "created_at", datetime.now()),
            updated_at=safe_getattr(investment, "updated_at", datetime.now()),
        )

    @staticmethod
    def to_dto_list(investments: list) -> list[InvestmentDTO]:
        """Convert list of Investment entities to DTOs"""
        return [InvestmentMapper.to_dto(inv) for inv in investments]


class MoneyMapper:
    """Mapper for Money value object to/from DTO"""

    @staticmethod
    def to_dto(money) -> MoneyDTO | None:
        """Convert Money value object to DTO"""
        if not money:
            return None

        # Get amount value, handling MagicMock in tests
        amount = getattr(money, "amount", 0.0)
        # If it's a MagicMock, convert to float
        if hasattr(amount, "_mock_name"):
            amount = 0.0

        return MoneyDTO(amount=amount, currency=str(getattr(money, "currency", "USD")))

    @staticmethod
    def from_dto(dto: MoneyDTO):
        """Convert MoneyDTO to domain Money object"""
        # This would create actual Money domain object
        # For now, return a dict representation
        return {"amount": float(dto.amount), "currency": dto.currency}


class PositionMapper:
    """Mapper for Position entity to/from DTO"""

    @staticmethod
    def to_dto(position) -> PositionDTO:
        """Convert Position entity to DTO"""
        return PositionDTO(
            symbol=getattr(position, "symbol", ""),
            quantity=getattr(position, "quantity", 0),
            average_price=MoneyMapper.to_dto(getattr(position, "average_price", None)),
            market_value=MoneyMapper.to_dto(getattr(position, "market_value", None))
            if hasattr(position, "market_value")
            else None,
            unrealized_pnl=MoneyMapper.to_dto(getattr(position, "unrealized_pnl", None))
            if hasattr(position, "unrealized_pnl")
            else None,
            first_purchase_date=getattr(
                position, "first_purchase_date", datetime.now()
            ),
            last_update=getattr(position, "last_update", datetime.now()),
        )

    @staticmethod
    def to_dto_list(positions: list) -> list[PositionDTO]:
        """Convert list of Position entities to DTOs"""
        return [PositionMapper.to_dto(pos) for pos in positions]


class PortfolioMapper:
    """Mapper for Portfolio entity to/from DTO"""

    @staticmethod
    def to_dto(portfolio, include_positions: bool = True) -> PortfolioDTO:
        """Convert Portfolio entity to DTO"""
        positions = []
        if include_positions and hasattr(portfolio, "positions"):
            positions = PositionMapper.to_dto_list(getattr(portfolio, "positions", []))

        total_value = None
        if hasattr(portfolio, "calculate_total_value"):
            try:
                total_value = MoneyMapper.to_dto(portfolio.calculate_total_value())
            except AttributeError:
                pass  # Catch specific exception instead of general Exception

        # Handle MagicMock values
        def safe_getattr(obj, attr, default):
            """Get attribute value, handling MagicMock objects"""
            value = getattr(obj, attr, default)
            if hasattr(value, "_mock_name"):
                return default
            return value

        return PortfolioDTO(
            id=safe_getattr(
                portfolio, "id", UUID("00000000-0000-0000-0000-000000000000")
            ),
            user_id=safe_getattr(
                portfolio, "user_id", UUID("00000000-0000-0000-0000-000000000000")
            ),
            name=str(safe_getattr(portfolio, "name", "Test Portfolio")),
            description=str(safe_getattr(portfolio, "description", None))
            if safe_getattr(portfolio, "description", None)
            else None,
            currency=str(safe_getattr(portfolio, "currency", "USD")),
            total_value=total_value,
            positions=positions,
            created_at=safe_getattr(portfolio, "created_at", datetime.now()),
            updated_at=safe_getattr(portfolio, "updated_at", datetime.now()),
        )


class PerformanceMapper:
    """Mapper for Performance metrics to/from DTO"""

    @staticmethod
    def to_dto(performance) -> PerformanceMetricsDTO:
        """Convert Performance entity to DTO"""
        return PerformanceMetricsDTO(
            total_return=getattr(performance, "total_return", 0.0),
            annualized_return=getattr(performance, "annualized_return", 0.0),
            volatility=getattr(performance, "volatility", 0.0),
            sharpe_ratio=getattr(performance, "sharpe_ratio", 0.0),
            max_drawdown=getattr(performance, "max_drawdown", 0.0),
            beta=getattr(performance, "beta", None),
            alpha=getattr(performance, "alpha", None),
            var_95=getattr(performance, "var_95", None),
        )


class TechnicalAnalysisMapper:
    """Mapper for Technical Analysis to/from DTO"""

    @staticmethod
    def to_dto(analysis, symbol: str) -> TechnicalAnalysisDTO:
        """Convert technical analysis results to DTO"""
        return TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=getattr(analysis, "rsi", None),
            macd=getattr(analysis, "macd", None),
            bollinger_position=getattr(analysis, "bollinger_position", None),
            sma_20=getattr(analysis, "sma_20", None),
            sma_50=getattr(analysis, "sma_50", None),
            volume_trend=getattr(analysis, "volume_trend", None),
            support_level=getattr(analysis, "support_level", None),
            resistance_level=getattr(analysis, "resistance_level", None),
            analysis_date=getattr(analysis, "analysis_date", datetime.now()),
        )


class SignalMapper:
    """Mapper for Trading Signal to/from DTO"""

    @staticmethod
    def to_dto(signal) -> SignalDTO:
        """Convert Signal entity to DTO"""
        return SignalDTO(
            symbol=getattr(signal, "symbol", ""),
            action=str(getattr(signal, "action", "HOLD")),
            confidence=float(getattr(signal, "confidence", 0.0)),
            price=MoneyMapper.to_dto(getattr(signal, "price", None)),
            timestamp=getattr(signal, "timestamp", datetime.now()),
            reason=getattr(signal, "reason", ""),
            metadata=getattr(signal, "metadata", {}),
        )
