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
from .market_data import TechnicalIndicator  # Signal import removed
from .market_data import MarketData
from .performance import PortfolioPerformance
from .portfolios import Portfolio, Position
from .system import AuditLog, SystemConfig
from .transactions import Transaction
from .users import User, UserSession

__all__ = [
    # Base
    "Base",
    "DatabaseMixin",
    # Enums
    "TransactionType",
    "InstrumentType",
    "SignalType",
    "SignalStrength",
    "RiskTolerance",
    "AlertType",
    "ConditionType",
    # Models
    "User",
    "UserSession",
    "Portfolio",
    "Position",
    "Instrument",
    "InvestmentModel",
    "Transaction",
    "MarketData",
    "TechnicalIndicator",
    "Alert",
    "Notification",
    "FundamentalData",
    "PortfolioPerformance",
    "AuditLog",
    "SystemConfig",
]
