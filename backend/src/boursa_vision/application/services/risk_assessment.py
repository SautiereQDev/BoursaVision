"""
Risk Assessment Service - Comprehensive Risk Analysis
==================================================
Service d'évaluation complète des risques utilisant de multiples indicateurs
et sources de données pour analyser les risques d'investissement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import yfinance as yf

from ..dtos import (
    FundamentalRiskDTO,
    GeopoliticalRiskDTO,
    RiskAssessmentDTO,
    RiskFactorDTO,
)


class RiskLevel(Enum):
    """Niveaux de risque standardisés"""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(Enum):
    """Catégories de risques"""

    MARKET = "MARKET"
    LIQUIDITY = "LIQUIDITY"
    CREDIT = "CREDIT"
    OPERATIONAL = "OPERATIONAL"
    GEOPOLITICAL = "GEOPOLITICAL"
    REGULATORY = "REGULATORY"
    FUNDAMENTAL = "FUNDAMENTAL"
    TECHNICAL = "TECHNICAL"
    ESG = "ESG"


@dataclass
class RiskFactor:
    """Facteur de risque individuel"""

    name: str
    category: RiskCategory
    level: RiskLevel
    score: float  # 0-100
    description: str
    impact: str  # LOW, MEDIUM, HIGH
    probability: str  # LOW, MEDIUM, HIGH
    timeframe: str  # SHORT, MEDIUM, LONG
    source: str
    last_updated: datetime


# ============================================================================
# STRATEGY PATTERN - Analyseurs de risques spécialisés
# ============================================================================


class IRiskAnalyzer(ABC):
    """Interface pour les analyseurs de risques"""

    @abstractmethod
    async def analyze(self, symbol: str, market_data: Dict) -> List[RiskFactor]:
        """Analyser les risques pour un symbole donné"""
        pass

    @abstractmethod
    def get_category(self) -> RiskCategory:
        """Retourner la catégorie de risque analysée"""
        pass


class MarketRiskAnalyzer(IRiskAnalyzer):
    """Analyseur des risques de marché"""

    def get_category(self) -> RiskCategory:
        return RiskCategory.MARKET

    async def analyze(self, symbol: str, market_data: Dict) -> List[RiskFactor]:
        """Analyser les risques de marché"""
        risks = []

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")

            # Volatilité historique
            volatility = hist["Close"].pct_change().std() * np.sqrt(252) * 100
            volatility_risk = self._assess_volatility_risk(volatility)
            risks.append(volatility_risk)

            # Beta (sensibilité au marché)
            beta = info.get("beta", 1.0)
            if beta:
                beta_risk = self._assess_beta_risk(beta)
                risks.append(beta_risk)

            # Corrélation avec le marché
            spy_data = yf.download("SPY", period="1y", progress=False)
            if not spy_data.empty and len(hist) > 0:
                correlation = (
                    hist["Close"].pct_change().corr(spy_data["Close"].pct_change())
                )
                corr_risk = self._assess_correlation_risk(correlation)
                risks.append(corr_risk)

            # Maximum Drawdown
            rolling_max = hist["Close"].expanding().max()
            drawdown = (hist["Close"] - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            dd_risk = self._assess_drawdown_risk(max_drawdown)
            risks.append(dd_risk)

        except Exception as e:
            risks.append(
                RiskFactor(
                    name="Market Data Unavailable",
                    category=RiskCategory.MARKET,
                    level=RiskLevel.MODERATE,
                    score=50.0,
                    description=f"Impossible d'obtenir les données de marché: {str(e)}",
                    impact="MEDIUM",
                    probability="HIGH",
                    timeframe="SHORT",
                    source="Market Analysis",
                    last_updated=datetime.now(),
                )
            )

        return risks

    def _assess_volatility_risk(self, volatility: float) -> RiskFactor:
        """Évaluer le risque de volatilité"""
        if volatility > 50:
            level = RiskLevel.VERY_HIGH
            score = 90.0  # Ensure float
        elif volatility > 30:
            level = RiskLevel.HIGH
            score = 75.0
        elif volatility > 20:
            level = RiskLevel.MODERATE
            score = 50.0
        elif volatility > 10:
            level = RiskLevel.LOW
            score = 25.0
        else:
            level = RiskLevel.VERY_LOW
            score = 10.0

        return RiskFactor(
            name="Volatility Risk",
            category=RiskCategory.MARKET,
            level=level,
            score=score,
            description=f"Volatilité annualisée de {volatility:.1f}%",
            impact="HIGH"
            if volatility > 30
            else "MEDIUM"
            if volatility > 15
            else "LOW",
            probability="HIGH",
            timeframe="SHORT",
            source="Historical Price Analysis",
            last_updated=datetime.now(),
        )

    def _assess_beta_risk(self, beta: float) -> RiskFactor:
        """Évaluer le risque Beta"""
        # Pour beta = 0.2, abs(0.2 - 1) = 0.8 > 0.8 est False, donc c'est MODERATE
        # Correction de la logique
        beta_deviation = abs(beta - 1)

        if beta_deviation > 1.5:
            level = RiskLevel.HIGH
            score = 80.0
        elif beta_deviation > 0.8:
            level = RiskLevel.MODERATE
            score = 60.0
        elif beta_deviation > 0.3:
            level = RiskLevel.LOW
            score = 30.0
        else:
            level = RiskLevel.VERY_LOW
            score = 15.0

        sensitivity = (
            "très sensible"
            if beta > 1.5
            else "sensible"
            if beta > 1.2
            else "peu sensible"
        )

        return RiskFactor(
            name="Market Beta Risk",
            category=RiskCategory.MARKET,
            level=level,
            score=score,
            description=f"Beta de {beta:.2f} - Action {sensitivity} aux mouvements du marché",
            impact="HIGH" if abs(beta - 1) > 1 else "MEDIUM",
            probability="HIGH",
            timeframe="MEDIUM",
            source="Market Beta Analysis",
            last_updated=datetime.now(),
        )

    def _assess_correlation_risk(self, correlation: float) -> RiskFactor:
        """Évaluer le risque de corrélation"""
        if abs(correlation) > 0.8:
            level = RiskLevel.MODERATE
            score = 60.0
        elif abs(correlation) > 0.6:
            level = RiskLevel.LOW
            score = 35.0
        else:
            level = RiskLevel.VERY_LOW
            score = 20.0

        return RiskFactor(
            name="Market Correlation Risk",
            category=RiskCategory.MARKET,
            level=level,
            score=score,
            description=f"Corrélation avec le marché: {correlation:.2f}",
            impact="MEDIUM",
            probability="MEDIUM",
            timeframe="MEDIUM",
            source="Correlation Analysis",
            last_updated=datetime.now(),
        )

    def _assess_drawdown_risk(self, max_drawdown: float) -> RiskFactor:
        """Évaluer le risque de drawdown"""
        if max_drawdown < -50:
            level = RiskLevel.VERY_HIGH
            score = 95.0
        elif max_drawdown < -30:
            level = RiskLevel.HIGH
            score = 80.0
        elif max_drawdown < -20:
            level = RiskLevel.MODERATE
            score = 60.0
        elif max_drawdown < -10:
            level = RiskLevel.LOW
            score = 35.0
        else:
            level = RiskLevel.VERY_LOW
            score = 15.0

        return RiskFactor(
            name="Maximum Drawdown Risk",
            category=RiskCategory.MARKET,
            level=level,
            score=score,
            description=f"Perte maximale historique: {abs(max_drawdown):.1f}%",
            impact="HIGH" if max_drawdown < -30 else "MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Drawdown Analysis",
            last_updated=datetime.now(),
        )


class FundamentalRiskAnalyzer(IRiskAnalyzer):
    """Analyseur des risques fondamentaux"""

    def get_category(self) -> RiskCategory:
        return RiskCategory.FUNDAMENTAL

    async def analyze(self, symbol: str, market_data: Dict) -> List[RiskFactor]:
        """Analyser les risques fondamentaux"""
        risks = []

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet

            # Analyse du ratio d'endettement
            debt_risk = self._assess_debt_risk(info)
            if debt_risk:
                risks.append(debt_risk)

            # Analyse de la liquidité
            liquidity_risk = self._assess_liquidity_risk(info)
            if liquidity_risk:
                risks.append(liquidity_risk)

            # Analyse de la rentabilité
            profitability_risk = self._assess_profitability_risk(info)
            if profitability_risk:
                risks.append(profitability_risk)

            # Analyse de la valorisation
            valuation_risk = self._assess_valuation_risk(info)
            if valuation_risk:
                risks.append(valuation_risk)

            # Analyse de la croissance
            growth_risk = self._assess_growth_risk(info)
            if growth_risk:
                risks.append(growth_risk)

            # Analyse de la qualité des revenus
            revenue_quality_risk = self._assess_revenue_quality_risk(info, financials)
            if revenue_quality_risk:
                risks.append(revenue_quality_risk)

        except Exception as e:
            risks.append(
                RiskFactor(
                    name="Fundamental Data Unavailable",
                    category=RiskCategory.FUNDAMENTAL,
                    level=RiskLevel.MODERATE,
                    score=50.0,
                    description=f"Données fondamentales indisponibles: {str(e)}",
                    impact="MEDIUM",
                    probability="HIGH",
                    timeframe="SHORT",
                    source="Fundamental Analysis",
                    last_updated=datetime.now(),
                )
            )

        return risks

    def _assess_debt_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque d'endettement"""
        debt_to_equity = info.get("debtToEquity")
        total_debt = info.get("totalDebt")

        if debt_to_equity is None:
            return None

        if debt_to_equity > 200:
            level = RiskLevel.VERY_HIGH
            score = 90
        elif debt_to_equity > 100:
            level = RiskLevel.HIGH
            score = 75
        elif debt_to_equity > 50:
            level = RiskLevel.MODERATE
            score = 50
        elif debt_to_equity > 25:
            level = RiskLevel.LOW
            score = 25
        else:
            level = RiskLevel.VERY_LOW
            score = 10

        return RiskFactor(
            name="Debt Risk",
            category=RiskCategory.FUNDAMENTAL,
            level=level,
            score=score,
            description=f"Ratio dette/equity: {debt_to_equity:.1f}%",
            impact="HIGH" if debt_to_equity > 100 else "MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Balance Sheet Analysis",
            last_updated=datetime.now(),
        )

    def _assess_liquidity_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque de liquidité"""
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")

        if current_ratio is None:
            return None

        if current_ratio < 0.8:
            level = RiskLevel.VERY_HIGH
            score = 85
        elif current_ratio < 1.0:
            level = RiskLevel.HIGH
            score = 70
        elif current_ratio < 1.5:
            level = RiskLevel.MODERATE
            score = 45
        elif current_ratio < 2.0:
            level = RiskLevel.LOW
            score = 25
        else:
            level = RiskLevel.VERY_LOW
            score = 10

        return RiskFactor(
            name="Liquidity Risk",
            category=RiskCategory.FUNDAMENTAL,
            level=level,
            score=score,
            description=f"Ratio de liquidité: {current_ratio:.2f}",
            impact="HIGH" if current_ratio < 1 else "MEDIUM",
            probability="MEDIUM",
            timeframe="SHORT",
            source="Liquidity Analysis",
            last_updated=datetime.now(),
        )

    def _assess_profitability_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque de rentabilité"""
        roe = info.get("returnOnEquity")
        profit_margin = info.get("profitMargins")

        if roe is None:
            return None

        roe_percent = roe * 100 if roe < 1 else roe

        if roe_percent < 5:
            level = RiskLevel.HIGH
            score = 80
        elif roe_percent < 10:
            level = RiskLevel.MODERATE
            score = 60
        elif roe_percent < 15:
            level = RiskLevel.LOW
            score = 30
        else:
            level = RiskLevel.VERY_LOW
            score = 15

        return RiskFactor(
            name="Profitability Risk",
            category=RiskCategory.FUNDAMENTAL,
            level=level,
            score=score,
            description=f"ROE: {roe_percent:.1f}%",
            impact="HIGH" if roe_percent < 8 else "MEDIUM",
            probability="MEDIUM",
            timeframe="MEDIUM",
            source="Profitability Analysis",
            last_updated=datetime.now(),
        )

    def _assess_valuation_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque de valorisation"""
        pe_ratio = info.get("trailingPE")
        pb_ratio = info.get("priceToBook")

        if pe_ratio is None:
            return None

        if pe_ratio > 50:
            level = RiskLevel.HIGH
            score = 80
        elif pe_ratio > 30:
            level = RiskLevel.MODERATE
            score = 60
        elif pe_ratio > 20:
            level = RiskLevel.LOW
            score = 35
        elif pe_ratio > 10:
            level = RiskLevel.VERY_LOW
            score = 20
        else:
            level = RiskLevel.LOW
            score = 40  # PE très bas peut indiquer des problèmes

        return RiskFactor(
            name="Valuation Risk",
            category=RiskCategory.FUNDAMENTAL,
            level=level,
            score=score,
            description=f"P/E Ratio: {pe_ratio:.1f}",
            impact="MEDIUM",
            probability="MEDIUM",
            timeframe="MEDIUM",
            source="Valuation Analysis",
            last_updated=datetime.now(),
        )

    def _assess_growth_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque de croissance"""
        revenue_growth = info.get("revenueGrowth")
        earnings_growth = info.get("earningsGrowth")

        if revenue_growth is None:
            return None

        revenue_growth_percent = (
            revenue_growth * 100 if revenue_growth < 1 else revenue_growth
        )

        if revenue_growth_percent < -10:
            level = RiskLevel.HIGH
            score = 80
        elif revenue_growth_percent < 0:
            level = RiskLevel.MODERATE
            score = 60
        elif revenue_growth_percent < 5:
            level = RiskLevel.LOW
            score = 35
        else:
            level = RiskLevel.VERY_LOW
            score = 15

        return RiskFactor(
            name="Growth Risk",
            category=RiskCategory.FUNDAMENTAL,
            level=level,
            score=score,
            description=f"Croissance revenus: {revenue_growth_percent:.1f}%",
            impact="HIGH" if revenue_growth_percent < -5 else "MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Growth Analysis",
            last_updated=datetime.now(),
        )

    def _assess_revenue_quality_risk(
        self, info: Dict, financials: pd.DataFrame
    ) -> Optional[RiskFactor]:
        """Évaluer la qualité des revenus"""
        try:
            if financials.empty:
                return None

            # Analyse simplifiée basée sur les informations disponibles
            # Simulation d'une analyse de qualité des revenus
            revenue_growth = info.get("revenueGrowth", 0)

            if revenue_growth is None:
                return None

            # Convert to percentage if needed
            if abs(revenue_growth) < 1:
                revenue_growth = revenue_growth * 100

            # Simple volatility assessment based on revenue growth
            if abs(revenue_growth) > 30:
                level = RiskLevel.HIGH
                score = 75
                volatility_desc = "élevée"
            elif abs(revenue_growth) > 15:
                level = RiskLevel.MODERATE
                score = 55
                volatility_desc = "modérée"
            elif abs(revenue_growth) > 5:
                level = RiskLevel.LOW
                score = 30
                volatility_desc = "faible"
            else:
                level = RiskLevel.VERY_LOW
                score = 15
                volatility_desc = "très faible"

            return RiskFactor(
                name="Revenue Quality Risk",
                category=RiskCategory.FUNDAMENTAL,
                level=level,
                score=score,
                description=f"Volatilité des revenus: {volatility_desc} (croissance: {revenue_growth:.1f}%)",
                impact="MEDIUM",
                probability="MEDIUM",
                timeframe="LONG",
                source="Revenue Quality Analysis",
                last_updated=datetime.now(),
            )

        except Exception:
            return None


class GeopoliticalRiskAnalyzer(IRiskAnalyzer):
    """Analyseur des risques géopolitiques"""

    def get_category(self) -> RiskCategory:
        return RiskCategory.GEOPOLITICAL

    async def analyze(self, symbol: str, market_data: Dict) -> List[RiskFactor]:
        """Analyser les risques géopolitiques"""
        risks = []

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Analyse par pays/région
            country_risk = self._assess_country_risk(info)
            if country_risk:
                risks.append(country_risk)

            # Analyse par secteur (exposition géopolitique)
            sector_risk = self._assess_sector_geopolitical_risk(info)
            if sector_risk:
                risks.append(sector_risk)

            # Exposition internationale
            international_risk = self._assess_international_exposure_risk(info)
            if international_risk:
                risks.append(international_risk)

        except Exception as e:
            risks.append(
                RiskFactor(
                    name="Geopolitical Analysis Error",
                    category=RiskCategory.GEOPOLITICAL,
                    level=RiskLevel.MODERATE,
                    score=50.0,
                    description=f"Erreur d'analyse géopolitique: {str(e)}",
                    impact="MEDIUM",
                    probability="MEDIUM",
                    timeframe="MEDIUM",
                    source="Geopolitical Analysis",
                    last_updated=datetime.now(),
                )
            )

        return risks

    def _assess_country_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque pays"""
        country = info.get("country", "")

        # Classification des risques par pays (simplifiée)
        high_risk_countries = ["Russia", "China", "Iran", "North Korea", "Venezuela"]
        medium_risk_countries = ["Turkey", "Brazil", "India", "South Africa", "Mexico"]

        if country in high_risk_countries:
            level = RiskLevel.HIGH
            score = 80
            description = f"Pays à haut risque géopolitique: {country}"
        elif country in medium_risk_countries:
            level = RiskLevel.MODERATE
            score = 55
            description = f"Pays à risque géopolitique modéré: {country}"
        elif country in [
            "United States",
            "Canada",
            "Germany",
            "Switzerland",
            "Netherlands",
        ]:
            level = RiskLevel.VERY_LOW
            score = 15
            description = f"Pays à faible risque géopolitique: {country}"
        else:
            level = RiskLevel.LOW
            score = 30
            description = f"Risque géopolitique standard pour: {country}"

        return RiskFactor(
            name="Country Risk",
            category=RiskCategory.GEOPOLITICAL,
            level=level,
            score=score,
            description=description,
            impact="HIGH"
            if level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
            else "MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Country Risk Assessment",
            last_updated=datetime.now(),
        )

    def _assess_sector_geopolitical_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque géopolitique par secteur"""
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        # Secteurs sensibles aux tensions géopolitiques
        high_risk_sectors = [
            "Energy",
            "Oil & Gas",
            "Defense",
            "Technology",
            "Semiconductors",
            "Telecommunications",
            "Banking",
            "Mining",
            "Aerospace",
        ]

        # Industries spécifiquement sensibles
        high_risk_industries = [
            "Oil & Gas E&P",
            "Semiconductors",
            "Defense",
            "Cybersecurity",
            "Telecommunications Equipment",
            "Solar",
            "Lithium",
            "Rare Earth",
        ]

        is_high_risk = any(
            risk_sector.lower() in sector.lower() for risk_sector in high_risk_sectors
        )
        is_high_risk_industry = any(
            risk_industry.lower() in industry.lower()
            for risk_industry in high_risk_industries
        )

        if is_high_risk or is_high_risk_industry:
            level = RiskLevel.HIGH
            score = 75
            impact = "HIGH"
            description = f"Secteur sensible aux tensions géopolitiques: {sector}"
        elif sector in ["Consumer Staples", "Utilities", "Real Estate"]:
            level = RiskLevel.LOW
            score = 25
            impact = "LOW"
            description = f"Secteur peu sensible aux tensions géopolitiques: {sector}"
        else:
            level = RiskLevel.MODERATE
            score = 45
            impact = "MEDIUM"
            description = f"Sensibilité géopolitique modérée: {sector}"

        return RiskFactor(
            name="Sector Geopolitical Risk",
            category=RiskCategory.GEOPOLITICAL,
            level=level,
            score=score,
            description=description,
            impact=impact,
            probability="MEDIUM",
            timeframe="MEDIUM",
            source="Sector Risk Assessment",
            last_updated=datetime.now(),
        )

    def _assess_international_exposure_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer le risque d'exposition internationale"""
        # Simulation basée sur la taille de l'entreprise et le secteur
        market_cap = info.get("marketCap", 0)
        sector = info.get("sector", "")

        # Les grandes entreprises tech ont souvent une forte exposition internationale
        tech_sectors = ["Technology", "Communication Services"]
        is_tech = any(tech in sector for tech in tech_sectors)

        if market_cap > 100_000_000_000 and is_tech:  # > 100B et tech
            level = RiskLevel.MODERATE
            score = 60
            description = (
                "Forte exposition internationale - Sensible aux tensions commerciales"
            )
        elif market_cap > 50_000_000_000:  # > 50B
            level = RiskLevel.LOW
            score = 35
            description = "Exposition internationale modérée"
        else:
            level = RiskLevel.VERY_LOW
            score = 20
            description = "Exposition internationale limitée"

        return RiskFactor(
            name="International Exposure Risk",
            category=RiskCategory.GEOPOLITICAL,
            level=level,
            score=score,
            description=description,
            impact="MEDIUM" if level == RiskLevel.MODERATE else "LOW",
            probability="MEDIUM",
            timeframe="MEDIUM",
            source="International Exposure Analysis",
            last_updated=datetime.now(),
        )


class ESGRiskAnalyzer(IRiskAnalyzer):
    """Analyseur des risques ESG (Environmental, Social, Governance)"""

    def get_category(self) -> RiskCategory:
        return RiskCategory.ESG

    async def analyze(self, symbol: str, market_data: Dict) -> List[RiskFactor]:
        """Analyser les risques ESG"""
        risks = []

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Analyse ESG basée sur le secteur
            environmental_risk = self._assess_environmental_risk(info)
            if environmental_risk:
                risks.append(environmental_risk)

            # Risques de gouvernance
            governance_risk = self._assess_governance_risk(info)
            if governance_risk:
                risks.append(governance_risk)

            # Risques sociaux
            social_risk = self._assess_social_risk(info)
            if social_risk:
                risks.append(social_risk)

        except Exception as e:
            risks.append(
                RiskFactor(
                    name="ESG Analysis Error",
                    category=RiskCategory.ESG,
                    level=RiskLevel.MODERATE,
                    score=50.0,
                    description=f"Erreur d'analyse ESG: {str(e)}",
                    impact="MEDIUM",
                    probability="MEDIUM",
                    timeframe="LONG",
                    source="ESG Analysis",
                    last_updated=datetime.now(),
                )
            )

        return risks

    def _assess_environmental_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer les risques environnementaux"""
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        # Secteurs à haut risque environnemental
        high_env_risk = [
            "Energy",
            "Materials",
            "Oil & Gas",
            "Mining",
            "Chemicals",
            "Steel",
            "Aluminum",
            "Coal",
            "Utilities",
        ]

        is_high_risk = any(
            risk_sector.lower() in sector.lower()
            or risk_sector.lower() in industry.lower()
            for risk_sector in high_env_risk
        )

        if is_high_risk:
            level = RiskLevel.HIGH
            score = 75
            description = f"Secteur à haut risque environnemental: {sector}"
            impact = "HIGH"
        elif sector in ["Technology", "Healthcare", "Financial Services"]:
            level = RiskLevel.LOW
            score = 25
            description = f"Secteur à faible impact environnemental: {sector}"
            impact = "LOW"
        else:
            level = RiskLevel.MODERATE
            score = 45
            description = f"Impact environnemental modéré: {sector}"
            impact = "MEDIUM"

        return RiskFactor(
            name="Environmental Risk",
            category=RiskCategory.ESG,
            level=level,
            score=score,
            description=description,
            impact=impact,
            probability="HIGH",
            timeframe="LONG",
            source="Environmental Risk Assessment",
            last_updated=datetime.now(),
        )

    def _assess_governance_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer les risques de gouvernance"""
        # Indicateurs basés sur les données disponibles
        insider_ownership = info.get("heldByInsiders", 0) * 100
        institutional_ownership = info.get("heldByInstitutions", 0) * 100

        if insider_ownership > 50:
            level = RiskLevel.MODERATE
            score = 60
            description = f"Forte concentration du capital ({insider_ownership:.1f}% détenu par les dirigeants)"
        elif institutional_ownership < 30:
            level = RiskLevel.MODERATE
            score = 55
            description = f"Faible participation institutionnelle ({institutional_ownership:.1f}%)"
        else:
            level = RiskLevel.LOW
            score = 30
            description = "Structure de gouvernance équilibrée"

        return RiskFactor(
            name="Governance Risk",
            category=RiskCategory.ESG,
            level=level,
            score=score,
            description=description,
            impact="MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Governance Analysis",
            last_updated=datetime.now(),
        )

    def _assess_social_risk(self, info: Dict) -> Optional[RiskFactor]:
        """Évaluer les risques sociaux"""
        sector = info.get("sector", "")
        employees = info.get("fullTimeEmployees", 0)

        # Secteurs sensibles aux enjeux sociaux
        social_sensitive_sectors = [
            "Consumer Discretionary",
            "Technology",
            "Healthcare",
            "Financial Services",
            "Communication Services",
        ]

        is_sensitive = any(
            sens_sector.lower() in sector.lower()
            for sens_sector in social_sensitive_sectors
        )

        if is_sensitive and employees > 100000:
            level = RiskLevel.MODERATE
            score = 55
            description = (
                f"Grande entreprise dans secteur sensible ({employees:,} employés)"
            )
        elif employees > 500000:
            level = RiskLevel.MODERATE
            score = 50
            description = f"Très grande entreprise - Enjeux sociaux complexes ({employees:,} employés)"
        else:
            level = RiskLevel.LOW
            score = 30
            description = "Risques sociaux limités"

        return RiskFactor(
            name="Social Risk",
            category=RiskCategory.ESG,
            level=level,
            score=score,
            description=description,
            impact="MEDIUM",
            probability="MEDIUM",
            timeframe="LONG",
            source="Social Risk Assessment",
            last_updated=datetime.now(),
        )


# ============================================================================
# FACADE PATTERN - Service principal d'évaluation des risques
# ============================================================================


class RiskAssessmentService:
    """
    Service principal d'évaluation des risques utilisant le pattern Facade
    pour orchestrer tous les analyseurs de risques spécialisés.
    """

    def __init__(self):
        """Initialiser le service avec tous les analyseurs"""
        self._analyzers: List[IRiskAnalyzer] = [
            MarketRiskAnalyzer(),
            FundamentalRiskAnalyzer(),
            GeopoliticalRiskAnalyzer(),
            ESGRiskAnalyzer(),
        ]

    async def assess_comprehensive_risk(
        self, symbol: str, market_data: Optional[Dict] = None
    ) -> RiskAssessmentDTO:
        """
        Effectuer une évaluation complète des risques pour un symbole.

        Args:
            symbol: Symbole de l'action à analyser
            market_data: Données de marché optionnelles

        Returns:
            RiskAssessmentDTO: Évaluation complète des risques
        """
        all_risks = []

        # Exécuter tous les analyseurs en parallèle (simulation avec boucle simple)
        for analyzer in self._analyzers:
            try:
                risks = await analyzer.analyze(symbol, market_data or {})
                all_risks.extend(risks)
            except Exception as e:
                # Log l'erreur mais continue avec les autres analyseurs
                print(f"Erreur dans l'analyseur {analyzer.__class__.__name__}: {e}")
                continue

        # Calculer le score de risque global
        overall_score = self._calculate_overall_risk_score(all_risks)
        overall_level = self._determine_overall_risk_level(overall_score)

        # Grouper les risques par catégorie et convertir en DTOs
        risks_by_category = self._group_risks_by_category_as_dto(all_risks)
        all_risk_factor_dtos = [
            self._convert_risk_factor_to_dto(risk) for risk in all_risks
        ]

        # Identifier les risques critiques
        critical_risks = [
            risk
            for risk in all_risks
            if risk.level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
        ]

        return RiskAssessmentDTO(
            symbol=symbol,
            overall_risk_score=overall_score,
            overall_risk_level=overall_level.value,
            total_risk_factors=len(all_risks),
            critical_risk_count=len(critical_risks),
            risks_by_category=risks_by_category,
            all_risk_factors=all_risk_factor_dtos,
            analysis_timestamp=datetime.now(),
            summary=self._generate_risk_summary(all_risks, overall_level),
        )

    def _calculate_overall_risk_score(self, risks: List[RiskFactor]) -> float:
        """Calculer le score de risque global pondéré"""
        if not risks:
            return 50.0

        # Pondération par catégorie
        category_weights = {
            RiskCategory.MARKET: 0.25,
            RiskCategory.FUNDAMENTAL: 0.25,
            RiskCategory.GEOPOLITICAL: 0.20,
            RiskCategory.ESG: 0.15,
            RiskCategory.LIQUIDITY: 0.10,
            RiskCategory.REGULATORY: 0.05,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for risk in risks:
            weight = category_weights.get(risk.category, 0.1)
            weighted_score += risk.score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 50.0

    def _determine_overall_risk_level(self, score: float) -> RiskLevel:
        """Déterminer le niveau de risque global basé sur le score"""
        if score >= 85:
            return RiskLevel.VERY_HIGH
        elif score >= 70:
            return RiskLevel.HIGH
        elif score >= 50:
            return RiskLevel.MODERATE
        elif score >= 30:
            return RiskLevel.LOW
        else:
            return RiskLevel.VERY_LOW

    def _group_risks_by_category(
        self, risks: List[RiskFactor]
    ) -> Dict[str, List[RiskFactor]]:
        """Grouper les risques par catégorie"""
        grouped: Dict[str, List[RiskFactor]] = {}
        for risk in risks:
            category = risk.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(risk)
        return grouped

    def _convert_risk_factor_to_dto(self, risk_factor: RiskFactor) -> RiskFactorDTO:
        """Convert RiskFactor domain object to RiskFactorDTO"""
        return RiskFactorDTO(
            name=risk_factor.name,
            category=risk_factor.category.value,
            level=risk_factor.level.value,
            score=risk_factor.score,
            description=risk_factor.description,
            impact=risk_factor.impact,
            probability=risk_factor.probability,
            timeframe=risk_factor.timeframe,
            source=risk_factor.source,
            last_updated=risk_factor.last_updated,
        )

    def _group_risks_by_category_as_dto(
        self, risks: List[RiskFactor]
    ) -> Dict[str, List[RiskFactorDTO]]:
        """Grouper les risques par catégorie et convertir en DTOs"""
        grouped: Dict[str, List[RiskFactorDTO]] = {}
        for risk in risks:
            category = risk.category.value
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(self._convert_risk_factor_to_dto(risk))
        return grouped

    def _generate_risk_summary(
        self, risks: List[RiskFactor], overall_level: RiskLevel
    ) -> str:
        """Générer un résumé des risques"""
        if not risks:
            return "Aucune donnée de risque disponible"

        high_risks = [
            r for r in risks if r.level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        ]
        categories = list({r.category.value for r in risks})

        summary = f"Niveau de risque global: {overall_level.value}. "
        summary += f"Analyse de {len(risks)} facteurs de risque dans {len(categories)} catégories. "

        if high_risks:
            summary += f"{len(high_risks)} risques élevés identifiés: "
            summary += ", ".join([r.name for r in high_risks[:3]])
            if len(high_risks) > 3:
                summary += f" et {len(high_risks) - 3} autres."
        else:
            summary += "Aucun risque critique identifié."

        return summary
