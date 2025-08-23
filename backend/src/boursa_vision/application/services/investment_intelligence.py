"""
Investment Intelligence Service - Recommandations d'Achat Automatisées
=====================================================================

Service principal orchestrant l'analyse massive et la génération de recommandations d'achat.
Utilise les patterns Strategy, Observer et Command pour une architecture modulaire.

Design Patterns Utilisés:
- Strategy Pattern: Différentes stratégies de recommandation
- Observer Pattern: Notifications des nouvelles opportunités
- Command Pattern: Exécution des analyses
- Factory Pattern: Création des analyseurs
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .market_scanner import MarketScannerService, ScanConfig, ScanResult, ScanStrategy

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Types de recommandations d'investissement"""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class RiskLevel(str, Enum):
    """Niveaux de risque"""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class InvestmentHorizon(str, Enum):
    """Horizons d'investissement"""

    SHORT_TERM = "SHORT_TERM"  # < 6 mois
    MEDIUM_TERM = "MEDIUM_TERM"  # 6 mois - 2 ans
    LONG_TERM = "LONG_TERM"  # > 2 ans


@dataclass
class InvestmentRecommendation:
    """Recommandation d'investissement complète"""

    symbol: str
    name: str
    recommendation: RecommendationType
    confidence_score: float  # 0-100
    target_price: float | None
    current_price: float
    potential_return: float  # Pourcentage
    risk_level: RiskLevel
    investment_horizon: InvestmentHorizon
    sector: str | None
    market_cap: float | None

    # Scores détaillés
    fundamental_score: float
    technical_score: float
    momentum_score: float
    value_score: float
    quality_score: float

    # Ratios clés
    pe_ratio: float | None
    pb_ratio: float | None
    roe: float | None
    debt_to_equity: float | None

    # Analyse technique
    rsi: float | None
    macd_signal: str | None

    # Métadonnées
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "recommendation": self.recommendation.value,
            "confidence_score": self.confidence_score,
            "target_price": self.target_price,
            "current_price": self.current_price,
            "potential_return": self.potential_return,
            "risk_level": self.risk_level.value,
            "investment_horizon": self.investment_horizon.value,
            "sector": self.sector,
            "market_cap": self.market_cap,
            "fundamental_score": self.fundamental_score,
            "technical_score": self.technical_score,
            "momentum_score": self.momentum_score,
            "value_score": self.value_score,
            "quality_score": self.quality_score,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "roe": self.roe,
            "debt_to_equity": self.debt_to_equity,
            "rsi": self.rsi,
            "macd_signal": self.macd_signal,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class AnalysisConfig:
    """Configuration pour l'analyse d'investissement"""

    min_confidence_score: float = 70.0
    max_recommendations: int = 50
    include_sectors: set[str] | None = None
    exclude_sectors: set[str] | None = None
    min_market_cap: float = 1e9  # 1 milliard
    max_risk_level: RiskLevel = RiskLevel.HIGH
    preferred_horizon: InvestmentHorizon = InvestmentHorizon.MEDIUM_TERM
    update_frequency_hours: int = 6


class RecommendationStrategy(ABC):
    """Interface pour les stratégies de recommandation"""

    @abstractmethod
    def analyze_opportunity(
        self, scan_result: ScanResult
    ) -> InvestmentRecommendation | None:
        """Analyse une opportunité et génère une recommandation"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Nom de la stratégie"""
        pass


class ValueInvestingStrategy(RecommendationStrategy):
    """Stratégie d'investissement dans la valeur"""

    def analyze_opportunity(
        self, scan_result: ScanResult
    ) -> InvestmentRecommendation | None:
        """Analyse selon les critères de value investing"""

        # Critères de value investing
        value_score = self._calculate_value_score(scan_result)
        quality_score = self._calculate_quality_score(scan_result)

        if value_score < 60 or quality_score < 50:
            return None

        # Calcul du score de confiance
        confidence = value_score * 0.6 + quality_score * 0.4

        # Détermination de la recommandation
        recommendation = self._determine_recommendation(confidence)

        # Calcul du prix cible (conservateur)
        target_price = self._calculate_target_price(scan_result)
        potential_return = (
            ((target_price - scan_result.price) / scan_result.price) * 100
            if target_price
            else 0
        )

        reasons = [
            f"Score de valeur élevé: {value_score:.1f}/100",
            f"Score de qualité: {quality_score:.1f}/100",
        ]

        if scan_result.pe_ratio and scan_result.pe_ratio < 15:
            reasons.append(f"P/E ratio attractif: {scan_result.pe_ratio:.1f}")

        if scan_result.pb_ratio and scan_result.pb_ratio < 1.5:
            reasons.append(f"P/B ratio faible: {scan_result.pb_ratio:.1f}")

        if scan_result.roe and scan_result.roe > 15:
            reasons.append(f"ROE solide: {scan_result.roe:.1f}%")

        return InvestmentRecommendation(
            symbol=scan_result.symbol,
            name=scan_result.name,
            recommendation=recommendation,
            confidence_score=confidence,
            target_price=target_price,
            current_price=scan_result.price,
            potential_return=potential_return,
            risk_level=RiskLevel.MODERATE,
            investment_horizon=InvestmentHorizon.LONG_TERM,
            sector=scan_result.sector,
            market_cap=scan_result.market_cap,
            fundamental_score=scan_result.fundamental_score,
            technical_score=scan_result.technical_score,
            momentum_score=50.0,  # Neutral pour value investing
            value_score=value_score,
            quality_score=quality_score,
            pe_ratio=scan_result.pe_ratio,
            pb_ratio=scan_result.pb_ratio,
            roe=scan_result.roe,
            debt_to_equity=scan_result.debt_to_equity,
            rsi=scan_result.rsi,
            macd_signal=scan_result.macd_signal,
            reasons=reasons,
        )

    def _calculate_value_score(self, scan_result: ScanResult) -> float:
        """Calcule le score de valeur"""
        score = 50.0

        # P/E ratio scoring
        score += self._score_pe_ratio(scan_result.pe_ratio)

        # P/B ratio scoring
        score += self._score_pb_ratio(scan_result.pb_ratio)

        # Dividend yield scoring
        score += self._score_dividend_yield(scan_result.dividend_yield)

        return max(0, min(100, score))

    def _score_pe_ratio(self, pe_ratio: float | None) -> float:
        """Score P/E ratio component"""
        if not pe_ratio or pe_ratio <= 0:
            return 0
        if pe_ratio < 10:
            return 25
        elif pe_ratio < 15:
            return 15
        elif pe_ratio < 20:
            return 5
        else:
            return -10

    def _score_pb_ratio(self, pb_ratio: float | None) -> float:
        """Score P/B ratio component"""
        if not pb_ratio or pb_ratio <= 0:
            return 0
        if pb_ratio < 1:
            return 20
        elif pb_ratio < 1.5:
            return 10
        elif pb_ratio < 2:
            return 0
        else:
            return -10

    def _score_dividend_yield(self, dividend_yield: float | None) -> float:
        """Score dividend yield component"""
        if not dividend_yield:
            return 0
        if dividend_yield > 3:
            return 15
        elif dividend_yield > 1:
            return 5
        return 0

    def _calculate_quality_score(self, scan_result: ScanResult) -> float:
        """Calcule le score de qualité"""
        score = 50.0
        components = 0

        # ROE
        if scan_result.roe:
            if scan_result.roe > 20:
                score += 20
            elif scan_result.roe > 15:
                score += 10
            elif scan_result.roe > 10:
                score += 0
            else:
                score -= 10
            components += 1

        # Debt to equity
        if scan_result.debt_to_equity is not None:
            if scan_result.debt_to_equity < 0.3:
                score += 15
            elif scan_result.debt_to_equity < 0.6:
                score += 5
            elif scan_result.debt_to_equity < 1.0:
                score -= 5
            else:
                score -= 15
            components += 1

        return max(0, min(100, score)) if components > 0 else 50.0

    def _determine_recommendation(self, confidence: float) -> RecommendationType:
        """Détermine la recommandation"""
        if confidence >= 85:
            return RecommendationType.STRONG_BUY
        elif confidence >= 75:
            return RecommendationType.BUY
        elif confidence >= 60:
            return RecommendationType.HOLD
        else:
            return RecommendationType.SELL

    def _calculate_target_price(self, scan_result: ScanResult) -> float | None:
        """Calcule le prix cible conservateur"""
        if not scan_result.pe_ratio or scan_result.pe_ratio <= 0:
            return None

        # Utilise un P/E cible de 15 pour les actions value
        target_pe = min(15, scan_result.pe_ratio * 1.2)

        # Estime les earnings par action
        if scan_result.pe_ratio > 0:
            eps = scan_result.price / scan_result.pe_ratio
            return eps * target_pe

        return None

    def get_strategy_name(self) -> str:
        return "Value Investing"


class GrowthInvestingStrategy(RecommendationStrategy):
    """Stratégie d'investissement dans la croissance"""

    def analyze_opportunity(
        self, scan_result: ScanResult
    ) -> InvestmentRecommendation | None:
        """Analyse selon les critères de growth investing"""

        # Critères de growth investing
        momentum_score = self._calculate_momentum_score(scan_result)
        growth_potential = self._calculate_growth_potential(scan_result)

        if momentum_score < 60 or growth_potential < 50:
            return None

        # Score de confiance
        confidence = momentum_score * 0.7 + growth_potential * 0.3

        recommendation = self._determine_recommendation(confidence)
        target_price = self._calculate_target_price(scan_result)
        potential_return = (
            ((target_price - scan_result.price) / scan_result.price) * 100
            if target_price
            else 0
        )

        reasons = [
            f"Score de momentum: {momentum_score:.1f}/100",
            f"Potentiel de croissance: {growth_potential:.1f}/100",
        ]

        if scan_result.rsi and scan_result.rsi < 70:
            reasons.append(f"RSI favorable: {scan_result.rsi:.1f}")

        if scan_result.macd_signal == "BUY":
            reasons.append("Signal MACD haussier")

        return InvestmentRecommendation(
            symbol=scan_result.symbol,
            name=scan_result.name,
            recommendation=recommendation,
            confidence_score=confidence,
            target_price=target_price,
            current_price=scan_result.price,
            potential_return=potential_return,
            risk_level=RiskLevel.HIGH,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            sector=scan_result.sector,
            market_cap=scan_result.market_cap,
            fundamental_score=scan_result.fundamental_score,
            technical_score=scan_result.technical_score,
            momentum_score=momentum_score,
            value_score=30.0,  # Moins important pour growth
            quality_score=growth_potential,
            pe_ratio=scan_result.pe_ratio,
            pb_ratio=scan_result.pb_ratio,
            roe=scan_result.roe,
            debt_to_equity=scan_result.debt_to_equity,
            rsi=scan_result.rsi,
            macd_signal=scan_result.macd_signal,
            reasons=reasons,
        )

    def _calculate_momentum_score(self, scan_result: ScanResult) -> float:
        """Calcule le score de momentum"""
        score = 50.0

        # Performance récente
        if scan_result.change_percent > 5:
            score += 20
        elif scan_result.change_percent > 2:
            score += 10
        elif scan_result.change_percent < -5:
            score -= 20

        # RSI
        if scan_result.rsi:
            if 50 <= scan_result.rsi <= 70:
                score += 15
            elif scan_result.rsi > 70:
                score -= 10
            elif scan_result.rsi < 30:
                score -= 5

        # Signal MACD
        if scan_result.macd_signal == "BUY":
            score += 15
        elif scan_result.macd_signal == "SELL":
            score -= 15

        return max(0, min(100, score))

    def _calculate_growth_potential(self, scan_result: ScanResult) -> float:
        """Calcule le potentiel de croissance"""
        score = 50.0

        # Secteur technologique bonus
        if scan_result.sector and "technolog" in scan_result.sector.lower():
            score += 10

        # ROE élevé
        if scan_result.roe and scan_result.roe > 15:
            score += 15

        # Capitalisation (favorise les mid/large caps)
        if scan_result.market_cap:
            if 10e9 <= scan_result.market_cap <= 100e9:  # 10B-100B
                score += 10
            elif scan_result.market_cap > 100e9:  # >100B
                score += 5

        return max(0, min(100, score))

    def _determine_recommendation(self, confidence: float) -> RecommendationType:
        """Détermine la recommandation"""
        if confidence >= 80:
            return RecommendationType.STRONG_BUY
        elif confidence >= 70:
            return RecommendationType.BUY
        elif confidence >= 55:
            return RecommendationType.HOLD
        else:
            return RecommendationType.SELL

    def _calculate_target_price(self, scan_result: ScanResult) -> float | None:
        """Calcule le prix cible plus agressif"""
        # Pour les actions growth, on accepte des P/E plus élevés
        return scan_result.price * 1.25  # 25% upside potentiel

    def get_strategy_name(self) -> str:
        return "Growth Investing"


class InvestmentIntelligenceService:
    """Service principal d'intelligence d'investissement"""

    def __init__(self, market_scanner: MarketScannerService):
        self.market_scanner = market_scanner
        self.strategies: list[RecommendationStrategy] = [
            ValueInvestingStrategy(),
            GrowthInvestingStrategy(),
        ]
        self.last_analysis: datetime | None = None
        self.cached_recommendations: list[InvestmentRecommendation] = []

    async def generate_investment_recommendations(
        self, config: AnalysisConfig
    ) -> list[InvestmentRecommendation]:
        """Génère des recommandations d'investissement complètes"""

        logger.info("Starting investment analysis...")
        start_time = datetime.now(UTC)

        # Configuration du scan de marché
        scan_config = ScanConfig(
            strategy=ScanStrategy.FULL_MARKET,
            max_symbols=2000,
            min_market_cap=config.min_market_cap,
            include_fundamentals=True,
            include_technicals=True,
            parallel_requests=100,
        )

        # Scanner le marché
        scan_results = await self.market_scanner.scan_market(scan_config)
        logger.info(f"Market scan completed: {len(scan_results)} symbols analyzed")

        # Générer des recommandations avec chaque stratégie
        all_recommendations = []

        for strategy in self.strategies:
            strategy_recommendations = []

            for scan_result in scan_results:
                try:
                    recommendation = strategy.analyze_opportunity(scan_result)
                    if (
                        recommendation
                        and recommendation.confidence_score
                        >= config.min_confidence_score
                    ):
                        strategy_recommendations.append(recommendation)
                except Exception as e:
                    logger.error(
                        f"Error analyzing {scan_result.symbol} with {strategy.get_strategy_name()}: {e}"
                    )

            logger.info(
                f"{strategy.get_strategy_name()}: {len(strategy_recommendations)} recommendations generated"
            )
            all_recommendations.extend(strategy_recommendations)

        # Déduplication et tri
        recommendations = self._deduplicate_recommendations(all_recommendations)
        recommendations = self._filter_and_rank_recommendations(recommendations, config)

        # Limitation du nombre de résultats
        recommendations = recommendations[: config.max_recommendations]

        # Mise à jour du cache
        self.cached_recommendations = recommendations
        self.last_analysis = datetime.now(UTC)

        analysis_time = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"Investment analysis completed: {len(recommendations)} final recommendations in {analysis_time:.2f}s"
        )

        return recommendations

    def _deduplicate_recommendations(
        self, recommendations: list[InvestmentRecommendation]
    ) -> list[InvestmentRecommendation]:
        """Déduplique les recommandations par symbole en gardant la meilleure"""
        best_recommendations = {}

        for rec in recommendations:
            if rec.symbol not in best_recommendations:
                best_recommendations[rec.symbol] = rec
            else:
                # Garder celle avec le meilleur score de confiance
                if (
                    rec.confidence_score
                    > best_recommendations[rec.symbol].confidence_score
                ):
                    best_recommendations[rec.symbol] = rec

        return list(best_recommendations.values())

    def _filter_and_rank_recommendations(
        self, recommendations: list[InvestmentRecommendation], config: AnalysisConfig
    ) -> list[InvestmentRecommendation]:
        """Filtre et classe les recommandations"""

        # Filtrer selon les critères
        filtered = []
        for rec in recommendations:
            # Filtre par secteur
            if config.include_sectors and rec.sector not in config.include_sectors:
                continue
            if config.exclude_sectors and rec.sector in config.exclude_sectors:
                continue

            # Filtre par niveau de risque
            risk_levels = [
                RiskLevel.VERY_LOW,
                RiskLevel.LOW,
                RiskLevel.MODERATE,
                RiskLevel.HIGH,
                RiskLevel.VERY_HIGH,
            ]
            if risk_levels.index(rec.risk_level) > risk_levels.index(
                config.max_risk_level
            ):
                continue

            # Filtre par capitalisation
            if rec.market_cap and rec.market_cap < config.min_market_cap:
                continue

            filtered.append(rec)

        # Tri par score de confiance puis par potentiel de retour
        filtered.sort(
            key=lambda x: (x.confidence_score, x.potential_return), reverse=True
        )

        return filtered

    def get_top_opportunities(self, limit: int = 20) -> list[InvestmentRecommendation]:
        """Récupère les meilleures opportunités"""
        strong_buys = [
            r
            for r in self.cached_recommendations
            if r.recommendation == RecommendationType.STRONG_BUY
        ]
        buys = [
            r
            for r in self.cached_recommendations
            if r.recommendation == RecommendationType.BUY
        ]

        # Prioriser STRONG_BUY puis BUY
        top_opportunities = strong_buys + buys
        return top_opportunities[:limit]

    def get_sector_recommendations(self) -> dict[str, list[InvestmentRecommendation]]:
        """Récupère les recommandations par secteur"""
        sector_recommendations = {}

        for rec in self.cached_recommendations:
            if rec.sector and rec.recommendation in [
                RecommendationType.STRONG_BUY,
                RecommendationType.BUY,
            ]:
                if rec.sector not in sector_recommendations:
                    sector_recommendations[rec.sector] = []
                sector_recommendations[rec.sector].append(rec)

        # Trier chaque secteur par score de confiance
        for sector in sector_recommendations:
            sector_recommendations[sector].sort(
                key=lambda x: x.confidence_score, reverse=True
            )
            sector_recommendations[sector] = sector_recommendations[sector][
                :5
            ]  # Top 5 par secteur

        return sector_recommendations

    def get_portfolio_suggestions(
        self, portfolio_size: float = 100000.0
    ) -> dict[str, Any]:
        """Génère des suggestions de portefeuille diversifié"""
        top_recommendations = self.get_top_opportunities(50)

        if not top_recommendations:
            return {"error": "Aucune recommandation disponible"}

        # Grouper par secteur
        sector_groups = {}
        for rec in top_recommendations:
            sector = rec.sector or "Unknown"
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(rec)

        # Sélectionner le meilleur de chaque secteur (diversification)
        portfolio_suggestions = []
        total_weight = 0

        for sector, recommendations in sector_groups.items():
            best_rec = recommendations[0]  # Déjà trié par score de confiance
            weight = min(0.2, 0.8 / len(sector_groups))  # Max 20% par secteur

            portfolio_suggestions.append(
                {
                    "symbol": best_rec.symbol,
                    "name": best_rec.name,
                    "sector": sector,
                    "weight": weight,
                    "suggested_amount": portfolio_size * weight,
                    "confidence_score": best_rec.confidence_score,
                    "recommendation": best_rec.recommendation.value,
                    "target_price": best_rec.target_price,
                    "current_price": best_rec.current_price,
                    "potential_return": best_rec.potential_return,
                }
            )
            total_weight += weight

        return {
            "portfolio_suggestions": portfolio_suggestions,
            "total_weight": total_weight,
            "diversification_score": len(sector_groups)
            * 10,  # Plus de secteurs = meilleure diversification
            "expected_return": sum(
                s["potential_return"] * s["weight"] for s in portfolio_suggestions
            ),
            "risk_level": "MODERATE",  # Calculé basé sur la diversification
        }

    def should_update_analysis(self, config: AnalysisConfig) -> bool:
        """Vérifie si une nouvelle analyse est nécessaire"""
        if not self.last_analysis:
            return True

        time_since_last = datetime.now(UTC) - self.last_analysis
        return time_since_last.total_seconds() > config.update_frequency_hours * 3600

    def get_analysis_summary(self) -> dict[str, Any]:
        """Résumé de la dernière analyse"""
        if not self.cached_recommendations:
            return {"error": "Aucune analyse disponible"}

        strong_buys = len(
            [
                r
                for r in self.cached_recommendations
                if r.recommendation == RecommendationType.STRONG_BUY
            ]
        )
        buys = len(
            [
                r
                for r in self.cached_recommendations
                if r.recommendation == RecommendationType.BUY
            ]
        )
        holds = len(
            [
                r
                for r in self.cached_recommendations
                if r.recommendation == RecommendationType.HOLD
            ]
        )

        avg_confidence = sum(
            r.confidence_score for r in self.cached_recommendations
        ) / len(self.cached_recommendations)
        avg_potential_return = sum(
            r.potential_return for r in self.cached_recommendations
        ) / len(self.cached_recommendations)

        sectors_analyzed = len(
            {r.sector for r in self.cached_recommendations if r.sector}
        )

        return {
            "total_recommendations": len(self.cached_recommendations),
            "strong_buys": strong_buys,
            "buys": buys,
            "holds": holds,
            "average_confidence": avg_confidence,
            "average_potential_return": avg_potential_return,
            "sectors_analyzed": sectors_analyzed,
            "last_updated": self.last_analysis.isoformat()
            if self.last_analysis
            else None,
            "top_sector": self._get_top_sector(),
        }

    def _get_top_sector(self) -> str | None:
        """Identifie le secteur avec le plus de recommandations d'achat"""
        if not self.cached_recommendations:
            return None

        buy_recommendations = [
            r
            for r in self.cached_recommendations
            if r.recommendation
            in [RecommendationType.STRONG_BUY, RecommendationType.BUY]
        ]

        sector_counts = {}
        for rec in buy_recommendations:
            if rec.sector:
                sector_counts[rec.sector] = sector_counts.get(rec.sector, 0) + 1

        return (
            max(sector_counts.items(), key=lambda x: x[1])[0] if sector_counts else None
        )
