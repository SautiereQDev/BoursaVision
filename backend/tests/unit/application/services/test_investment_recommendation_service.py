"""
Tests unitaires pour InvestmentRecommendationService
==================================================

Tests unitaires complets pour le service de recommandations d'investissement.
Ce service utilise l'analyse avancée pour générer des recommandations de portfolio optimisées.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from boursa_vision.application.services.advanced_analysis_service import (
    ComprehensiveAnalysisResult,
)
from boursa_vision.application.services.investment_recommendation_service import (
    InvestmentRecommendation,
    InvestmentRecommendationService,
    PortfolioRecommendation,
    RecommendationRequest,
)


class TestRecommendationRequest:
    """Tests pour la classe RecommendationRequest."""

    def test_default_values(self):
        """Test des valeurs par défaut."""
        request = RecommendationRequest()

        assert request.symbols is None
        assert request.max_recommendations == 10
        assert request.risk_tolerance == "MODERATE"
        assert request.investment_horizon == "MEDIUM"
        assert request.exclude_sectors == []
        assert abs(request.min_score - 60.0) < 0.001
        assert request.max_risk_level == "HIGH"

    def test_custom_values(self):
        """Test avec des valeurs personnalisées."""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        exclude_sectors = ["Energy", "Materials"]

        request = RecommendationRequest(
            symbols=symbols,
            max_recommendations=5,
            risk_tolerance="LOW",
            investment_horizon="LONG",
            exclude_sectors=exclude_sectors,
            min_score=70.0,
            max_risk_level="MODERATE",
        )

        assert request.symbols == symbols
        assert request.max_recommendations == 5
        assert request.risk_tolerance == "LOW"
        assert request.investment_horizon == "LONG"
        assert request.exclude_sectors == exclude_sectors
        assert abs(request.min_score - 70.0) < 0.001
        assert request.max_risk_level == "MODERATE"

    def test_risk_tolerance_validation(self):
        """Test des valeurs de tolérance au risque."""
        valid_values = ["LOW", "MODERATE", "HIGH"]
        for value in valid_values:
            request = RecommendationRequest(risk_tolerance=value)
            assert request.risk_tolerance == value

    def test_investment_horizon_validation(self):
        """Test des valeurs d'horizon d'investissement."""
        valid_values = ["SHORT", "MEDIUM", "LONG"]
        for value in valid_values:
            request = RecommendationRequest(investment_horizon=value)
            assert request.investment_horizon == value

    def test_max_risk_level_validation(self):
        """Test des valeurs de niveau de risque maximum."""
        valid_values = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
        for value in valid_values:
            request = RecommendationRequest(max_risk_level=value)
            assert request.max_risk_level == value


class TestInvestmentRecommendation:
    """Tests pour la classe InvestmentRecommendation."""

    def test_required_fields(self):
        """Test des champs obligatoires."""
        recommendation = InvestmentRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=150.0,
            currency="USD",
            recommendation="BUY",
            overall_score=85.0,
            confidence=0.9,
            risk_level="MODERATE",
            technical_score=80.0,
            fundamental_score=85.0,
            momentum_score=90.0,
        )

        assert recommendation.symbol == "AAPL"
        assert recommendation.name == "Apple Inc."
        assert abs(recommendation.current_price - 150.0) < 0.001
        assert recommendation.currency == "USD"
        assert recommendation.recommendation == "BUY"
        assert abs(recommendation.overall_score - 85.0) < 0.001
        assert abs(recommendation.confidence - 0.9) < 0.001
        assert recommendation.risk_level == "MODERATE"
        assert abs(recommendation.technical_score - 80.0) < 0.001
        assert abs(recommendation.fundamental_score - 85.0) < 0.001
        assert abs(recommendation.momentum_score - 90.0) < 0.001

    def test_optional_fields_defaults(self):
        """Test des valeurs par défaut des champs optionnels."""
        recommendation = InvestmentRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=150.0,
            currency="USD",
            recommendation="BUY",
            overall_score=85.0,
            confidence=0.9,
            risk_level="MODERATE",
            technical_score=80.0,
            fundamental_score=85.0,
            momentum_score=90.0,
        )

        assert recommendation.target_price is None
        assert recommendation.stop_loss is None
        assert recommendation.upside_potential is None
        assert recommendation.strengths == []
        assert recommendation.weaknesses == []
        assert recommendation.key_insights == []
        assert recommendation.data_quality == "GOOD"
        assert isinstance(recommendation.analyzed_at, datetime)

    def test_upside_potential_calculation(self):
        """Test du calcul du potentiel de hausse."""
        recommendation = InvestmentRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=150.0,
            currency="USD",
            recommendation="BUY",
            overall_score=85.0,
            confidence=0.9,
            risk_level="MODERATE",
            technical_score=80.0,
            fundamental_score=85.0,
            momentum_score=90.0,
            target_price=180.0,
            upside_potential=20.0,  # (180-150)/150 * 100
        )

        assert abs(recommendation.upside_potential - 20.0) < 0.001

    def test_with_detailed_analysis(self):
        """Test avec analyse détaillée."""
        strengths = ["Strong financials", "Market leadership"]
        weaknesses = ["High valuation", "Market saturation"]
        insights = ["AI growth potential", "Services expansion"]

        recommendation = InvestmentRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=150.0,
            currency="USD",
            recommendation="BUY",
            overall_score=85.0,
            confidence=0.9,
            risk_level="MODERATE",
            technical_score=80.0,
            fundamental_score=85.0,
            momentum_score=90.0,
            target_price=180.0,
            stop_loss=140.0,
            upside_potential=20.0,
            strengths=strengths,
            weaknesses=weaknesses,
            key_insights=insights,
            data_quality="EXCELLENT",
        )

        assert recommendation.strengths == strengths
        assert recommendation.weaknesses == weaknesses
        assert recommendation.key_insights == insights
        assert recommendation.data_quality == "EXCELLENT"


class TestPortfolioRecommendation:
    """Tests pour la classe PortfolioRecommendation."""

    def test_creation(self):
        """Test de création d'une recommandation de portfolio."""
        recommendations = [
            InvestmentRecommendation(
                symbol="AAPL",
                name="Apple Inc.",
                current_price=150.0,
                currency="USD",
                recommendation="BUY",
                overall_score=85.0,
                confidence=0.9,
                risk_level="MODERATE",
                technical_score=80.0,
                fundamental_score=85.0,
                momentum_score=90.0,
            )
        ]

        portfolio_metrics = {"total_recommendations": 1}
        analysis_summary = {"total_analyzed": 10}
        risk_assessment = {"average_risk_score": 50.0}
        sector_allocation = {"Technology": 100.0}

        portfolio_recommendation = PortfolioRecommendation(
            recommendations=recommendations,
            portfolio_metrics=portfolio_metrics,
            analysis_summary=analysis_summary,
            risk_assessment=risk_assessment,
            sector_allocation=sector_allocation,
        )

        assert len(portfolio_recommendation.recommendations) == 1
        assert portfolio_recommendation.portfolio_metrics == portfolio_metrics
        assert portfolio_recommendation.analysis_summary == analysis_summary
        assert portfolio_recommendation.risk_assessment == risk_assessment
        assert portfolio_recommendation.sector_allocation == sector_allocation
        assert isinstance(portfolio_recommendation.generated_at, datetime)


class TestInvestmentRecommendationService:
    """Tests pour le service InvestmentRecommendationService."""

    @pytest.fixture
    def mock_analyzer(self):
        """Mock de l'analyseur avancé."""
        mock = Mock()
        mock.analyze_investment.return_value = self._create_mock_analysis("AAPL")
        return mock

    @pytest.fixture
    def service(self, mock_analyzer):
        """Service avec analyseur mocké."""
        service = InvestmentRecommendationService()
        service.analyzer = mock_analyzer
        return service

    def _create_mock_analysis(self, symbol: str) -> ComprehensiveAnalysisResult:
        """Crée un résultat d'analyse mocké."""
        return ComprehensiveAnalysisResult(
            investment_symbol=symbol,
            overall_score=75.0,
            confidence=0.8,
            risk_level="MODERATE",
            recommendation="BUY",
            technical_score=70.0,
            fundamental_score=80.0,
            momentum_score=75.0,
            target_price=180.0,
            stop_loss=140.0,
            strengths=["Strong fundamentals"],
            weaknesses=["High valuation"],
            insights=["Growth potential"],
        )

    def test_initialization(self):
        """Test de l'initialisation du service."""
        service = InvestmentRecommendationService()

        assert service.analyzer is not None
        assert service._cache == {}
        assert service._cache_ttl == 3600

    def test_indices_symbols_structure(self):
        """Test de la structure des symboles d'indices."""
        service = InvestmentRecommendationService()

        assert "cac40" in service.INDICES_SYMBOLS
        assert "nasdaq100" in service.INDICES_SYMBOLS
        assert "ftse100" in service.INDICES_SYMBOLS
        assert "dax40" in service.INDICES_SYMBOLS

        # Vérifier que chaque indice a des symboles
        for index_name, symbols in service.INDICES_SYMBOLS.items():
            assert isinstance(symbols, list)
            assert len(symbols) > 0
            for symbol in symbols:
                assert isinstance(symbol, str)
                assert len(symbol) > 0

    def test_get_symbols_to_analyze_with_custom_symbols(self, service):
        """Test avec symboles personnalisés."""
        request = RecommendationRequest(symbols=["AAPL", "MSFT", "GOOGL"])
        symbols = service._get_symbols_to_analyze(request)

        assert symbols == ["AAPL", "MSFT", "GOOGL"]

    def test_get_symbols_to_analyze_with_all_indices(self, service):
        """Test avec tous les symboles d'indices."""
        request = RecommendationRequest()
        symbols = service._get_symbols_to_analyze(request)

        # Doit retourner tous les symboles uniques des indices
        assert len(symbols) > 0
        assert isinstance(symbols, list)

        # Vérifier qu'il n'y a pas de doublons
        assert len(symbols) == len(set(symbols))

        # Vérifier que certains symboles connus sont présents
        all_symbols_from_indices = []
        for index_symbols in service.INDICES_SYMBOLS.values():
            all_symbols_from_indices.extend(index_symbols)

        # Tous les symboles uniques doivent être présents
        expected_symbols = list(dict.fromkeys(all_symbols_from_indices))
        assert symbols == expected_symbols

    @patch(
        "boursa_vision.application.services.investment_recommendation_service.ThreadPoolExecutor"
    )
    def test_analyze_investments_parallel_success(
        self, mock_executor_class, service, mock_analyzer
    ):
        """Test d'analyse parallèle réussie."""
        # Configuration des mocks
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor

        # Mock des futures
        future1 = Mock()
        future1.result.return_value = self._create_mock_analysis("AAPL")
        future2 = Mock()
        future2.result.return_value = self._create_mock_analysis("MSFT")

        mock_executor.submit.side_effect = [future1, future2]

        # Mock de as_completed
        with patch(
            "boursa_vision.application.services.investment_recommendation_service.as_completed"
        ) as mock_as_completed:
            mock_as_completed.return_value = [future1, future2]

            symbols = ["AAPL", "MSFT"]
            analyses = service._analyze_investments_parallel(symbols)

            assert len(analyses) == 2
            assert all(
                isinstance(analysis, ComprehensiveAnalysisResult)
                for analysis in analyses
            )

    def test_analyze_with_cache_new_symbol(self, service):
        """Test d'analyse avec cache pour un nouveau symbole."""
        symbol = "AAPL"

        # Premier appel - doit utiliser l'analyseur
        analysis = service._analyze_with_cache(symbol)

        assert analysis is not None
        assert analysis.investment_symbol == symbol

        # Vérifier que le cache contient maintenant le résultat
        assert len(service._cache) == 1

    def test_analyze_with_cache_cached_symbol(self, service, mock_analyzer):
        """Test d'analyse avec cache pour un symbole déjà en cache."""
        symbol = "AAPL"
        cached_analysis = self._create_mock_analysis(symbol)

        # Mettre en cache manuellement
        import time

        cache_key = f"analysis_{symbol}_{int(time.time() // service._cache_ttl)}"
        service._cache[cache_key] = cached_analysis

        # L'appel doit retourner le résultat en cache
        analysis = service._analyze_with_cache(symbol)

        assert analysis == cached_analysis
        # L'analyseur ne doit pas être appelé
        mock_analyzer.analyze_investment.assert_not_called()

    def test_filter_analyses_by_score(self, service):
        """Test de filtrage par score."""
        analyses = [
            self._create_mock_analysis("AAPL"),  # 75.0
            ComprehensiveAnalysisResult(
                investment_symbol="MSFT",
                overall_score=50.0,  # Sous le minimum
                confidence=0.8,
                risk_level="MODERATE",
                recommendation="HOLD",
                technical_score=50.0,
                fundamental_score=50.0,
                momentum_score=50.0,
                target_price=None,
                stop_loss=None,
                strengths=[],
                weaknesses=[],
                insights=[],
            ),
        ]

        request = RecommendationRequest(min_score=60.0)
        filtered = service._filter_analyses(analyses, request)

        # Seul AAPL doit passer le filtre
        assert len(filtered) == 1
        assert filtered[0].investment_symbol == "AAPL"

    def test_filter_analyses_by_risk_level(self, service):
        """Test de filtrage par niveau de risque."""
        analyses = [
            self._create_mock_analysis("AAPL"),  # MODERATE
            ComprehensiveAnalysisResult(
                investment_symbol="RISKY",
                overall_score=75.0,
                confidence=0.8,
                risk_level="VERY_HIGH",  # Trop risqué
                recommendation="BUY",
                technical_score=75.0,
                fundamental_score=75.0,
                momentum_score=75.0,
                target_price=None,
                stop_loss=None,
                strengths=[],
                weaknesses=[],
                insights=[],
            ),
        ]

        request = RecommendationRequest(max_risk_level="MODERATE")
        filtered = service._filter_analyses(analyses, request)

        # Seul AAPL doit passer le filtre
        assert len(filtered) == 1
        assert filtered[0].investment_symbol == "AAPL"

    def test_filter_analyses_exclude_sell_recommendations(self, service):
        """Test d'exclusion des recommandations SELL."""
        analyses = [
            self._create_mock_analysis("AAPL"),  # BUY
            ComprehensiveAnalysisResult(
                investment_symbol="SELL_STOCK",
                overall_score=75.0,
                confidence=0.8,
                risk_level="MODERATE",
                recommendation="SELL",  # Doit être exclu
                technical_score=75.0,
                fundamental_score=75.0,
                momentum_score=75.0,
                target_price=None,
                stop_loss=None,
                strengths=[],
                weaknesses=[],
                insights=[],
            ),
        ]

        # Avec min_score élevé, SELL doit être exclu
        request = RecommendationRequest(min_score=60.0)
        filtered = service._filter_analyses(analyses, request)

        assert len(filtered) == 1
        assert filtered[0].investment_symbol == "AAPL"

    def test_create_recommendation(self, service):
        """Test de création d'une recommandation."""
        analysis = self._create_mock_analysis("AAPL")
        recommendation = service._create_recommendation(analysis)

        assert isinstance(recommendation, InvestmentRecommendation)
        assert recommendation.symbol == "AAPL"
        assert recommendation.recommendation == "BUY"
        assert abs(recommendation.overall_score - 75.0) < 0.001
        assert abs(recommendation.confidence - 0.8) < 0.001
        assert recommendation.risk_level == "MODERATE"
        assert abs(recommendation.technical_score - 70.0) < 0.001
        assert abs(recommendation.fundamental_score - 80.0) < 0.001
        assert abs(recommendation.momentum_score - 75.0) < 0.001
        assert abs(recommendation.target_price - 180.0) < 0.001
        assert abs(recommendation.stop_loss - 140.0) < 0.001

    def test_calculate_portfolio_metrics_empty(self, service):
        """Test de calcul de métriques pour un portfolio vide."""
        metrics = service._calculate_portfolio_metrics([])
        assert metrics == {}

    def test_calculate_portfolio_metrics_with_recommendations(self, service):
        """Test de calcul de métriques avec recommandations."""
        recommendations = [
            InvestmentRecommendation(
                symbol="AAPL",
                name="Apple Inc.",
                current_price=150.0,
                currency="USD",
                recommendation="STRONG_BUY",
                overall_score=85.0,
                confidence=0.9,
                risk_level="MODERATE",
                technical_score=80.0,
                fundamental_score=85.0,
                momentum_score=90.0,
                data_quality="EXCELLENT",
            ),
            InvestmentRecommendation(
                symbol="MSFT",
                name="Microsoft Corp.",
                current_price=300.0,
                currency="USD",
                recommendation="BUY",
                overall_score=75.0,
                confidence=0.8,
                risk_level="MODERATE",
                technical_score=70.0,
                fundamental_score=75.0,
                momentum_score=80.0,
                data_quality="GOOD",
            ),
        ]

        metrics = service._calculate_portfolio_metrics(recommendations)

        assert metrics["total_recommendations"] == 2
        assert abs(metrics["average_score"] - 80.0) < 0.001  # (85 + 75) / 2
        assert abs(metrics["score_range"]["min"] - 75.0) < 0.001
        assert abs(metrics["score_range"]["max"] - 85.0) < 0.001
        assert abs(metrics["average_confidence"] - 0.85) < 0.001  # (0.9 + 0.8) / 2
        assert metrics["strong_buy_count"] == 1
        assert metrics["buy_count"] == 1
        assert metrics["hold_count"] == 0
        assert metrics["high_quality_count"] == 2

    def test_assess_portfolio_risk_empty(self, service):
        """Test d'évaluation du risque pour un portfolio vide."""
        risk_assessment = service._assess_portfolio_risk([])
        assert risk_assessment == {}

    def test_assess_portfolio_risk_with_recommendations(self, service):
        """Test d'évaluation du risque avec recommandations."""
        recommendations = [
            InvestmentRecommendation(
                symbol="AAPL",
                name="Apple Inc.",
                current_price=150.0,
                currency="USD",
                recommendation="BUY",
                overall_score=85.0,
                confidence=0.9,
                risk_level="MODERATE",
                technical_score=80.0,
                fundamental_score=85.0,
                momentum_score=90.0,
            ),
            InvestmentRecommendation(
                symbol="RISKY",
                name="Risky Stock",
                current_price=50.0,
                currency="USD",
                recommendation="BUY",
                overall_score=70.0,
                confidence=0.7,
                risk_level="HIGH",
                technical_score=65.0,
                fundamental_score=70.0,
                momentum_score=75.0,
            ),
        ]

        risk_assessment = service._assess_portfolio_risk(recommendations)

        assert "risk_distribution" in risk_assessment
        assert risk_assessment["risk_distribution"]["MODERATE"] == 1
        assert risk_assessment["risk_distribution"]["HIGH"] == 1
        assert "average_risk_score" in risk_assessment
        assert (
            abs(risk_assessment["average_risk_score"] - 62.5) < 0.001
        )  # (50 + 75) / 2
        assert "risk_assessment" in risk_assessment
        assert "diversification_score" in risk_assessment

    def test_categorize_portfolio_risk(self, service):
        """Test de catégorisation du risque du portfolio."""
        assert service._categorize_portfolio_risk(15.0) == "VERY_CONSERVATIVE"
        assert service._categorize_portfolio_risk(30.0) == "CONSERVATIVE"
        assert service._categorize_portfolio_risk(45.0) == "MODERATE"
        assert service._categorize_portfolio_risk(60.0) == "AGGRESSIVE"
        assert service._categorize_portfolio_risk(80.0) == "VERY_AGGRESSIVE"

    def test_calculate_sector_allocation(self, service):
        """Test de calcul de répartition sectorielle."""
        recommendations = [
            InvestmentRecommendation(
                symbol="AAPL",
                name="Apple Inc.",
                current_price=150.0,
                currency="USD",
                recommendation="BUY",
                overall_score=85.0,
                confidence=0.9,
                risk_level="MODERATE",
                technical_score=80.0,
                fundamental_score=85.0,
                momentum_score=90.0,
            ),
            InvestmentRecommendation(
                symbol="MSFT",
                name="Microsoft Corp.",
                current_price=300.0,
                currency="USD",
                recommendation="BUY",
                overall_score=75.0,
                confidence=0.8,
                risk_level="MODERATE",
                technical_score=70.0,
                fundamental_score=75.0,
                momentum_score=80.0,
            ),
        ]

        allocation = service._calculate_sector_allocation(recommendations)

        # Les deux sont des actions tech selon la logique du service
        assert "Technology" in allocation
        assert abs(allocation["Technology"] - 100.0) < 0.001

    @patch.object(InvestmentRecommendationService, "_analyze_investments_parallel")
    @patch.object(InvestmentRecommendationService, "_get_symbols_to_analyze")
    def test_get_investment_recommendations_success(
        self, mock_get_symbols, mock_analyze, service
    ):
        """Test de génération de recommandations réussie."""
        # Configuration des mocks
        mock_get_symbols.return_value = ["AAPL", "MSFT"]
        mock_analyze.return_value = [
            self._create_mock_analysis("AAPL"),
            self._create_mock_analysis("MSFT"),
        ]

        request = RecommendationRequest(max_recommendations=2)
        result = service.get_investment_recommendations(request)

        assert isinstance(result, PortfolioRecommendation)
        assert len(result.recommendations) <= 2
        assert "total_recommendations" in result.portfolio_metrics
        assert "total_analyzed" in result.analysis_summary
        assert isinstance(result.risk_assessment, dict)
        assert isinstance(result.sector_allocation, dict)

    @patch.object(InvestmentRecommendationService, "_get_symbols_to_analyze")
    def test_get_investment_recommendations_error_handling(
        self, mock_get_symbols, service
    ):
        """Test de gestion d'erreur lors de la génération."""
        # Faire échouer l'obtention des symboles
        mock_get_symbols.side_effect = Exception("Test error")

        request = RecommendationRequest()
        result = service.get_investment_recommendations(request)

        # Doit retourner un résultat vide avec erreur
        assert isinstance(result, PortfolioRecommendation)
        assert result.recommendations == []
        assert result.portfolio_metrics == {}
        assert "error" in result.analysis_summary
        assert result.risk_assessment == {}
        assert result.sector_allocation == {}

    def test_concurrent_analysis_timeout_handling(self, service, mock_analyzer):
        """Test de gestion du timeout lors de l'analyse concurrente."""
        # Simuler un timeout
        mock_analyzer.analyze_investment.side_effect = Exception("Timeout")

        with patch("builtins.print"):  # Supprimer les prints pendant le test
            analyses = service._analyze_investments_parallel(["AAPL"])

        # Ne doit pas planter et retourner une liste vide
        assert isinstance(analyses, list)

    def test_cache_key_generation_time_based(self, service):
        """Test de génération de clé de cache basée sur le temps."""
        symbol = "AAPL"

        # Analyser le même symbole deux fois dans la même fenêtre de cache
        analysis1 = service._analyze_with_cache(symbol)
        analysis2 = service._analyze_with_cache(symbol)

        # Les deux résultats doivent être identiques (du cache)
        assert analysis1 == analysis2

        # Ne doit y avoir qu'un seul appel à l'analyseur
        assert service.analyzer.analyze_investment.call_count == 1
