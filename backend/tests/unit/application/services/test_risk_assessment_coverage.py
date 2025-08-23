"""
Tests de couverture pour Risk Assessment - Phase 2
==================================================
Tests ciblés pour couvrir les branches manquantes identifiées dans le rapport de couverture.

Architecture: AAA Pattern pour augmenter la couverture de 93.0% vers 98%+
Objectif: Tester les conditions limites et les branches non couvertes
"""

from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
import yfinance as yf

from boursa_vision.application.services.risk_assessment import (
    FundamentalRiskAnalyzer,
    MarketRiskAnalyzer,
    RiskAssessmentService,
    RiskCategory,
    RiskFactor,
    RiskLevel,
)


@pytest.fixture
def market_analyzer():
    """Market risk analyzer fixture"""
    return MarketRiskAnalyzer()


@pytest.fixture
def fundamental_analyzer():
    """Fundamental risk analyzer fixture"""
    return FundamentalRiskAnalyzer()


class TestMarketRiskAnalyzerCoverage:
    """Test coverage for MarketRiskAnalyzer branches"""

    @patch("yfinance.Ticker")
    @patch("yfinance.download")
    async def test_analyze_with_missing_beta(
        self, mock_download, mock_ticker, market_analyzer
    ):
        """Test market analysis when beta is None or 0 (line 103->108)"""
        # Setup
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        # Beta is None - should skip beta analysis
        mock_ticker_instance.info = {"beta": None}
        mock_ticker_instance.history.return_value = pd.DataFrame(
            {"Close": [100, 105, 95, 110, 108]},
            index=pd.date_range("2024-01-01", periods=5),
        )

        # Mock SPY data for correlation
        mock_download.return_value = pd.DataFrame(
            {"Close": [400, 402, 395, 405, 403]},
            index=pd.date_range("2024-01-01", periods=5),
        )

        # Execute
        risks = await market_analyzer.analyze("AAPL", {})

        # Verify - should not include beta risk
        beta_risks = [r for r in risks if "Beta" in r.name]
        assert len(beta_risks) == 0

    @patch("yfinance.Ticker")
    @patch("yfinance.download")
    async def test_analyze_with_empty_spy_data(
        self, mock_download, mock_ticker, market_analyzer
    ):
        """Test market analysis when SPY data is empty (line 109->117)"""
        # Setup
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        mock_ticker_instance.info = {"beta": 1.2}
        mock_ticker_instance.history.return_value = pd.DataFrame(
            {"Close": [100, 105, 95, 110, 108]},
            index=pd.date_range("2024-01-01", periods=5),
        )

        # Empty SPY data - should skip correlation analysis
        mock_download.return_value = pd.DataFrame()

        # Execute
        risks = await market_analyzer.analyze("AAPL", {})

        # Verify - should not include correlation risk
        correlation_risks = [r for r in risks if "Correlation" in r.name]
        assert len(correlation_risks) == 0


class TestFundamentalRiskAnalyzerCoverage:
    """Test coverage for FundamentalRiskAnalyzer branches"""

    def test_assess_growth_risk_edge_cases(self, fundamental_analyzer):
        """Test growth risk assessment for different ranges (lines 497-501, 503-504)"""
        # Test revenue_growth_percent < -10 (line 497-498)
        info = {"revenueGrowth": -0.15}  # -15%
        risk = fundamental_analyzer._assess_growth_risk(info)
        assert risk.level == RiskLevel.HIGH
        assert risk.score == 80

        # Test 0 <= revenue_growth_percent < 5 (line 503-504)
        info = {"revenueGrowth": 0.03}  # 3%
        risk = fundamental_analyzer._assess_growth_risk(info)
        assert risk.level == RiskLevel.LOW
        assert risk.score == 35

    def test_assess_revenue_quality_risk_none_return(self, fundamental_analyzer):
        """Test revenue quality when revenueGrowth is None (line 535)"""
        info = {"revenueGrowth": None}
        financials = pd.DataFrame(
            {"Revenue": [100, 110, 120]}
        )  # Non-empty but None revenue

        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk is None

    def test_assess_revenue_quality_risk_empty_financials(self, fundamental_analyzer):
        """Test revenue quality when financials is empty (line 527-528)"""
        info = {"revenueGrowth": 0.15}
        financials = pd.DataFrame()  # Empty dataframe

        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk is None

    def test_assess_revenue_quality_risk_edge_cases(self, fundamental_analyzer):
        """Test revenue quality risk for different volatility ranges (lines 538-557)"""
        # Test high volatility (abs > 30) - line 543-545
        info = {"revenueGrowth": 0.35}  # 35%
        financials = pd.DataFrame({"Revenue": [100, 110, 120]})  # Non-empty dataframe
        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk.level == RiskLevel.HIGH
        assert risk.score == 75
        assert "élevée" in risk.description

        # Test moderate volatility (15 < abs <= 30) - line 547-549
        info = {"revenueGrowth": 0.20}  # 20%
        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk.level == RiskLevel.MODERATE
        assert risk.score == 55
        assert "modérée" in risk.description

        # Test low volatility (5 < abs <= 15) - line 555-557
        info = {"revenueGrowth": 0.08}  # 8%
        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk.level == RiskLevel.LOW
        assert risk.score == 30
        assert "faible" in risk.description

    def test_assess_revenue_quality_risk_very_low(self, fundamental_analyzer):
        """Test revenue quality risk for very low volatility (line 572-573)"""
        info = {"revenueGrowth": 0.02}  # 2%
        financials = pd.DataFrame({"Revenue": [100, 102, 104]})  # Non-empty dataframe

        risk = fundamental_analyzer._assess_revenue_quality_risk(info, financials)
        assert risk.level == RiskLevel.VERY_LOW
        assert risk.score == 15
        assert "très faible" in risk.description


class TestRiskAssessmentServiceCoverage:
    """Test coverage for RiskAssessmentService branches"""

    @pytest.fixture
    def service(self):
        """Risk assessment service fixture"""
        return RiskAssessmentService()

    @patch(
        "boursa_vision.application.services.risk_assessment.MarketRiskAnalyzer.analyze"
    )
    @patch(
        "boursa_vision.application.services.risk_assessment.FundamentalRiskAnalyzer.analyze"
    )
    async def test_assess_risk_with_exception_handling(
        self, mock_fundamental, mock_market, service
    ):
        """Test risk assessment with analyzer exceptions (lines 592-621)"""
        # Setup - make one analyzer fail
        mock_market.side_effect = Exception("Market data error")
        mock_fundamental.return_value = []

        # Execute
        result = await service.assess_comprehensive_risk("AAPL", {})

        # Verify - should handle exceptions gracefully and return RiskAssessmentDTO
        from boursa_vision.application.dtos import RiskAssessmentDTO

        assert isinstance(result, RiskAssessmentDTO)
        assert hasattr(result, "overall_risk_score")

    def test_generate_risk_summary_no_high_risks(self, service):
        """Test risk summary generation with no high risks (line 1123)"""
        # Create risks with no high-level risks
        risks = [
            RiskFactor(
                name="Low Risk",
                category=RiskCategory.MARKET,
                level=RiskLevel.LOW,
                score=20.0,
                description="Test low risk",
                impact="LOW",
                probability="LOW",
                timeframe="SHORT",
                source="Test",
                last_updated=datetime.now(),
            )
        ]

        summary = service._generate_risk_summary(risks, RiskLevel.LOW)
        assert "Aucun risque critique identifié" in summary

    def test_generate_risk_summary_many_high_risks(self, service):
        """Test risk summary with more than 3 high risks (lines 995-998)"""
        # Create more than 3 high-level risks
        risks = []
        for i in range(5):
            risks.append(
                RiskFactor(
                    name=f"High Risk {i+1}",
                    category=RiskCategory.MARKET,
                    level=RiskLevel.HIGH,
                    score=80.0,
                    description=f"Test high risk {i+1}",
                    impact="HIGH",
                    probability="HIGH",
                    timeframe="SHORT",
                    source="Test",
                    last_updated=datetime.now(),
                )
            )

        summary = service._generate_risk_summary(risks, RiskLevel.HIGH)
        assert "et 2 autres" in summary


class TestAnalyzerErrorHandling:
    """Test error handling in analyzers"""

    @patch("yfinance.Ticker")
    async def test_fundamental_analyzer_with_data_error(self, mock_ticker):
        """Test fundamental analyzer error handling (lines 605-606)"""
        # Setup - make yfinance fail
        mock_ticker.side_effect = Exception("Data unavailable")

        analyzer = FundamentalRiskAnalyzer()

        # Execute
        risks = await analyzer.analyze("INVALID", {})

        # Verify - should return error risk factor
        assert len(risks) == 1
        assert "Data Unavailable" in risks[0].name
        assert risks[0].level == RiskLevel.MODERATE

    @patch("yfinance.Ticker")
    async def test_geopolitical_analyzer_error_branches(self, mock_ticker):
        """Test geopolitical analyzer error handling (lines 791-820)"""
        from boursa_vision.application.services.risk_assessment import (
            GeopoliticalRiskAnalyzer,
        )

        # Setup
        mock_ticker_instance = MagicMock()
        mock_ticker.return_value = mock_ticker_instance

        # Test missing country info (line 804-805)
        mock_ticker_instance.info = {"country": None}

        analyzer = GeopoliticalRiskAnalyzer()
        risks = await analyzer.analyze("TEST", {})

        # Should handle gracefully
        assert isinstance(risks, list)

    def test_geopolitical_analyzer_extreme_cases(self):
        """Test geopolitical analyzer extreme cases (lines 933-935)"""
        from boursa_vision.application.services.risk_assessment import (
            GeopoliticalRiskAnalyzer,
        )

        analyzer = GeopoliticalRiskAnalyzer()

        # Test very high employee count (line 933-935)
        info = {"fullTimeEmployees": 600000}
        risk = analyzer._assess_international_exposure_risk(info)

        assert risk is not None
        assert (
            risk.level == RiskLevel.VERY_LOW
        )  # Large companies typically have lower risk
