"""
Tests unitaires pour le service InvestmentIntelligenceService
Couverture exhaustive des fonctionnalités critiques : stratégies d'investissement,
scoring, recommandations, analyses de portefeuille et optimisation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

from boursa_vision.application.services.investment_intelligence import (
    InvestmentIntelligenceService,
    InvestmentRecommendation,
    ValueInvestingStrategy,
    GrowthInvestingStrategy,
    RecommendationType,
    RiskLevel,
    InvestmentHorizon,
    AnalysisConfig,
)
from boursa_vision.application.services.market_scanner import (
    MarketScannerService,
    ScanResult,
    ScanConfig,
    ScanStrategy,
)


@pytest.mark.unit
@pytest.mark.intelligence
class TestInvestmentRecommendation:
    """Tests pour la classe InvestmentRecommendation."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.test_recommendation = InvestmentRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            recommendation=RecommendationType.BUY,
            confidence_score=85.5,
            target_price=200.0,
            current_price=180.0,
            potential_return=11.11,
            risk_level=RiskLevel.MODERATE,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            sector="Technology",
            market_cap=3000000000000,
            fundamental_score=80.0,
            technical_score=75.0,
            momentum_score=70.0,
            value_score=85.0,
            quality_score=90.0,
            pe_ratio=25.5,
            pb_ratio=8.2,
            roe=28.5,
            debt_to_equity=0.35,
            rsi=58.0,
            macd_signal="BUY",
            reasons=["Strong fundamentals", "Good technical outlook"],
            warnings=["High P/E ratio"]
        )

    def test_should_create_recommendation_with_all_attributes(self):
        """Test de création d'une recommandation complète."""
        # Given & When - Créé dans setup_method
        rec = self.test_recommendation
        
        # Then
        assert rec.symbol == "AAPL"
        assert abs(rec.confidence_score - 85.5) < 0.01
        assert rec.recommendation == RecommendationType.BUY
        assert rec.risk_level == RiskLevel.MODERATE
        assert len(rec.reasons) == 2
        assert len(rec.warnings) == 1

    def test_should_convert_to_dict_correctly(self):
        """Test de conversion en dictionnaire."""
        # Given
        rec = self.test_recommendation
        
        # When
        result = rec.to_dict()
        
        # Then
        assert result["symbol"] == "AAPL"
        assert abs(result["confidence_score"] - 85.5) < 0.01
        assert result["recommendation"] == "BUY"
        assert result["risk_level"] == "MODERATE"
        assert result["investment_horizon"] == "MEDIUM_TERM"
        assert isinstance(result["last_updated"], str)
        assert "fundamental_score" in result
        assert "technical_score" in result

    def test_should_handle_optional_values_in_to_dict(self):
        """Test de gestion des valeurs optionnelles dans to_dict."""
        # Given
        rec = InvestmentRecommendation(
            symbol="TEST",
            name="Test Corp",
            recommendation=RecommendationType.HOLD,
            confidence_score=50.0,
            target_price=None,  # Valeur optionnelle
            current_price=100.0,
            potential_return=0.0,
            risk_level=RiskLevel.LOW,
            investment_horizon=InvestmentHorizon.LONG_TERM,
            sector=None,  # Valeur optionnelle
            market_cap=None,  # Valeur optionnelle
            fundamental_score=60.0,
            technical_score=40.0,
            momentum_score=30.0,
            value_score=70.0,
            quality_score=55.0,
            pe_ratio=None,
            pb_ratio=None,
            roe=None,
            debt_to_equity=None,
            rsi=None,
            macd_signal=None
        )
        
        # When
        result = rec.to_dict()
        
        # Then
        assert result["target_price"] is None
        assert result["sector"] is None
        assert result["pe_ratio"] is None
        assert result["symbol"] == "TEST"

    def test_should_set_default_timestamp(self):
        """Test que last_updated est défini par défaut."""
        # Given & When
        rec = InvestmentRecommendation(
            symbol="TEST",
            name="Test Corp",
            recommendation=RecommendationType.SELL,
            confidence_score=25.0,
            target_price=80.0,
            current_price=100.0,
            potential_return=-20.0,
            risk_level=RiskLevel.HIGH,
            investment_horizon=InvestmentHorizon.SHORT_TERM,
            sector="Finance",
            market_cap=1000000000,
            fundamental_score=30.0,
            technical_score=20.0,
            momentum_score=15.0,
            value_score=40.0,
            quality_score=25.0,
            pe_ratio=15.0,
            pb_ratio=1.2,
            roe=8.5,
            debt_to_equity=0.8,
            rsi=72.0,
            macd_signal="SELL"
        )
        
        # Then
        assert rec.last_updated is not None
        assert isinstance(rec.last_updated, datetime)
        # Vérifie que le timestamp est récent (moins d'1 minute)
        time_diff = datetime.now(timezone.utc) - rec.last_updated
        assert time_diff.total_seconds() < 60


@pytest.mark.unit
@pytest.mark.intelligence
class TestValueInvestingStrategy:
    """Tests complets pour ValueInvestingStrategy."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.strategy = ValueInvestingStrategy()
        self.mock_scan_result = Mock(spec=ScanResult)
        self.mock_scan_result.symbol = "VTI"
        self.mock_scan_result.name = "Value Corp"
        self.mock_scan_result.price = 100.0
        self.mock_scan_result.sector = "Utilities"
        self.mock_scan_result.market_cap = 5000000000
        self.mock_scan_result.pe_ratio = 12.0
        self.mock_scan_result.pb_ratio = 1.2
        self.mock_scan_result.roe = 18.0
        self.mock_scan_result.debt_to_equity = 0.4
        self.mock_scan_result.dividend_yield = 2.5
        self.mock_scan_result.fundamental_score = 80.0
        self.mock_scan_result.technical_score = 70.0
        self.mock_scan_result.rsi = 45.0
        self.mock_scan_result.macd_signal = "NEUTRAL"
        self.mock_scan_result.change_percent = 1.5

    def test_should_analyze_good_value_opportunity(self):
        """Test d'analyse d'une bonne opportunité value."""
        # Given - mock_scan_result configuré avec de meilleures valeurs value
        self.mock_scan_result.pe_ratio = 10.0  # Excellent P/E
        self.mock_scan_result.pb_ratio = 1.0   # Excellent P/B
        self.mock_scan_result.roe = 22.0       # Excellent ROE
        self.mock_scan_result.debt_to_equity = 0.2  # Faible dette
        self.mock_scan_result.dividend_yield = 3.5  # Bon dividende
        
        # When
        result = self.strategy.analyze_opportunity(self.mock_scan_result)
        
        # Then
        assert result is not None
        assert result.symbol == "VTI"
        assert result.recommendation in [RecommendationType.BUY, RecommendationType.STRONG_BUY, RecommendationType.HOLD]
        assert result.confidence_score >= 60
        assert result.investment_horizon == InvestmentHorizon.LONG_TERM
        assert result.risk_level == RiskLevel.MODERATE
        assert len(result.reasons) > 0

    def test_should_reject_poor_value_opportunity(self):
        """Test de rejet d'une mauvaise opportunité value."""
        # Given
        self.mock_scan_result.pe_ratio = 35.0  # P/E trop élevé
        self.mock_scan_result.pb_ratio = 4.0   # P/B trop élevé
        self.mock_scan_result.roe = 5.0        # ROE trop faible
        self.mock_scan_result.debt_to_equity = 2.0  # Dette trop élevée
        
        # When
        result = self.strategy.analyze_opportunity(self.mock_scan_result)
        
        # Then
        assert result is None

    def test_should_score_pe_ratio_correctly(self):
        """Test du scoring du P/E ratio."""
        # Given & When & Then
        assert self.strategy._score_pe_ratio(8.0) == 25    # Excellent
        assert self.strategy._score_pe_ratio(12.0) == 15   # Bon
        assert self.strategy._score_pe_ratio(18.0) == 5    # Acceptable
        assert self.strategy._score_pe_ratio(25.0) == -10  # Élevé
        assert self.strategy._score_pe_ratio(None) == 0    # Pas de données
        assert self.strategy._score_pe_ratio(-5.0) == 0    # Valeur négative

    def test_should_score_pb_ratio_correctly(self):
        """Test du scoring du P/B ratio."""
        # Given & When & Then
        assert self.strategy._score_pb_ratio(0.8) == 20    # Excellent
        assert self.strategy._score_pb_ratio(1.2) == 10    # Bon
        assert self.strategy._score_pb_ratio(1.8) == 0     # Neutre
        assert self.strategy._score_pb_ratio(2.5) == -10   # Élevé
        assert self.strategy._score_pb_ratio(None) == 0    # Pas de données

    def test_should_score_dividend_yield_correctly(self):
        """Test du scoring du dividend yield."""
        # Given & When & Then
        assert self.strategy._score_dividend_yield(4.0) == 15  # Bon dividende
        assert self.strategy._score_dividend_yield(2.0) == 5   # Dividende modeste
        assert self.strategy._score_dividend_yield(0.5) == 0   # Faible dividende
        assert self.strategy._score_dividend_yield(None) == 0  # Pas de dividende

    def test_should_calculate_value_score_within_bounds(self):
        """Test que le score de valeur reste dans les limites 0-100."""
        # Given - Configuration extrême positive
        self.mock_scan_result.pe_ratio = 5.0  # Excellent
        self.mock_scan_result.pb_ratio = 0.5  # Excellent
        self.mock_scan_result.dividend_yield = 5.0  # Excellent
        
        # When
        score = self.strategy._calculate_value_score(self.mock_scan_result)
        
        # Then
        assert 0 <= score <= 100

    def test_should_calculate_quality_score_with_valid_components(self):
        """Test de calcul du score de qualité avec composants valides."""
        # Given - Bonnes métriques de qualité
        self.mock_scan_result.roe = 25.0
        self.mock_scan_result.debt_to_equity = 0.2
        
        # When
        score = self.strategy._calculate_quality_score(self.mock_scan_result)
        
        # Then
        assert score > 50  # Score supérieur à la base
        assert 0 <= score <= 100

    def test_should_determine_recommendation_levels(self):
        """Test de détermination des niveaux de recommandation."""
        # Given & When & Then
        assert self.strategy._determine_recommendation(90.0) == RecommendationType.STRONG_BUY
        assert self.strategy._determine_recommendation(78.0) == RecommendationType.BUY
        assert self.strategy._determine_recommendation(65.0) == RecommendationType.HOLD
        assert self.strategy._determine_recommendation(45.0) == RecommendationType.SELL

    def test_should_calculate_conservative_target_price(self):
        """Test de calcul d'un prix cible conservateur."""
        # Given
        self.mock_scan_result.price = 100.0
        self.mock_scan_result.pe_ratio = 20.0
        
        # When
        target_price = self.strategy._calculate_target_price(self.mock_scan_result)
        
        # Then
        assert target_price is not None
        # Le prix cible devrait être raisonnable (utilise P/E cible de 15 max)
        expected_eps = 100.0 / 20.0  # 5.0
        expected_target = expected_eps * 15  # 75.0
        assert target_price == expected_target

    def test_should_handle_invalid_pe_for_target_price(self):
        """Test de gestion P/E invalide pour calcul prix cible."""
        # Given
        self.mock_scan_result.pe_ratio = None
        
        # When
        target_price = self.strategy._calculate_target_price(self.mock_scan_result)
        
        # Then
        assert target_price is None

    def test_should_return_strategy_name(self):
        """Test du nom de stratégie."""
        # Given & When & Then
        assert self.strategy.get_strategy_name() == "Value Investing"


@pytest.mark.unit
@pytest.mark.intelligence
class TestGrowthInvestingStrategy:
    """Tests complets pour GrowthInvestingStrategy."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.strategy = GrowthInvestingStrategy()
        self.mock_scan_result = Mock(spec=ScanResult)
        self.mock_scan_result.symbol = "TECH"
        self.mock_scan_result.name = "Tech Growth Corp"
        self.mock_scan_result.price = 150.0
        self.mock_scan_result.sector = "Technology"
        self.mock_scan_result.market_cap = 50000000000  # 50B
        self.mock_scan_result.pe_ratio = 30.0
        self.mock_scan_result.pb_ratio = 5.0
        self.mock_scan_result.roe = 22.0
        self.mock_scan_result.debt_to_equity = 0.3
        self.mock_scan_result.dividend_yield = 0.5
        self.mock_scan_result.fundamental_score = 75.0
        self.mock_scan_result.technical_score = 85.0
        self.mock_scan_result.rsi = 62.0
        self.mock_scan_result.macd_signal = "BUY"
        self.mock_scan_result.change_percent = 8.5

    def test_should_analyze_good_growth_opportunity(self):
        """Test d'analyse d'une bonne opportunité growth."""
        # Given - mock configuré avec de bonnes métriques growth
        
        # When
        result = self.strategy.analyze_opportunity(self.mock_scan_result)
        
        # Then
        assert result is not None
        assert result.symbol == "TECH"
        assert result.recommendation in [RecommendationType.BUY, RecommendationType.STRONG_BUY]
        assert result.risk_level == RiskLevel.HIGH
        assert result.investment_horizon == InvestmentHorizon.MEDIUM_TERM
        assert result.momentum_score >= 60

    def test_should_reject_poor_growth_opportunity(self):
        """Test de rejet d'une mauvaise opportunité growth."""
        # Given
        self.mock_scan_result.change_percent = -10.0  # Performance négative
        self.mock_scan_result.rsi = 25.0              # RSI très bas
        self.mock_scan_result.macd_signal = "SELL"    # Signal baissier
        self.mock_scan_result.roe = 5.0               # ROE faible
        
        # When
        result = self.strategy.analyze_opportunity(self.mock_scan_result)
        
        # Then
        assert result is None

    def test_should_calculate_momentum_score_correctly(self):
        """Test de calcul du score de momentum."""
        # Given - Bonnes métriques de momentum
        self.mock_scan_result.change_percent = 7.0   # Bonne performance
        self.mock_scan_result.rsi = 65.0             # RSI dans bonne zone
        self.mock_scan_result.macd_signal = "BUY"    # Signal haussier
        
        # When
        score = self.strategy._calculate_momentum_score(self.mock_scan_result)
        
        # Then
        assert score > 50  # Score supérieur à la base
        assert 0 <= score <= 100

    def test_should_calculate_growth_potential_with_tech_sector(self):
        """Test de calcul du potentiel de croissance avec secteur tech."""
        # Given
        self.mock_scan_result.sector = "Technology"
        self.mock_scan_result.roe = 20.0
        self.mock_scan_result.market_cap = 25000000000  # 25B (mid-cap)
        
        # When
        score = self.strategy._calculate_growth_potential(self.mock_scan_result)
        
        # Then
        assert score > 50  # Bonus tech + bon ROE + bonne cap
        assert 0 <= score <= 100

    def test_should_set_aggressive_target_price(self):
        """Test de calcul d'un prix cible agressif."""
        # Given
        self.mock_scan_result.price = 100.0
        
        # When
        target_price = self.strategy._calculate_target_price(self.mock_scan_result)
        
        # Then
        assert abs(target_price - 125.0) < 0.01  # 25% upside

    def test_should_return_strategy_name(self):
        """Test du nom de stratégie."""
        # Given & When & Then
        assert self.strategy.get_strategy_name() == "Growth Investing"


@pytest.mark.unit
@pytest.mark.intelligence
class TestInvestmentIntelligenceService:
    """Tests complets pour InvestmentIntelligenceService."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.mock_scanner = Mock(spec=MarketScannerService)
        self.service = InvestmentIntelligenceService(self.mock_scanner)
        
        # Mock scan results
        self.mock_scan_results = [
            self._create_mock_scan_result("AAPL", "Apple", 180.0, "Technology", pe_ratio=25.0),
            self._create_mock_scan_result("MSFT", "Microsoft", 350.0, "Technology", pe_ratio=30.0),
            self._create_mock_scan_result("JNJ", "Johnson & Johnson", 170.0, "Healthcare", pe_ratio=15.0),
        ]
        
        # Configuration de test
        self.test_config = AnalysisConfig(
            min_confidence_score=70.0,
            max_recommendations=10,
            min_market_cap=1e9,
            max_risk_level=RiskLevel.HIGH
        )

    def _create_mock_scan_result(self, symbol: str, name: str, price: float, 
                                sector: str, pe_ratio: float = 20.0) -> Mock:
        """Crée un mock ScanResult."""
        mock = Mock(spec=ScanResult)
        mock.symbol = symbol
        mock.name = name
        mock.price = price
        mock.sector = sector
        mock.market_cap = 10000000000  # 10B
        mock.pe_ratio = pe_ratio
        mock.pb_ratio = 2.0
        mock.roe = 15.0
        mock.debt_to_equity = 0.5
        mock.dividend_yield = 2.0
        mock.fundamental_score = 75.0
        mock.technical_score = 70.0
        mock.rsi = 55.0
        mock.macd_signal = "BUY"
        mock.change_percent = 3.0
        return mock

    @pytest.mark.asyncio
    async def test_should_generate_investment_recommendations_successfully(self):
        """Test de génération de recommandations d'investissement."""
        # Given
        self.mock_scanner.scan_market = AsyncMock(return_value=self.mock_scan_results)
        
        # When
        recommendations = await self.service.generate_investment_recommendations(self.test_config)
        
        # Then
        assert isinstance(recommendations, list)
        assert len(recommendations) <= self.test_config.max_recommendations
        self.mock_scanner.scan_market.assert_called_once()
        
        # Vérifier que les recommandations ont les bonnes propriétés
        for rec in recommendations:
            assert isinstance(rec, InvestmentRecommendation)
            assert rec.confidence_score >= self.test_config.min_confidence_score

    @pytest.mark.asyncio
    async def test_should_handle_scanner_exceptions_gracefully(self):
        """Test de gestion des exceptions du scanner."""
        # Given
        self.mock_scanner.scan_market = AsyncMock(side_effect=Exception("Scanner error"))
        
        # When & Then
        with pytest.raises(Exception):
            await self.service.generate_investment_recommendations(self.test_config)

    @pytest.mark.asyncio
    async def test_should_deduplicate_recommendations_correctly(self):
        """Test de déduplication des recommandations."""
        # Given
        self.mock_scanner.scan_market = AsyncMock(return_value=self.mock_scan_results)
        
        # Ajouter un doublon avec meilleur score
        duplicate_scan = self._create_mock_scan_result("AAPL", "Apple", 180.0, "Technology", pe_ratio=12.0)
        duplicate_scan.roe = 25.0  # Meilleur ROE pour score plus élevé
        self.mock_scan_results.append(duplicate_scan)
        
        # When
        recommendations = await self.service.generate_investment_recommendations(self.test_config)
        
        # Then
        symbols = [rec.symbol for rec in recommendations]
        assert len(symbols) == len(set(symbols))  # Pas de doublons

    def test_should_get_top_opportunities_correctly(self):
        """Test de récupération des meilleures opportunités."""
        # Given
        self.service.cached_recommendations = [
            self._create_test_recommendation("AAPL", RecommendationType.STRONG_BUY, 95.0),
            self._create_test_recommendation("MSFT", RecommendationType.BUY, 85.0),
            self._create_test_recommendation("GOOGL", RecommendationType.HOLD, 65.0),
        ]
        
        # When
        opportunities = self.service.get_top_opportunities(5)
        
        # Then
        assert len(opportunities) == 2  # Seuls STRONG_BUY et BUY
        assert opportunities[0].symbol == "AAPL"
        assert opportunities[1].symbol == "MSFT"

    def test_should_get_sector_recommendations_correctly(self):
        """Test de récupération des recommandations par secteur."""
        # Given
        self.service.cached_recommendations = [
            self._create_test_recommendation("AAPL", RecommendationType.STRONG_BUY, 95.0, "Technology"),
            self._create_test_recommendation("MSFT", RecommendationType.BUY, 85.0, "Technology"),
            self._create_test_recommendation("JNJ", RecommendationType.BUY, 80.0, "Healthcare"),
            self._create_test_recommendation("PG", RecommendationType.HOLD, 70.0, "Consumer Goods"),
        ]
        
        # When
        sector_recs = self.service.get_sector_recommendations()
        
        # Then
        assert "Technology" in sector_recs
        assert "Healthcare" in sector_recs
        assert "Consumer Goods" not in sector_recs  # HOLD ignoré
        assert len(sector_recs["Technology"]) == 2
        assert sector_recs["Technology"][0].symbol == "AAPL"  # Trié par score

    def test_should_generate_portfolio_suggestions(self):
        """Test de génération de suggestions de portefeuille."""
        # Given
        self.service.cached_recommendations = [
            self._create_test_recommendation("AAPL", RecommendationType.STRONG_BUY, 95.0, "Technology"),
            self._create_test_recommendation("JNJ", RecommendationType.BUY, 85.0, "Healthcare"),
            self._create_test_recommendation("JPM", RecommendationType.BUY, 80.0, "Finance"),
        ]
        
        # When
        portfolio = self.service.get_portfolio_suggestions(100000.0)
        
        # Then
        assert "portfolio_suggestions" in portfolio
        assert "diversification_score" in portfolio
        assert "expected_return" in portfolio
        assert len(portfolio["portfolio_suggestions"]) == 3
        
        # Vérifier la diversification
        sectors = {s["sector"] for s in portfolio["portfolio_suggestions"]}
        assert len(sectors) == 3

    def test_should_determine_update_necessity_correctly(self):
        """Test de détermination du besoin de mise à jour."""
        # Given - Pas d'analyse précédente
        assert self.service.should_update_analysis(self.test_config) is True
        
        # Given - Analyse récente
        self.service.last_analysis = datetime.now(timezone.utc) - timedelta(hours=2)
        assert self.service.should_update_analysis(self.test_config) is False
        
        # Given - Analyse ancienne
        self.service.last_analysis = datetime.now(timezone.utc) - timedelta(hours=8)
        assert self.service.should_update_analysis(self.test_config) is True

    def test_should_generate_analysis_summary(self):
        """Test de génération du résumé d'analyse."""
        # Given
        self.service.cached_recommendations = [
            self._create_test_recommendation("A", RecommendationType.STRONG_BUY, 95.0, "Tech"),
            self._create_test_recommendation("B", RecommendationType.BUY, 85.0, "Tech"),
            self._create_test_recommendation("C", RecommendationType.HOLD, 70.0, "Health"),
        ]
        self.service.last_analysis = datetime.now(timezone.utc)
        
        # When
        summary = self.service.get_analysis_summary()
        
        # Then
        assert summary["total_recommendations"] == 3
        assert summary["strong_buys"] == 1
        assert summary["buys"] == 1
        assert summary["holds"] == 1
        assert summary["sectors_analyzed"] == 2
        assert 70 <= summary["average_confidence"] <= 95
        assert "last_updated" in summary

    def test_should_handle_empty_recommendations_in_summary(self):
        """Test de gestion des recommandations vides dans le résumé."""
        # Given - Pas de recommandations
        self.service.cached_recommendations = []
        
        # When
        summary = self.service.get_analysis_summary()
        
        # Then
        assert "error" in summary
        assert summary["error"] == "Aucune analyse disponible"

    def _create_test_recommendation(self, symbol: str, recommendation: RecommendationType,
                                   confidence: float, sector: str = "Technology") -> InvestmentRecommendation:
        """Crée une recommandation de test."""
        return InvestmentRecommendation(
            symbol=symbol,
            name=f"{symbol} Corp",
            recommendation=recommendation,
            confidence_score=confidence,
            target_price=200.0,
            current_price=180.0,
            potential_return=11.11,
            risk_level=RiskLevel.MODERATE,
            investment_horizon=InvestmentHorizon.MEDIUM_TERM,
            sector=sector,
            market_cap=10000000000,
            fundamental_score=80.0,
            technical_score=75.0,
            momentum_score=70.0,
            value_score=85.0,
            quality_score=90.0,
            pe_ratio=25.0,
            pb_ratio=2.0,
            roe=15.0,
            debt_to_equity=0.5,
            rsi=55.0,
            macd_signal="BUY"
        )


@pytest.mark.unit
@pytest.mark.intelligence  
class TestAnalysisConfig:
    """Tests pour AnalysisConfig."""

    def test_should_create_config_with_defaults(self):
        """Test de création de config avec valeurs par défaut."""
        # Given & When
        config = AnalysisConfig()
        
        # Then
        assert abs(config.min_confidence_score - 70.0) < 0.01
        assert config.max_recommendations == 50
        assert abs(config.min_market_cap - 1e9) < 0.01
        assert config.max_risk_level == RiskLevel.HIGH
        assert config.update_frequency_hours == 6

    def test_should_create_config_with_custom_values(self):
        """Test de création de config avec valeurs custom."""
        # Given & When
        config = AnalysisConfig(
            min_confidence_score=80.0,
            max_recommendations=25,
            include_sectors={"Technology", "Healthcare"},
            exclude_sectors={"Energy"},
            min_market_cap=5e9,
            max_risk_level=RiskLevel.MODERATE
        )
        
        # Then
        assert abs(config.min_confidence_score - 80.0) < 0.01
        assert config.max_recommendations == 25
        assert "Technology" in config.include_sectors
        assert "Energy" in config.exclude_sectors
        assert abs(config.min_market_cap - 5e9) < 0.01
        assert config.max_risk_level == RiskLevel.MODERATE


@pytest.mark.unit
@pytest.mark.intelligence
class TestPerformanceIntelligence:
    """Tests de performance pour le service d'intelligence."""

    def setup_method(self):
        """Configuration pour les tests de performance."""
        self.mock_scanner = Mock(spec=MarketScannerService)
        self.service = InvestmentIntelligenceService(self.mock_scanner)

    @pytest.mark.asyncio
    async def test_should_complete_analysis_under_performance_threshold(self):
        """Test que l'analyse se complete sous le seuil de performance."""
        # Given
        mock_results = [
            self._create_fast_scan_result(f"SYM{i}") for i in range(100)
        ]
        self.mock_scanner.scan_market = AsyncMock(return_value=mock_results)
        config = AnalysisConfig(max_recommendations=50)
        
        # When
        start_time = datetime.now(timezone.utc)
        await self.service.generate_investment_recommendations(config)
        end_time = datetime.now(timezone.utc)
        
        # Then
        analysis_time = (end_time - start_time).total_seconds()
        assert analysis_time < 5.0  # Moins de 5 secondes pour 100 symboles

    def _create_fast_scan_result(self, symbol: str) -> Mock:
        """Crée un scan result optimisé pour les tests de performance."""
        mock = Mock(spec=ScanResult)
        mock.symbol = symbol
        mock.name = f"{symbol} Corp"
        mock.price = 100.0
        mock.sector = "Technology"
        mock.market_cap = 10000000000
        mock.pe_ratio = 20.0
        mock.pb_ratio = 2.0
        mock.roe = 15.0
        mock.debt_to_equity = 0.5
        mock.dividend_yield = 2.0
        mock.fundamental_score = 75.0
        mock.technical_score = 70.0
        mock.rsi = 55.0
        mock.macd_signal = "BUY"
        mock.change_percent = 3.0
        return mock
