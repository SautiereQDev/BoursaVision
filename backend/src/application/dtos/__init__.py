"""
DTOs (Data Transfer Objects) for Application Layer
=================================================

Pydantic models that define the data structures for communication
between the application layer and external interfaces.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..exceptions import InvalidSymbolError, PriceRangeError

# Constants to avoid string duplication
ASSET_SYMBOL_DESC = "Asset symbol"
INVESTMENT_NAME_DESC = "Investment name"
EXCHANGE_NAME_DESC = "Exchange name"
INVESTMENT_TYPE_DESC = "Type of investment"
INVESTMENT_SECTOR_DESC = "Investment sector"
MARKET_CAP_DESC = "Market capitalization category"
TRADING_CURRENCY_DESC = "Trading currency"
PORTFOLIO_NAME_DESC = "Portfolio name"
USER_ID_DESC = "User identifier"
AMOUNT_DESC = "Amount of money"
CURRENCY_CODE_DESC = "Currency code"
QUANTITY_DESC = "Quantity of the position"
AVERAGE_PRICE_DESC = "Average purchase price"
CURRENT_PRICE_DESC = "Current market price"


class BaseDTO(BaseModel):
    """Base DTO with common configuration."""

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
            Decimal: float,
        }


class MoneyDTO(BaseDTO):
    """Money value object DTO."""

    amount: Decimal = Field(..., description=AMOUNT_DESC)
    currency: str = Field(..., description=CURRENCY_CODE_DESC)


class TechnicalAnalysisDTO(BaseDTO):
    """Technical analysis indicators DTO."""

    symbol: str = Field(..., description=ASSET_SYMBOL_DESC)
    rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI indicator")
    macd: Optional[float] = Field(None, description="MACD indicator")
    bollinger_position: Optional[float] = Field(
        None, description="Bollinger Bands position"
    )
    sma_20: Optional[float] = Field(None, description="Simple Moving Average 20")
    sma_50: Optional[float] = Field(None, description="Simple Moving Average 50")
    volume_trend: Optional[float] = Field(None, description="Volume trend indicator")
    support_level: Optional[float] = Field(None, description="Support level")
    resistance_level: Optional[float] = Field(None, description="Resistance level")
    analysis_date: datetime = Field(
        default_factory=datetime.now, description="Analysis timestamp"
    )


class SignalDTO(BaseDTO):
    """Trading signal DTO."""

    symbol: str = Field(..., description=ASSET_SYMBOL_DESC)
    action: str = Field(..., description="Signal action (BUY/SELL/HOLD)")
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence score")
    price: Optional[float] = Field(None, description="Recommended price")
    target_price: Optional[float] = Field(None, description="Target price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    reason: str = Field(..., description="Signal reasoning")
    metadata: Dict[str, Union[str, float, int]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(..., description="Signal timestamp")

    @property
    def reasoning(self) -> str:
        """Alias for reason for backward compatibility."""
        return self.reason


class InvestmentDTO(BaseDTO):
    """Investment entity DTO."""

    id: UUID = Field(..., description="Investment unique identifier")
    symbol: str = Field(..., min_length=1, max_length=10, description=ASSET_SYMBOL_DESC)
    name: str = Field(
        ..., min_length=1, max_length=200, description=INVESTMENT_NAME_DESC
    )
    investment_type: str = Field(..., description=INVESTMENT_TYPE_DESC)
    sector: str = Field(..., description=INVESTMENT_SECTOR_DESC)
    market_cap: str = Field(..., description=MARKET_CAP_DESC)
    currency: str = Field(..., description=TRADING_CURRENCY_DESC)
    exchange: str = Field(
        ..., min_length=1, max_length=50, description=EXCHANGE_NAME_DESC
    )
    current_price: Optional[MoneyDTO] = Field(None, description="Current market price")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PositionDTO(BaseDTO):
    """Portfolio position DTO."""

    id: UUID = Field(..., description="Position unique identifier")
    investment: InvestmentDTO = Field(..., description="Investment details")
    quantity: int = Field(..., ge=0, description=QUANTITY_DESC)
    average_price: MoneyDTO = Field(..., description=AVERAGE_PRICE_DESC)
    current_price: Optional[MoneyDTO] = Field(None, description=CURRENT_PRICE_DESC)
    market_value: Optional[MoneyDTO] = Field(None, description="Current market value")
    unrealized_pnl: Optional[MoneyDTO] = Field(
        None, description="Unrealized profit/loss"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PortfolioDTO(BaseDTO):
    """Portfolio entity DTO."""

    id: UUID = Field(..., description="Portfolio unique identifier")
    name: str = Field(
        ..., min_length=1, max_length=100, description=PORTFOLIO_NAME_DESC
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Portfolio description"
    )
    user_id: UUID = Field(..., description=USER_ID_DESC)
    positions: List[PositionDTO] = Field(
        default_factory=list, description="Portfolio positions"
    )
    total_value: Optional[MoneyDTO] = Field(None, description="Total portfolio value")
    currency: str = Field(..., description="Base currency")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PerformanceMetricsDTO(BaseDTO):
    """Performance metrics DTO."""

    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., description="Volatility percentage")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    beta: Optional[float] = Field(None, description="Beta coefficient")
    alpha: Optional[float] = Field(None, description="Alpha coefficient")
    var_95: Optional[float] = Field(None, description="Value at Risk 95%")


# Request DTOs for use cases
class CreateInvestmentDTO(BaseDTO):
    """Create investment request DTO."""

    symbol: str = Field(..., min_length=1, max_length=10, description=ASSET_SYMBOL_DESC)
    name: str = Field(
        ..., min_length=1, max_length=200, description=INVESTMENT_NAME_DESC
    )
    investment_type: str = Field(..., description=INVESTMENT_TYPE_DESC)
    sector: str = Field(..., description=INVESTMENT_SECTOR_DESC)
    market_cap: str = Field(..., description=MARKET_CAP_DESC)
    currency: str = Field(..., description=TRADING_CURRENCY_DESC)
    exchange: str = Field(
        ..., min_length=1, max_length=50, description=EXCHANGE_NAME_DESC
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        if not v.isalnum():
            raise InvalidSymbolError(v)
        return v.upper()


class CreatePortfolioDTO(BaseDTO):
    """Create portfolio request DTO."""

    name: str = Field(
        ..., min_length=1, max_length=100, description=PORTFOLIO_NAME_DESC
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Portfolio description"
    )
    user_id: UUID = Field(..., description=USER_ID_DESC)
    currency: str = Field(default="USD", description="Base currency")


class FindInvestmentsRequestDTO(BaseDTO):
    """Find investments request DTO."""

    symbol: Optional[str] = Field(None, description=ASSET_SYMBOL_DESC)
    investment_type: Optional[str] = Field(None, description=INVESTMENT_TYPE_DESC)
    sector: Optional[str] = Field(None, description=INVESTMENT_SECTOR_DESC)
    market_cap: Optional[str] = Field(None, description=MARKET_CAP_DESC)
    exchange: Optional[str] = Field(None, description=EXCHANGE_NAME_DESC)
    min_price: Optional[float] = Field(None, gt=0, description="Minimum price")
    max_price: Optional[float] = Field(None, gt=0, description="Maximum price")
    include_technical_analysis: bool = Field(
        default=True, description="Include technical analysis"
    )
    include_signals: bool = Field(default=True, description="Include trading signals")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset")

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, v: Optional[float], info) -> Optional[float]:
        """Validate price range."""
        if (
            v is not None
            and "min_price" in info.data
            and info.data["min_price"] is not None
            and v <= info.data["min_price"]
        ):
            raise PriceRangeError()
        return v


class AnalyzePortfolioRequestDTO(BaseDTO):
    """Analyze portfolio request DTO."""

    portfolio_id: UUID = Field(..., description="Portfolio identifier")
    include_performance_metrics: bool = Field(
        default=True, description="Include performance metrics"
    )
    include_risk_analysis: bool = Field(
        default=True, description="Include risk analysis"
    )
    include_recommendations: bool = Field(
        default=True, description="Include recommendations"
    )
    benchmark_symbol: Optional[str] = Field(
        None, description="Benchmark symbol for comparison"
    )


class FindInvestmentsResponseDTO(BaseDTO):
    """Find investments response DTO."""

    investments: List[InvestmentDTO] = Field(..., description="Found investments")
    technical_analysis: Dict[str, TechnicalAnalysisDTO] = Field(
        default_factory=dict, description="Technical analysis by symbol"
    )
    signals: Dict[str, SignalDTO] = Field(
        default_factory=dict, description="Trading signals by symbol"
    )
    total_count: int = Field(..., description="Total number of matching investments")
    has_more: bool = Field(..., description="Whether more results are available")


class AnalyzePortfolioResponseDTO(BaseDTO):
    """Analyze portfolio response DTO."""

    portfolio: PortfolioDTO = Field(..., description="Portfolio details")
    performance_metrics: Optional[PerformanceMetricsDTO] = Field(
        None, description="Performance metrics"
    )
    risk_analysis: Optional[Dict[str, Union[str, float]]] = Field(
        None, description="Risk analysis"
    )
    asset_allocation: Optional[Dict[str, float]] = Field(
        None, description="Asset allocation percentages"
    )
    recommendations: Optional[List[str]] = Field(
        None, description="Investment recommendations"
    )
    signals: Optional[List[SignalDTO]] = Field(
        None, description="Trading signals for positions"
    )


# Additional DTOs for missing types
class InvestmentSearchResultDTO(BaseModel):
    """Investment search result DTO."""

    investments: List[InvestmentDTO]
    total_count: int
    page: int = 1
    page_size: int = 50
    technical_analysis: List[TechnicalAnalysisDTO] = Field(default_factory=list)
    signals: List[SignalDTO] = Field(default_factory=list)


class PortfolioAnalysisResultDTO(BaseModel):
    """Portfolio analysis result DTO."""

    portfolio: PortfolioDTO
    performance_metrics: PerformanceMetricsDTO
    risk_metrics: Dict[str, float] = Field(default_factory=dict)
    allocation: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    signals: List[SignalDTO] = Field(default_factory=list)
    analysis_date: datetime = Field(default_factory=datetime.now)

    # Additional fields for test compatibility
    @property
    def performance(self):
        """Access performance metrics via .performance attribute."""
        return self.performance_metrics

    @property
    def risk(self):
        """Access risk metrics via .risk attribute."""
        return self.risk_metrics


# ============================================================================
# RISK ASSESSMENT DTOs
# ============================================================================

class RiskFactorDTO(BaseModel):
    """DTO pour un facteur de risque individuel"""
    name: str
    category: str  # MARKET, FUNDAMENTAL, GEOPOLITICAL, ESG, etc.
    level: str  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH, CRITICAL
    score: float  # 0-100
    description: str
    impact: str  # LOW, MEDIUM, HIGH
    probability: str  # LOW, MEDIUM, HIGH
    timeframe: str  # SHORT, MEDIUM, LONG
    source: str
    last_updated: datetime


class GeopoliticalRiskDTO(BaseModel):
    """DTO pour les risques géopolitiques"""
    country_risk: Optional[RiskFactorDTO] = None
    sector_risk: Optional[RiskFactorDTO] = None
    international_exposure: Optional[RiskFactorDTO] = None
    regulatory_risk: Optional[RiskFactorDTO] = None
    trade_war_impact: Optional[RiskFactorDTO] = None
    sanctions_risk: Optional[RiskFactorDTO] = None


class FundamentalRiskDTO(BaseModel):
    """DTO pour les risques fondamentaux"""
    debt_risk: Optional[RiskFactorDTO] = None
    liquidity_risk: Optional[RiskFactorDTO] = None
    profitability_risk: Optional[RiskFactorDTO] = None
    valuation_risk: Optional[RiskFactorDTO] = None
    growth_risk: Optional[RiskFactorDTO] = None
    revenue_quality_risk: Optional[RiskFactorDTO] = None
    competitive_position_risk: Optional[RiskFactorDTO] = None


class MarketRiskDTO(BaseModel):
    """DTO pour les risques de marché"""
    volatility_risk: Optional[RiskFactorDTO] = None
    beta_risk: Optional[RiskFactorDTO] = None
    correlation_risk: Optional[RiskFactorDTO] = None
    drawdown_risk: Optional[RiskFactorDTO] = None
    liquidity_risk: Optional[RiskFactorDTO] = None
    concentration_risk: Optional[RiskFactorDTO] = None


class ESGRiskDTO(BaseModel):
    """DTO pour les risques ESG"""
    environmental_risk: Optional[RiskFactorDTO] = None
    social_risk: Optional[RiskFactorDTO] = None
    governance_risk: Optional[RiskFactorDTO] = None
    sustainability_risk: Optional[RiskFactorDTO] = None
    reputation_risk: Optional[RiskFactorDTO] = None


class RiskAssessmentDTO(BaseModel):
    """DTO pour l'évaluation complète des risques"""
    symbol: str
    overall_risk_score: float  # 0-100
    overall_risk_level: str  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH, CRITICAL
    total_risk_factors: int
    critical_risk_count: int
    
    # Risques par catégorie
    market_risks: MarketRiskDTO = Field(default_factory=MarketRiskDTO)
    fundamental_risks: FundamentalRiskDTO = Field(default_factory=FundamentalRiskDTO)
    geopolitical_risks: GeopoliticalRiskDTO = Field(default_factory=GeopoliticalRiskDTO)
    esg_risks: ESGRiskDTO = Field(default_factory=ESGRiskDTO)
    
    # Groupement par catégorie
    risks_by_category: Dict[str, List[RiskFactorDTO]] = Field(default_factory=dict)
    
    # Tous les facteurs de risque
    all_risk_factors: List[RiskFactorDTO] = Field(default_factory=list)
    
    # Métadonnées
    analysis_timestamp: datetime
    summary: str
    
    # Recommandations basées sur les risques
    risk_mitigation_strategies: List[str] = Field(default_factory=list)
    monitoring_recommendations: List[str] = Field(default_factory=list)


class ComprehensiveInvestmentAnalysisDTO(BaseModel):
    """DTO pour une analyse complète d'investissement incluant les risques"""
    symbol: str
    name: str
    
    # Analyses existantes
    technical_analysis: Optional[TechnicalAnalysisDTO] = None
    signal: Optional[SignalDTO] = None
    
    # Nouvelle analyse des risques
    risk_assessment: Optional[RiskAssessmentDTO] = None
    
    # Score global combiné
    overall_investment_score: float  # 0-100
    investment_recommendation: str  # BUY, HOLD, SELL
    confidence_level: str  # LOW, MEDIUM, HIGH
    
    # Résumé exécutif
    executive_summary: str
    key_opportunities: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    
    # Métadonnées
    analysis_date: datetime
    analyst_notes: Optional[str] = None
