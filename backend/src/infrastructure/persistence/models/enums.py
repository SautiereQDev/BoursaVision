# ================================================================
# PLATEFORME TRADING - ENUMERATIONS
# Enums utilisés dans les modèles SQLAlchemy
# ================================================================

from enum import Enum


class TransactionType(str, Enum):
    """Types de transactions financières"""

    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    SPIN_OFF = "SPIN_OFF"


class InstrumentType(str, Enum):
    """Types d'instruments financiers"""

    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"


class SignalType(str, Enum):
    """Types de signaux d'investissement"""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(str, Enum):
    """Force des signaux d'investissement"""

    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class RiskTolerance(str, Enum):
    """Tolérance au risque des utilisateurs"""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class AlertType(str, Enum):
    """Types d'alertes"""

    PRICE = "PRICE"
    VOLUME = "VOLUME"
    SIGNAL = "SIGNAL"
    PORTFOLIO = "PORTFOLIO"


class ConditionType(str, Enum):
    """Types de conditions pour les alertes"""

    ABOVE = "ABOVE"
    BELOW = "BELOW"
    EQUALS = "EQUALS"
    CHANGE_PCT = "CHANGE_PCT"
