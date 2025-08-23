"""
SQLAlchemy models package for the trading platform.
Compatible with Clean Architecture + FastAPI.
"""
# ================================================================
# PLATEFORME TRADING - MODELES SQLALCHEMY
# Compatible avec l'architecture Clean Architecture + FastAPI
# PostgreSQL + TimescaleDB + SQLAlchemy ORM
# ================================================================

from .alerts import Alert, Notification
from .base import Base, DatabaseMixin
from .enums import (
    AlertType,
    ConditionType,
    InstrumentType,
    RiskTolerance,
    SignalStrength,
    SignalType,
    TransactionType,
)
from .fundamental import FundamentalData
from .instruments import Instrument
from .investment import InvestmentModel
from .market_data import (
    MarketData,
    TechnicalIndicator,  # Signal import removed
)
from .market_data_archive import MarketDataArchive
from .performance import PortfolioPerformance
from .portfolios import Portfolio, Position
from .refresh_tokens import RefreshToken
from .system import AuditLog, SystemConfig
from .transactions import Transaction
from .users import User, UserSession

__all__ = [
    "Alert",
    "AlertType",
    "AuditLog",
    # Base
    "Base",
    "ConditionType",
    "DatabaseMixin",
    "FundamentalData",
    "Instrument",
    "InstrumentType",
    "InvestmentModel",
    "MarketData",
    "MarketDataArchive",
    "Notification",
    "Portfolio",
    "PortfolioPerformance",
    "Position",
    "RefreshToken",
    "RiskTolerance",
    "SignalStrength",
    "SignalType",
    "SystemConfig",
    "TechnicalIndicator",
    "Transaction",
    # Enums
    "TransactionType",
    # Models
    "User",
    "UserSession",
]
