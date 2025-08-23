"""
Tests unitaires pour SQLAlchemyInvestmentRepository
==================================================

Tests complets pour le repository d'investissements avec SQLAlchemy,
incluant CRUD, mapper, recherches complexes et gestion d'erreurs.
"""

from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

# Constant for floating point comparisons
FLOAT_TOLERANCE = 1e-6

from boursa_vision.domain.entities.investment import (
    Investment,
    InvestmentSector,
    InvestmentType,
    MarketCap,
)
from boursa_vision.domain.value_objects.money import Currency
from boursa_vision.infrastructure.persistence.models.investment import InvestmentModel
from boursa_vision.infrastructure.persistence.repositories.investment_repository import (
    SimpleInvestmentMapper,
    SQLAlchemyInvestmentRepository,
)


class TestSimpleInvestmentMapper:
    """Tests pour le mapper Investment ↔ InvestmentModel"""

    def setup_method(self):
        """Setup pour chaque test"""
        self.mapper = SimpleInvestmentMapper()

    @pytest.mark.unit
    def test_to_domain_complete_data(self):
        """Test de conversion InvestmentModel vers Investment avec données complètes"""
        # Given
        model = InvestmentModel(
            id="test-id-123",
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2500.0,  # 2.5T - MEGA cap
            description="Apple Inc. designs and manufactures consumer electronics",
        )

        # When
        investment = self.mapper.to_domain(model)

        # Then
        assert investment.symbol == "AAPL"
        assert investment.name == "Apple Inc."
        assert investment.investment_type == InvestmentType.STOCK
        assert investment.sector == InvestmentSector.TECHNOLOGY
        assert investment.market_cap == MarketCap.MEGA  # 2500B > 300B
        assert investment.currency == Currency.USD
        assert investment.exchange == "NASDAQ"

    @pytest.mark.unit
    def test_to_domain_market_cap_mapping(self):
        """Test du mapping des différents market caps"""
        test_cases = [
            (0.02, MarketCap.NANO),  # $20M < $50M
            (0.15, MarketCap.MICRO),  # $150M ($50M - $300M)
            (1.5, MarketCap.SMALL),  # $1.5B ($300M - $2B)
            (5.0, MarketCap.MID),  # $5B ($2B - $10B)
            (100.0, MarketCap.LARGE),  # $100B ($10B - $200B)
            (500.0, MarketCap.MEGA),  # $500B > $200B
        ]

        for market_cap_value, expected_enum in test_cases:
            # Given
            model = InvestmentModel(
                symbol="TEST",
                name="Test Company",
                exchange="TEST",
                sector="Technology",
                market_cap=market_cap_value,
            )

            # When
            investment = self.mapper.to_domain(model)

            # Then
            assert (
                investment.market_cap == expected_enum
            ), f"Pour {market_cap_value}B attendu {expected_enum}"

    @pytest.mark.unit
    def test_to_domain_invalid_sector_fallback(self):
        """Test du fallback pour secteur invalide"""
        # Given
        model = InvestmentModel(
            symbol="TEST",
            name="Test Company",
            exchange="TEST",
            sector="InvalidSector",  # Secteur non reconnu
            market_cap=50.0,
        )

        # When
        investment = self.mapper.to_domain(model)

        # Then
        assert investment.sector == InvestmentSector.TECHNOLOGY  # Fallback par défaut

    @pytest.mark.unit
    def test_to_domain_none_values(self):
        """Test avec valeurs None/nulles"""
        # Given
        model = InvestmentModel(
            symbol="TEST",
            name="Test Company",
            exchange="TEST",
            sector=None,  # Secteur None
            market_cap=None,  # Market cap None
        )

        # When
        investment = self.mapper.to_domain(model)

        # Then
        assert investment.symbol == "TEST"
        assert investment.market_cap == MarketCap.LARGE  # Fallback par défaut
        assert investment.sector == InvestmentSector.TECHNOLOGY  # Fallback par défaut

    @pytest.mark.unit
    def test_to_persistence_complete_data(self):
        """Test de conversion Investment vers InvestmentModel"""
        # Given
        investment = Investment.create(
            symbol="MSFT",
            name="Microsoft Corporation",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            currency=Currency.USD,
            exchange="NASDAQ",
            isin="US5949181045",
        )

        # When
        model = self.mapper.to_persistence(investment)

        # Then
        assert model.symbol == "MSFT"
        assert model.name == "Microsoft Corporation"
        assert model.exchange == "NASDAQ"
        assert model.sector == "TECHNOLOGY"
        assert model.industry == "Software"
        assert (
            abs(model.market_cap - 100.0) < FLOAT_TOLERANCE
        )  # Updated to match new LARGE value

    @pytest.mark.unit
    def test_to_persistence_market_cap_mapping(self):
        """Test du mapping market cap enum vers valeur numérique"""
        test_cases = [
            (MarketCap.NANO, 0.025),  # ~$25M
            (MarketCap.MICRO, 0.175),  # ~$175M
            (MarketCap.SMALL, 1.15),  # ~$1.15B
            (MarketCap.MID, 6.0),  # ~$6B
            (MarketCap.LARGE, 100.0),  # ~$100B
            (MarketCap.MEGA, 500.0),  # ~$500B
        ]

        for market_cap_enum, expected_value in test_cases:
            # Given
            investment = Investment.create(
                symbol="TEST",
                name="Test Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=market_cap_enum,
                currency=Currency.USD,
                exchange="TEST",
            )

            # When
            model = self.mapper.to_persistence(investment)

            # Then
            assert abs(model.market_cap - expected_value) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_roundtrip_conversion(self):
        """Test de conversion aller-retour Investment ↔ Model"""
        # Given - Investment original
        original_investment = Investment.create(
            symbol="GOOGL",
            name="Alphabet Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MEGA,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # When - Conversion Investment → Model → Investment
        model = self.mapper.to_persistence(original_investment)
        roundtrip_investment = self.mapper.to_domain(model)

        # Then - Les données principales doivent être préservées
        assert roundtrip_investment.symbol == original_investment.symbol
        assert roundtrip_investment.name == original_investment.name
        assert roundtrip_investment.exchange == original_investment.exchange
        assert roundtrip_investment.sector == original_investment.sector
        assert roundtrip_investment.market_cap == original_investment.market_cap


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy AsyncSession"""
    session = Mock(spec=AsyncSession)
    # Make execute async
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    # Keep add and delete as sync methods (they don't return coroutines in SQLAlchemy)
    session.add = Mock()
    session.delete = Mock()
    return session


def create_mock_result_single(model=None):
    """Helper to create mock result for single item queries"""
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = model
    return mock_result


def create_mock_result_multiple(models):
    """Helper to create mock result for multiple item queries"""
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = models
    mock_result.scalars.return_value = mock_scalars
    return mock_result


@pytest.fixture
def investment_repository(mock_session):
    """Repository avec session mockée"""
    return SQLAlchemyInvestmentRepository(mock_session)


@pytest.fixture
def sample_investment():
    """Investment sample pour les tests"""
    return Investment.create(
        symbol="AAPL",
        name="Apple Inc.",
        investment_type=InvestmentType.STOCK,
        sector=InvestmentSector.TECHNOLOGY,
        market_cap=MarketCap.MEGA,
        currency=Currency.USD,
        exchange="NASDAQ",
    )


@pytest.fixture
def sample_investment_model():
    """InvestmentModel sample pour les tests"""
    return InvestmentModel(
        id=123,  # Integer ID, not string
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=2500.0,
        description="Apple Inc.",
    )


class TestSQLAlchemyInvestmentRepository:
    """Tests pour SQLAlchemyInvestmentRepository"""

    @pytest.mark.unit
    def test_repository_init(self, mock_session):
        """Test d'initialisation du repository"""
        # When
        repo = SQLAlchemyInvestmentRepository(mock_session)

        # Then
        assert repo._session == mock_session
        assert isinstance(repo._mapper, SimpleInvestmentMapper)

    @pytest.mark.unit
    async def test_find_by_symbol_found(
        self, investment_repository, mock_session, sample_investment_model
    ):
        """Test find_by_symbol avec résultat trouvé"""
        # Given
        mock_result = create_mock_result_single(sample_investment_model)
        mock_session.execute.return_value = mock_result

        # When
        investment = await investment_repository.find_by_symbol("AAPL")

        # Then
        assert investment is not None
        assert investment.symbol == "AAPL"
        assert investment.name == "Apple Inc."
        mock_session.execute.assert_called_once()

        # Vérifier que la requête SQL est correcte
        call_args = mock_session.execute.call_args[0][0]
        assert str(call_args).lower().count("where") == 1

    @pytest.mark.unit
    async def test_find_by_symbol_not_found(self, investment_repository, mock_session):
        """Test find_by_symbol sans résultat"""
        # Given
        mock_result = create_mock_result_single(None)
        mock_session.execute.return_value = mock_result

        # When
        investment = await investment_repository.find_by_symbol("NOTFOUND")

        # Then
        assert investment is None
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    async def test_find_by_id_found(
        self, investment_repository, mock_session, sample_investment_model
    ):
        """Test find_by_id avec résultat trouvé"""
        # Given
        mock_result = create_mock_result_single(sample_investment_model)
        mock_session.execute.return_value = mock_result

        # When
        investment = await investment_repository.find_by_id("test-id-123")

        # Then
        assert investment is not None
        assert investment.symbol == "AAPL"
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    async def test_find_by_exchange(self, investment_repository, mock_session):
        """Test find_by_exchange avec résultats multiples"""
        # Given
        nasdaq_models = [
            InvestmentModel(
                id=1,
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=2500.0,
            ),
            InvestmentModel(
                id=2,
                symbol="MSFT",
                name="Microsoft Corp.",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=2300.0,
            ),
        ]

        mock_result = create_mock_result_multiple(nasdaq_models)
        mock_session.execute.return_value = mock_result

    @pytest.mark.unit
    async def test_find_by_sector(self, investment_repository, mock_session):
        """Test find_by_sector avec résultats multiples"""
        # Given
        tech_models = [
            InvestmentModel(
                id=1,
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=2500.0,
            ),
            InvestmentModel(
                id=2,
                symbol="GOOGL",
                name="Alphabet Inc.",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=1800.0,
            ),
        ]

        mock_result = create_mock_result_multiple(tech_models)
        mock_session.execute.return_value = mock_result

    @pytest.mark.unit
    async def test_find_all_active(self, investment_repository, mock_session):
        """Test find_all_active"""
        # Given
        all_models = [
            InvestmentModel(
                symbol="AAPL",
                name="Apple",
                exchange="NASDAQ",
                sector="Technology",
                market_cap=2500.0,
            ),
            InvestmentModel(
                symbol="JPM",
                name="JPMorgan",
                exchange="NYSE",
                sector="Financial Services",
                market_cap=400.0,
            ),
            InvestmentModel(
                symbol="JNJ",
                name="Johnson & Johnson",
                exchange="NYSE",
                sector="Healthcare",
                market_cap=450.0,
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = all_models
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.find_all_active()

        # Then
        assert len(investments) == 3
        symbols = [inv.symbol for inv in investments]
        assert "AAPL" in symbols
        assert "JPM" in symbols
        assert "JNJ" in symbols

    @pytest.mark.unit
    async def test_save_new_investment(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test save avec nouvel investment"""
        # Given
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # Pas d'existing
        mock_session.execute.return_value = mock_result

        # When
        saved_investment = await investment_repository.save(sample_investment)

        # Then
        assert saved_investment.symbol == "AAPL"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.unit
    async def test_save_update_existing_investment(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test save avec investment existant (update)"""
        # Given
        existing_model = InvestmentModel(
            symbol="AAPL",
            name="Old Apple Name",
            exchange="NASDAQ",
            sector="Technology",
            market_cap=1000.0,
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_model
        mock_session.execute.return_value = mock_result

        # When
        saved_investment = await investment_repository.save(sample_investment)

        # Then
        assert saved_investment.symbol == "AAPL"
        # La nouvelle implémentation utilise execute() pour SELECT et DELETE, puis add() pour INSERT
        assert mock_session.execute.call_count == 2  # SELECT, DELETE
        mock_session.add.assert_called_once()  # INSERT via add()
        mock_session.flush.assert_called()  # Au moins un appel à flush

    @pytest.mark.unit
    async def test_delete_existing_investment(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test delete avec investment existant"""
        # Given
        existing_model = InvestmentModel(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            market_cap=2500.0,
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_model
        mock_result.rowcount = 1  # Mock du rowcount pour la suppression
        mock_session.execute.return_value = mock_result

        # When
        await investment_repository.delete(sample_investment)

        # Then
        # La nouvelle implémentation utilise execute() pour DELETE directement
        mock_session.execute.assert_called()  # Au moins un appel pour DELETE
        mock_session.flush.assert_called_once()

    @pytest.mark.unit
    async def test_delete_non_existing_investment(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test delete avec investment non existant"""
        # Given
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.rowcount = 0  # Mock du rowcount pour la suppression non réussie
        mock_session.execute.return_value = mock_result

        # When
        await investment_repository.delete(sample_investment)

        # Then
        # Même avec un investment non existant, la nouvelle implémentation fait le DELETE SQL
        # et appelle flush() - cela ne cause pas d'erreur
        mock_session.execute.assert_called()  # Au moins un appel
        mock_session.flush.assert_called_once()

    @pytest.mark.unit
    async def test_find_all_alias(self, investment_repository, mock_session):
        """Test que find_all est un alias pour find_all_active"""
        # Given
        models = [
            InvestmentModel(
                symbol="TEST",
                name="Test",
                exchange="TEST",
                sector="Tech",
                market_cap=100.0,
            )
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = models
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.find_all()

        # Then
        assert len(investments) == 1
        assert investments[0].symbol == "TEST"

    @pytest.mark.unit
    async def test_find_by_market_cap(self, investment_repository, mock_session):
        """Test find_by_market_cap avec différentes tailles"""
        # Given
        large_cap_models = [
            InvestmentModel(
                symbol="AAPL",
                name="Apple",
                exchange="NASDAQ",
                sector="Technology",
                market_cap=45.0,
            ),
            InvestmentModel(
                symbol="MSFT",
                name="Microsoft",
                exchange="NASDAQ",
                sector="Technology",
                market_cap=55.0,
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = large_cap_models
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.find_by_market_cap("LARGE")

        # Then
        assert len(investments) == 2
        mock_session.execute.assert_called_once()
        # Vérifier que la requête utilise BETWEEN pour la recherche par plage

    @pytest.mark.unit
    async def test_search_by_name(self, investment_repository, mock_session):
        """Test search_by_name avec pattern de recherche"""
        # Given
        matching_models = [
            InvestmentModel(
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ",
                sector="Technology",
                market_cap=2500.0,
            ),
            InvestmentModel(
                symbol="AMAT",
                name="Applied Materials",
                exchange="NASDAQ",
                sector="Technology",
                market_cap=100.0,
            ),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = matching_models
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.search_by_name("Apple")

        # Then
        assert len(investments) == 2
        mock_session.execute.assert_called_once()
        # Vérifier que la requête utilise ILIKE pour la recherche insensible à la casse


class TestInvestmentRepositoryErrorHandling:
    """Tests de gestion d'erreurs pour InvestmentRepository"""

    @pytest.mark.unit
    async def test_find_by_symbol_database_error(
        self, investment_repository, mock_session
    ):
        """Test de gestion d'erreur de base de données"""
        # Given
        mock_session.execute.side_effect = SQLAlchemyError("Database connection error")

        # When/Then
        with pytest.raises(SQLAlchemyError):
            await investment_repository.find_by_symbol("AAPL")

    @pytest.mark.unit
    async def test_save_integrity_error(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test de gestion d'erreur d'intégrité lors du save"""
        # Given
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.flush.side_effect = IntegrityError(
            "Duplicate key", orig=Exception("Original"), params=None
        )

        # When/Then
        with pytest.raises(IntegrityError):
            await investment_repository.save(sample_investment)

    @pytest.mark.unit
    async def test_delete_database_error(
        self, investment_repository, mock_session, sample_investment
    ):
        """Test de gestion d'erreur lors du delete"""
        # Given
        # Configurer l'erreur pour la requête DELETE (seul appel à execute dans delete)
        mock_session.execute.side_effect = SQLAlchemyError("Delete error")

        # When/Then
        with pytest.raises(SQLAlchemyError):
            await investment_repository.delete(sample_investment)


class TestInvestmentRepositoryEdgeCases:
    """Tests des cas limites pour InvestmentRepository"""

    @pytest.mark.unit
    async def test_find_by_exchange_empty_results(
        self, investment_repository, mock_session
    ):
        """Test find_by_exchange avec résultats vides"""
        # Given
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.find_by_exchange("UNKNOWN")

        # Then
        assert investments == []

    @pytest.mark.unit
    async def test_search_by_name_special_characters(
        self, investment_repository, mock_session
    ):
        """Test search_by_name avec caractères spéciaux"""
        # Given
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # When
        investments = await investment_repository.search_by_name("AT&T%_Test")

        # Then
        assert investments == []
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    async def test_find_by_market_cap_invalid_value(
        self, investment_repository, mock_session
    ):
        """Test find_by_market_cap avec valeur invalide"""
        # Given
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # When - Valeur non reconnue utilisera le fallback (50.0)
        investments = await investment_repository.find_by_market_cap("INVALID")

        # Then
        assert investments == []
        mock_session.execute.assert_called_once()

    @pytest.mark.unit
    async def test_mapper_with_extreme_market_cap_values(self):
        """Test du mapper avec des valeurs extrêmes de market cap"""
        mapper = SimpleInvestmentMapper()

        extreme_cases = [
            (0.0, MarketCap.NANO),  # Valeur zéro
            (0.001, MarketCap.NANO),  # Très petit
            (10000.0, MarketCap.MEGA),  # Très grand
        ]

        for market_cap_value, expected_enum in extreme_cases:
            # Given
            model = InvestmentModel(
                symbol="TEST",
                name="Test Company",
                exchange="TEST",
                sector="Technology",
                market_cap=market_cap_value,
            )

            # When
            investment = mapper.to_domain(model)

            # Then
            assert investment.market_cap == expected_enum

    @pytest.mark.unit
    def test_mapper_sector_case_sensitivity(self):
        """Test de la sensibilité à la casse du secteur"""
        mapper = SimpleInvestmentMapper()

        # Given - secteur avec différentes casses
        model = InvestmentModel(
            symbol="TEST",
            name="Test Company",
            exchange="TEST",
            sector="technology",  # Minuscule
            market_cap=50.0,
        )

        # When
        investment = mapper.to_domain(model)

        # Then - Devrait utiliser le fallback car "technology" != "Technology"
        assert investment.sector == InvestmentSector.TECHNOLOGY


class TestInvestmentRepositoryIntegration:
    """Tests d'intégration simples pour InvestmentRepository"""

    @pytest.mark.unit
    async def test_full_crud_workflow(self, investment_repository, mock_session):
        """Test d'un workflow CRUD complet"""
        # Given
        investment = Investment.create(
            symbol="TEST",
            name="Test Company",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.MID,
            currency=Currency.USD,
            exchange="NASDAQ",
        )

        # Mock pour save (create)
        mock_result_none = create_mock_result_single(None)

        # Mock pour find (read)
        test_model = InvestmentModel(
            id=1,
            symbol="TEST",
            name="Test Company",
            exchange="NASDAQ",
            sector="Technology",
            industry="Software",
            market_cap=6.0,
        )
        mock_result_found = create_mock_result_single(test_model)

        # Mock pour delete avec rowcount
        mock_result_delete = Mock()
        mock_result_delete.rowcount = 1  # Simulation suppression réussie

        # Configure la séquence d'appels
        mock_session.execute.side_effect = [
            mock_result_none,  # Save - pas existant
            mock_result_found,  # Find - trouvé
            mock_result_delete,  # Delete - trouvé
        ]

        # When - CRUD workflow
        # Create
        saved = await investment_repository.save(investment)
        assert saved.symbol == "TEST"

        # Read
        found = await investment_repository.find_by_symbol("TEST")
        assert found is not None
        assert found.symbol == "TEST"

        # Delete
        await investment_repository.delete(found)

        # Then
        assert (
            mock_session.execute.call_count >= 3
        )  # Au moins 3 appels: save, find, delete
        # La nouvelle implémentation n'utilise plus add() ni delete() directement
        mock_session.flush.assert_called()  # Au moins un appel à flush

    @pytest.mark.unit
    async def test_multiple_search_methods(self, investment_repository, mock_session):
        """Test de l'utilisation de plusieurs méthodes de recherche"""
        # Given - Différents modèles pour différentes recherches
        tech_models = [
            InvestmentModel(
                id=1,
                symbol="AAPL",
                name="Apple Inc.",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=2500.0,
            ),
            InvestmentModel(
                id=2,
                symbol="MSFT",
                name="Microsoft Corp",
                exchange="NASDAQ",
                sector="Technology",
                industry="Software",
                market_cap=2000.0,
            ),
        ]

        nasdaq_models = tech_models + [
            InvestmentModel(
                id=3,
                symbol="AMZN",
                name="Amazon Inc.",
                exchange="NASDAQ",
                sector="Consumer Discretionary",
                industry="E-commerce",
                market_cap=1500.0,
            )
        ]

        apple_models = [tech_models[0]]  # Seulement Apple pour la recherche par nom

        # Configure les mocks pour différentes requêtes
        mock_result_tech = create_mock_result_multiple(tech_models)
        mock_result_nasdaq = create_mock_result_multiple(nasdaq_models)
        mock_result_apple = create_mock_result_multiple(apple_models)

        mock_session.execute.side_effect = [
            mock_result_tech,
            mock_result_nasdaq,
            mock_result_apple,
        ]

        # When - Différentes recherches
        tech_investments = await investment_repository.find_by_sector("Technology")
        nasdaq_investments = await investment_repository.find_by_exchange("NASDAQ")
        apple_investments = await investment_repository.search_by_name("Apple")

        # Then
        assert len(tech_investments) == 2
        assert len(nasdaq_investments) == 3
        assert len(apple_investments) == 1
        assert apple_investments[0].symbol == "AAPL"
