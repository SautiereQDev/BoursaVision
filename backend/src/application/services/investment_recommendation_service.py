"""Investment Recommendation Service with portfolio optimization."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .advanced_analysis_service import (
    AdvancedInvestmentAnalyzer,
    ComprehensiveAnalysisResult,
)


@dataclass
class RecommendationRequest:
    """Request for investment recommendations."""

    symbols: Optional[List[str]] = None  # If None, use all available symbols
    max_recommendations: int = 10
    risk_tolerance: str = "MODERATE"  # LOW, MODERATE, HIGH
    investment_horizon: str = "MEDIUM"  # SHORT, MEDIUM, LONG
    exclude_sectors: List[str] = field(default_factory=list)
    min_score: float = 60.0
    max_risk_level: str = "HIGH"  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH


@dataclass
class InvestmentRecommendation:
    """Single investment recommendation."""

    symbol: str
    name: str
    current_price: float
    currency: str
    recommendation: str
    overall_score: float
    confidence: float
    risk_level: str

    # Detailed scores
    technical_score: float
    fundamental_score: float
    momentum_score: float

    # Price targets
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    upside_potential: Optional[float] = None

    # Analysis details
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)

    # Metadata
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_quality: str = "GOOD"  # EXCELLENT, GOOD, FAIR, POOR


@dataclass
class PortfolioRecommendation:
    """Complete portfolio recommendation with multiple investments."""

    recommendations: List[InvestmentRecommendation]
    portfolio_metrics: Dict[str, Any]
    analysis_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    sector_allocation: Dict[str, float]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InvestmentRecommendationService:
    """Service for generating investment recommendations."""

    # Financial indices symbols
    INDICES_SYMBOLS = {
        "cac40": [
            "MC.PA",
            "ASML.AS",
            "OR.PA",
            "SAP",
            "TTE.PA",
            "RMS.PA",
            "INGA.AS",
            "SAN.PA",
            "BNP.PA",
            "AIR.PA",
            "SU.PA",
            "BN.PA",
            "DG.PA",
            "EL.PA",
            "CAP.PA",
            "ML.PA",
            "ORA.PA",
            "AI.PA",
            "GLE.PA",
            "LR.PA",
            "VIV.PA",
            "KER.PA",
            "PUB.PA",
            "URW.AS",
            "STM.PA",
            "TEP.PA",
            "WLN.PA",
            "EN.PA",
            "ACA.PA",
            "CS.PA",
            "BIO.PA",
            "SGO.PA",
            "SW.PA",
            "ALO.PA",
            "HO.PA",
            "ATO.PA",
            "RCO.PA",
            "DBG.PA",
            "STLA.PA",
            "EDF.PA",
        ],
        "nasdaq100": [
            "AAPL",
            "MSFT",
            "AMZN",
            "NVDA",
            "GOOGL",
            "GOOG",
            "META",
            "TSLA",
            "AVGO",
            "COST",
            "NFLX",
            "TMUS",
            "ASML",
            "ADBE",
            "PEP",
            "CSCO",
            "LIN",
            "TXN",
            "QCOM",
            "CMCSA",
            "AMAT",
            "AMD",
            "AMGN",
            "HON",
            "INTU",
            "ISRG",
            "BKNG",
            "VRTX",
            "ADP",
            "SBUX",
            "GILD",
            "ADI",
            "MU",
            "INTC",
            "PYPL",
            "REGN",
            "MELI",
            "LRCX",
            "KLAC",
            "SNPS",
            "CDNS",
            "MRVL",
            "ORLY",
            "CSX",
            "FTNT",
            "ADSK",
            "NXPI",
            "WDAY",
            "ABNB",
            "CHTR",
            "TEAM",
            "PCAR",
            "CPRT",
            "MNST",
            "AEP",
            "ROST",
            "FAST",
            "KDP",
            "EA",
            "VRSK",
            "ODFL",
            "EXC",
            "LULU",
            "GEHC",
            "CTSH",
            "XEL",
            "FANG",
            "CCEP",
            "KHC",
            "CSGP",
            "DDOG",
            "ZS",
            "BKR",
            "DLTR",
            "CRWD",
            "ANSS",
            "IDXX",
            "ON",
            "ILMN",
            "BIIB",
            "GFS",
            "CDW",
            "MDB",
            "WBD",
            "ARM",
            "MRNA",
            "SMCI",
        ],
        "ftse100": [
            "SHEL.L",
            "AZN.L",
            "LSEG.L",
            "UU.L",
            "ULVR.L",
            "BP.L",
            "GSK.L",
            "VOD.L",
            "LLOY.L",
            "TSCO.L",
            "PRU.L",
            "BT-A.L",
            "RIO.L",
            "BARC.L",
            "DGE.L",
            "NG.L",
            "NWG.L",
            "CRH.L",
            "REL.L",
            "GLEN.L",
        ],
        "dax40": [
            "SAP",
            "ASML.AS",
            "INGA.AS",
            "URW.AS",
            "SIE.DE",
            "DTE.DE",
            "MBG.DE",
            "ALV.DE",
            "MUV2.DE",
            "BAS.DE",
            "BMW.DE",
            "DB1.DE",
            "VOW3.DE",
            "HEN3.DE",
            "BEI.DE",
            "ADS.DE",
            "SHL.DE",
            "VNA.DE",
            "DBK.DE",
            "CON.DE",
            "IFX.DE",
            "MTX.DE",
            "ENR.DE",
            "HEI.DE",
            "RWE.DE",
            "EON.DE",
            "QIA.DE",
            "ZAL.DE",
            "SAR.DE",
            "PUM.DE",
            "WCH.DE",
            "PFV.DE",
            "HAB.DE",
            "FME.DE",
            "FRE.DE",
            "SRT.DE",
            "AIX.DE",
            "BNR.DE",
            "P911.DE",
            "MRK.DE",
        ],
    }

    def __init__(self):
        self.analyzer = AdvancedInvestmentAnalyzer()
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache

    def get_investment_recommendations(
        self, request: RecommendationRequest
    ) -> PortfolioRecommendation:
        """Generate investment recommendations based on request parameters."""
        try:
            # Determine symbols to analyze
            symbols_to_analyze = self._get_symbols_to_analyze(request)

            print(f"🔍 Analyzing {len(symbols_to_analyze)} investments...")

            # Analyze investments in parallel
            analyses = self._analyze_investments_parallel(symbols_to_analyze)

            # Filter analyses based on request criteria
            filtered_analyses = self._filter_analyses(analyses, request)

            # Sort and select top recommendations
            top_analyses = sorted(
                filtered_analyses,
                key=lambda x: (x.overall_score * x.confidence),
                reverse=True,
            )[: request.max_recommendations]

            # Convert to recommendations
            recommendations = [
                self._create_recommendation(analysis) for analysis in top_analyses
            ]

            # Generate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(recommendations)
            analysis_summary = self._generate_analysis_summary(
                analyses, filtered_analyses
            )
            risk_assessment = self._assess_portfolio_risk(recommendations)
            sector_allocation = self._calculate_sector_allocation(recommendations)

            return PortfolioRecommendation(
                recommendations=recommendations,
                portfolio_metrics=portfolio_metrics,
                analysis_summary=analysis_summary,
                risk_assessment=risk_assessment,
                sector_allocation=sector_allocation,
            )

        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return PortfolioRecommendation(
                recommendations=[],
                portfolio_metrics={},
                analysis_summary={"error": str(e)},
                risk_assessment={},
                sector_allocation={},
            )

    def _get_symbols_to_analyze(self, request: RecommendationRequest) -> List[str]:
        """Get list of symbols to analyze based on request."""
        if request.symbols:
            return request.symbols

        # Use all available symbols from indices
        all_symbols = []
        for index_symbols in self.INDICES_SYMBOLS.values():
            all_symbols.extend(index_symbols)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(all_symbols))

    def _analyze_investments_parallel(
        self, symbols: List[str]
    ) -> List[ComprehensiveAnalysisResult]:
        """Analyze investments in parallel for better performance."""
        analyses = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit analysis tasks
            future_to_symbol = {
                executor.submit(self._analyze_with_cache, symbol): symbol
                for symbol in symbols
            }

            # Collect results
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    analysis = future.result(timeout=30)  # 30 second timeout per symbol
                    if analysis:
                        analyses.append(analysis)
                        print(f"✅ {symbol}: Score {analysis.overall_score:.1f}")
                    else:
                        print(f"⚠️ {symbol}: No data available")
                except Exception as e:
                    print(f"❌ {symbol}: Error - {e}")

        return analyses

    def _analyze_with_cache(self, symbol: str) -> Optional[ComprehensiveAnalysisResult]:
        """Analyze investment with caching."""
        cache_key = f"analysis_{symbol}_{int(time.time() // self._cache_ttl)}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            analysis = self.analyzer.analyze_investment(symbol)
            self._cache[cache_key] = analysis
            return analysis
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def _filter_analyses(
        self,
        analyses: List[ComprehensiveAnalysisResult],
        request: RecommendationRequest,
    ) -> List[ComprehensiveAnalysisResult]:
        """Filter analyses based on request criteria."""
        filtered = []

        risk_level_order = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
        max_risk_index = risk_level_order.index(request.max_risk_level)

        for analysis in analyses:
            # Score filter
            if analysis.overall_score < request.min_score:
                continue

            # Risk filter
            try:
                risk_index = risk_level_order.index(analysis.risk_level)
                if risk_index > max_risk_index:
                    continue
            except ValueError:
                continue  # Skip if risk level is unknown

            # Recommendation filter (exclude SELL recommendations only if min_score is high)
            # If user sets very low min_score, they want to see all recommendations including SELL
            if analysis.recommendation in ["SELL"] and request.min_score > 40.0:
                continue

            filtered.append(analysis)

        return filtered

    def _create_recommendation(
        self, analysis: ComprehensiveAnalysisResult
    ) -> InvestmentRecommendation:
        """Convert analysis result to recommendation."""
        # Calculate upside potential
        upside_potential = None
        if analysis.target_price and hasattr(analysis, "current_price"):
            current_price = getattr(analysis, "current_price", None)
            if current_price:
                upside_potential = (
                    (analysis.target_price - current_price) / current_price
                ) * 100

        # Determine data quality based on confidence
        if analysis.confidence >= 0.8:
            data_quality = "EXCELLENT"
        elif analysis.confidence >= 0.6:
            data_quality = "GOOD"
        elif analysis.confidence >= 0.4:
            data_quality = "FAIR"
        else:
            data_quality = "POOR"

        # Extract key insights (top 3)
        key_insights = (
            analysis.insights[:3] if len(analysis.insights) > 3 else analysis.insights
        )

        return InvestmentRecommendation(
            symbol=analysis.investment_symbol,
            name=analysis.investment_symbol,  # Would need to fetch actual name
            current_price=0.0,  # Would need to fetch from market data
            currency="USD",  # Default, would need to determine actual currency
            recommendation=analysis.recommendation,
            overall_score=analysis.overall_score,
            confidence=analysis.confidence,
            risk_level=analysis.risk_level,
            technical_score=analysis.technical_score,
            fundamental_score=analysis.fundamental_score,
            momentum_score=analysis.momentum_score,
            target_price=analysis.target_price,
            stop_loss=analysis.stop_loss,
            upside_potential=upside_potential,
            strengths=analysis.strengths,
            weaknesses=analysis.weaknesses,
            key_insights=key_insights,
            data_quality=data_quality,
        )

    def _calculate_portfolio_metrics(
        self, recommendations: List[InvestmentRecommendation]
    ) -> Dict[str, Any]:
        """Calculate portfolio-level metrics."""
        if not recommendations:
            return {}

        scores = [r.overall_score for r in recommendations]
        confidences = [r.confidence for r in recommendations]

        return {
            "total_recommendations": len(recommendations),
            "average_score": sum(scores) / len(scores),
            "score_range": {"min": min(scores), "max": max(scores)},
            "average_confidence": sum(confidences) / len(confidences),
            "strong_buy_count": len(
                [r for r in recommendations if r.recommendation == "STRONG_BUY"]
            ),
            "buy_count": len([r for r in recommendations if r.recommendation == "BUY"]),
            "hold_count": len(
                [
                    r
                    for r in recommendations
                    if r.recommendation in ["HOLD", "WEAK_HOLD"]
                ]
            ),
            "high_quality_count": len(
                [r for r in recommendations if r.data_quality in ["EXCELLENT", "GOOD"]]
            ),
        }

    def _generate_analysis_summary(
        self,
        all_analyses: List[ComprehensiveAnalysisResult],
        filtered_analyses: List[ComprehensiveAnalysisResult],
    ) -> Dict[str, Any]:
        """Generate summary of analysis process."""
        return {
            "total_analyzed": len(all_analyses),
            "passed_filters": len(filtered_analyses),
            "filter_success_rate": len(filtered_analyses) / len(all_analyses)
            if all_analyses
            else 0,
            "average_score_all": sum(a.overall_score for a in all_analyses)
            / len(all_analyses)
            if all_analyses
            else 0,
            "average_score_filtered": sum(a.overall_score for a in filtered_analyses)
            / len(filtered_analyses)
            if filtered_analyses
            else 0,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _assess_portfolio_risk(
        self, recommendations: List[InvestmentRecommendation]
    ) -> Dict[str, Any]:
        """Assess overall portfolio risk."""
        if not recommendations:
            return {}

        risk_levels = [r.risk_level for r in recommendations]
        risk_counts = {level: risk_levels.count(level) for level in set(risk_levels)}

        # Calculate risk score (0-100, higher = more risky)
        risk_scores = {
            "VERY_LOW": 10,
            "LOW": 25,
            "MODERATE": 50,
            "HIGH": 75,
            "VERY_HIGH": 90,
        }

        avg_risk_score = sum(risk_scores.get(level, 50) for level in risk_levels) / len(
            risk_levels
        )

        return {
            "risk_distribution": risk_counts,
            "average_risk_score": avg_risk_score,
            "risk_assessment": self._categorize_portfolio_risk(avg_risk_score),
            "diversification_score": len(set(risk_levels))
            / 5
            * 100,  # Max 5 risk levels
        }

    def _categorize_portfolio_risk(self, risk_score: float) -> str:
        """Categorize portfolio risk based on average score."""
        if risk_score <= 20:
            return "VERY_CONSERVATIVE"
        elif risk_score <= 35:
            return "CONSERVATIVE"
        elif risk_score <= 50:
            return "MODERATE"
        elif risk_score <= 70:
            return "AGGRESSIVE"
        else:
            return "VERY_AGGRESSIVE"

    def _calculate_sector_allocation(
        self, recommendations: List[InvestmentRecommendation]
    ) -> Dict[str, float]:
        """Calculate sector allocation (simplified - would need actual sector data)."""
        # This is a simplified implementation
        # In reality, you'd fetch sector data for each symbol
        total = len(recommendations)
        if total == 0:
            return {}

        # Mock sector allocation based on symbol patterns
        sectors = {}
        for rec in recommendations:
            # Simple heuristic based on symbol
            if any(
                tech in rec.symbol for tech in ["AAPL", "MSFT", "GOOGL", "NVDA", "META"]
            ):
                sector = "Technology"
            elif any(health in rec.symbol for health in ["GSK", "AZN", "BIIB"]):
                sector = "Healthcare"
            elif any(energy in rec.symbol for energy in ["SHEL", "BP", "TTE"]):
                sector = "Energy"
            else:
                sector = "Other"

            sectors[sector] = sectors.get(sector, 0) + 1

        # Convert to percentages
        return {sector: (count / total) * 100 for sector, count in sectors.items()}
