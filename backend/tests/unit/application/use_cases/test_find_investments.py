"""
Tests unitaires pour FindInvestmentsUseCase
==========================================

Tests unitaires pour le use case de recherche d'investissements.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from boursa_vision.application.use_cases.find_investments import FindInvestmentsUseCase
from boursa_vision.application.queries.investment.find_investments_query import FindInvestmentsQuery
from boursa_vision.application.dtos import InvestmentSearchResultDTO
from boursa_vision.domain.entities.investment import (
    Investment,
    InvestmentType,
    InvestmentSector,
    MarketCap,
)
from boursa_vision.domain.value_objects.money import Money, Currency


class TestFindInvestmentsQuery:
    """Tests pour FindInvestmentsQuery."""

    def test_query_creation_with_default_values(self):
        """Test de création d'une query avec valeurs par défaut."""
        query = FindInvestmentsQuery()

        assert query.sectors is None
        assert query.investment_types is None
        assert query.market_caps is None
        assert query.currency is None
        assert query.min_price is None
        assert query.max_price is None
        assert query.search_term is None
        assert query.limit == 50
        assert query.offset == 0

    def test_query_creation_with_all_parameters(self):
        """Test de création d'une query avec tous les paramètres."""
        query = FindInvestmentsQuery(
            sectors=["TECHNOLOGY", "HEALTHCARE"],
            investment_types=["STOCK", "ETF"],
            market_caps=["LARGE", "MID"],
            currency="USD",
            min_price=100.0,
            max_price=200.0,
            search_term="Apple",
            limit=25,
            offset=50
        )

        assert query.sectors == ["TECHNOLOGY", "HEALTHCARE"]
        assert query.investment_types == ["STOCK", "ETF"]
        assert query.market_caps == ["LARGE", "MID"]
        assert query.currency == "USD"
        assert query.min_price == 100.0
        assert query.max_price == 200.0
        assert query.search_term == "Apple"
        assert query.limit == 25
        assert query.offset == 50


@pytest.mark.unit
@pytest.mark.asyncio
class TestFindInvestmentsUseCase:
    """Tests pour FindInvestmentsUseCase."""

    async def test_execute_with_no_results(self):
        """Test d'exécution sans résultats."""
        # Arrange
        mock_investment_repository = AsyncMock()
        mock_investment_repository.find_by_criteria.return_value = []
        mock_investment_repository.count_by_criteria.return_value = 0

        mock_technical_analyzer = AsyncMock()
        mock_technical_analyzer.analyze_multiple_investments.return_value = {}

        mock_signal_generator = AsyncMock()
        mock_signal_generator.generate_signals_for_portfolio.return_value = {}

        use_case = FindInvestmentsUseCase(
            investment_repository=mock_investment_repository,
            technical_analyzer=mock_technical_analyzer,
            signal_generator=mock_signal_generator
        )

        query = FindInvestmentsQuery()

        # Act
        result = await use_case.execute(query)

        # Assert
        assert isinstance(result, InvestmentSearchResultDTO)
        assert result.total_count == 0
        assert len(result.investments) == 0
        assert len(result.signals) == 0
        assert len(result.technical_analysis) == 0

    async def test_execute_with_results(self):
        """Test d'exécution avec des résultats."""
        # Arrange
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD,
            current_price=Money(Decimal("150.00"), Currency.USD)
        )

        mock_investment_repository = AsyncMock()
        mock_investment_repository.find_by_criteria.return_value = [investment]
        mock_investment_repository.count_by_criteria.return_value = 1

        mock_technical_analyzer = AsyncMock()
        mock_technical_analyzer.analyze_multiple_investments.return_value = {}

        mock_signal_generator = AsyncMock()
        mock_signal_generator.generate_signals_for_portfolio.return_value = {}

        use_case = FindInvestmentsUseCase(
            investment_repository=mock_investment_repository,
            technical_analyzer=mock_technical_analyzer,
            signal_generator=mock_signal_generator
        )

        query = FindInvestmentsQuery(sectors=["TECHNOLOGY"])

        # Act
        result = await use_case.execute(query)

        # Assert
        assert isinstance(result, InvestmentSearchResultDTO)
        assert result.total_count == 1
        assert len(result.investments) == 1
        assert result.investments[0].symbol == "AAPL"
        assert result.investments[0].name == "Apple Inc."

    async def test_repository_called_with_correct_criteria(self):
        """Test que le repository est appelé avec les bons critères."""
        # Arrange
        mock_investment_repository = AsyncMock()
        mock_investment_repository.find_by_criteria.return_value = []
        mock_investment_repository.count_by_criteria.return_value = 0

        mock_technical_analyzer = AsyncMock()
        mock_technical_analyzer.analyze_multiple_investments.return_value = {}

        mock_signal_generator = AsyncMock()
        mock_signal_generator.generate_signals_for_portfolio.return_value = {}

        use_case = FindInvestmentsUseCase(
            investment_repository=mock_investment_repository,
            technical_analyzer=mock_technical_analyzer,
            signal_generator=mock_signal_generator
        )

        query = FindInvestmentsQuery(
            sectors=["TECHNOLOGY"],
            search_term="Apple",
            min_price=100.0,
            max_price=200.0
        )

        # Act
        await use_case.execute(query)

        # Assert
        mock_investment_repository.find_by_criteria.assert_called_once()
        call_args = mock_investment_repository.find_by_criteria.call_args

        # Vérifier les critères passés
        criteria = call_args.kwargs['criteria']
        assert criteria['sectors'] == ["TECHNOLOGY"]
        assert criteria['search_term'] == "Apple"
        assert criteria['price_range'] == (100.0, 200.0)

        # Vérifier les paramètres de pagination
        assert call_args.kwargs['limit'] == 50
        assert call_args.kwargs['offset'] == 0
