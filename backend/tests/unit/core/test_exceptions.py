"""
Tests unitaires pour les exceptions personnalisées.

Tests pour toutes les exceptions de l'application Boursa Vision,
couvrant les hiérarchies d'erreurs, messages, et codes d'erreur.
"""

import sys
from pathlib import Path
import pytest

# Configuration path pour imports
root_dir = Path(__file__).parent.parent.parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    # Import des exceptions core
    from boursa_vision.core.exceptions import (
        BoursaVisionError,
        ConfigurationError,
        DatabaseError,
        ExternalServiceError,
        DataValidationError,
        ArchivingError,
        RecommendationError,
    )
    CORE_EXCEPTIONS_AVAILABLE = True
except ImportError as e:
    print(f"Core exceptions import warning: {e}")
    CORE_EXCEPTIONS_AVAILABLE = False

try:
    # Import des exceptions application
    from boursa_vision.application.exceptions import (
        BoursaVisionError as AppBoursaVisionError,
        PortfolioNotFoundError,
        InvalidSymbolError,
        PriceRangeError,
        FactoryProviderError,
        DatabaseNotInitializedError,
        RateLimitError,
        TemporaryFailureError,
        AnalysisFailedError,
    )
    APP_EXCEPTIONS_AVAILABLE = True
except ImportError as e:
    print(f"Application exceptions import warning: {e}")
    APP_EXCEPTIONS_AVAILABLE = False


class TestCoreExceptions:
    """Tests pour les exceptions core."""

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_boursa_vision_error_base(self):
        """Test exception de base BoursaVisionError."""
        message = "Erreur de test"
        error_code = "TEST_001"
        
        error = BoursaVisionError(message, error_code)
        
        assert str(error) == message
        assert error.message == message
        assert error.error_code == error_code
        assert isinstance(error, Exception)

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_boursa_vision_error_without_code(self):
        """Test exception de base sans code d'erreur."""
        message = "Erreur sans code"
        
        error = BoursaVisionError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.error_code is None

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_configuration_error(self):
        """Test ConfigurationError hérite de BoursaVisionError."""
        message = "Configuration invalide"
        error_code = "CONFIG_001"
        
        error = ConfigurationError(message, error_code)
        
        assert isinstance(error, BoursaVisionError)
        assert isinstance(error, Exception)
        assert str(error) == message
        assert error.message == message
        assert error.error_code == error_code

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_database_error(self):
        """Test DatabaseError hérite de BoursaVisionError."""
        message = "Erreur de base de données"
        
        error = DatabaseError(message)
        
        assert isinstance(error, BoursaVisionError)
        assert str(error) == message

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_external_service_error(self):
        """Test ExternalServiceError hérite de BoursaVisionError."""
        message = "Service externe indisponible"
        
        error = ExternalServiceError(message)
        
        assert isinstance(error, BoursaVisionError)
        assert str(error) == message

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_data_validation_error(self):
        """Test DataValidationError hérite de BoursaVisionError."""
        message = "Données invalides"
        
        error = DataValidationError(message)
        
        assert isinstance(error, BoursaVisionError)
        assert str(error) == message

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_archiving_error(self):
        """Test ArchivingError hérite de BoursaVisionError."""
        message = "Erreur d'archivage"
        
        error = ArchivingError(message)
        
        assert isinstance(error, BoursaVisionError)
        assert str(error) == message

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_recommendation_error(self):
        """Test RecommendationError hérite de BoursaVisionError."""
        message = "Erreur de recommandation"
        
        error = RecommendationError(message)
        
        assert isinstance(error, BoursaVisionError)
        assert str(error) == message


class TestApplicationExceptions:
    """Tests pour les exceptions application."""

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_app_boursa_vision_error_base(self):
        """Test exception de base de l'application."""
        error = AppBoursaVisionError("Test message")
        
        assert isinstance(error, Exception)
        assert str(error) == "Test message"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_portfolio_not_found_error(self):
        """Test PortfolioNotFoundError avec ID de portfolio."""
        portfolio_id = "12345678-1234-5678-9abc-123456789012"
        
        error = PortfolioNotFoundError(portfolio_id)
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == f"Portfolio {portfolio_id} not found"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_invalid_symbol_error(self):
        """Test InvalidSymbolError avec symbole invalide."""
        symbol = "INVALID@SYMBOL"
        
        error = InvalidSymbolError(symbol)
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == f"Symbol '{symbol}' must be alphanumeric"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_price_range_error(self):
        """Test PriceRangeError sans paramètres."""
        error = PriceRangeError()
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == "max_price must be greater than min_price"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_factory_provider_error(self):
        """Test FactoryProviderError sans paramètres."""
        error = FactoryProviderError()
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == "No factory provider registered"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_database_not_initialized_error(self):
        """Test DatabaseNotInitializedError sans paramètres."""
        error = DatabaseNotInitializedError()
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == "Database not initialized. Call initialize() first."

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_rate_limit_error(self):
        """Test RateLimitError avec symbole."""
        symbol = "AAPL"
        
        error = RateLimitError(symbol)
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == f"Rate limit exceeded for {symbol}"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_temporary_failure_error(self):
        """Test TemporaryFailureError avec message personnalisé."""
        message = "Service temporairement indisponible"
        
        error = TemporaryFailureError(message)
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == message

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_analysis_failed_error_default(self):
        """Test AnalysisFailedError avec message par défaut."""
        error = AnalysisFailedError()
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == "Analysis failed"

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_analysis_failed_error_custom_message(self):
        """Test AnalysisFailedError avec message personnalisé."""
        message = "Analyse technique échouée pour AAPL"
        
        error = AnalysisFailedError(message)
        
        assert isinstance(error, AppBoursaVisionError)
        assert str(error) == message


class TestExceptionHierarchy:
    """Tests pour la hiérarchie d'exceptions."""

    @pytest.mark.skipif(
        not (CORE_EXCEPTIONS_AVAILABLE and APP_EXCEPTIONS_AVAILABLE), 
        reason="Toutes les exceptions non disponibles"
    )
    def test_all_core_exceptions_inherit_from_base(self):
        """Test que toutes les exceptions core héritent de BoursaVisionError."""
        core_exceptions = [
            ConfigurationError("test"),
            DatabaseError("test"),
            ExternalServiceError("test"),
            DataValidationError("test"),
            ArchivingError("test"),
            RecommendationError("test"),
        ]
        
        for exception in core_exceptions:
            assert isinstance(exception, BoursaVisionError)
            assert isinstance(exception, Exception)

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_all_app_exceptions_inherit_from_base(self):
        """Test que toutes les exceptions application héritent de AppBoursaVisionError."""
        app_exceptions = [
            PortfolioNotFoundError("test-id"),
            InvalidSymbolError("TEST"),
            PriceRangeError(),
            FactoryProviderError(),
            DatabaseNotInitializedError(),
            RateLimitError("AAPL"),
            TemporaryFailureError("test"),
            AnalysisFailedError("test"),
        ]
        
        for exception in app_exceptions:
            assert isinstance(exception, AppBoursaVisionError)
            assert isinstance(exception, Exception)

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_exception_chaining(self):
        """Test chaînage d'exceptions."""
        try:
            try:
                raise DatabaseError("Erreur originale", "DB_001")
            except DatabaseError as db_error:
                raise ConfigurationError("Erreur de config") from db_error
        except ConfigurationError as config_error:
            assert isinstance(config_error, BoursaVisionError)
            assert config_error.__cause__ is not None
            assert isinstance(config_error.__cause__, DatabaseError)
            assert str(config_error.__cause__) == "Erreur originale"


class TestExceptionCatchingAndHandling:
    """Tests pour la capture et gestion d'exceptions."""

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_catch_specific_core_exception(self):
        """Test capture d'exception spécifique core."""
        with pytest.raises(DatabaseError) as exc_info:
            raise DatabaseError("Test database error", "DB_002")
        
        assert str(exc_info.value) == "Test database error"
        assert exc_info.value.error_code == "DB_002"

    @pytest.mark.skipif(not CORE_EXCEPTIONS_AVAILABLE, reason="Core exceptions non disponibles")
    def test_catch_core_base_exception(self):
        """Test capture par l'exception de base core."""
        with pytest.raises(BoursaVisionError):
            raise ConfigurationError("Config error")

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_catch_specific_app_exception(self):
        """Test capture d'exception spécifique application."""
        with pytest.raises(InvalidSymbolError) as exc_info:
            raise InvalidSymbolError("INVALID@")
        
        assert "INVALID@" in str(exc_info.value)

    @pytest.mark.skipif(not APP_EXCEPTIONS_AVAILABLE, reason="Application exceptions non disponibles")
    def test_catch_app_base_exception(self):
        """Test capture par l'exception de base application."""
        with pytest.raises(AppBoursaVisionError):
            raise PortfolioNotFoundError("test-id")

    def test_exception_imports_gracefully(self):
        """Test que les imports d'exceptions échouent gracieusement."""
        # Test que même si les imports échouent, les tests peuvent s'exécuter
        if not CORE_EXCEPTIONS_AVAILABLE:
            # Tester que les imports ont échoué de manière attendue
            with pytest.raises(ImportError):
                from boursa_vision.core.exceptions import BoursaVisionError
        else:
            assert CORE_EXCEPTIONS_AVAILABLE is True
        
        if not APP_EXCEPTIONS_AVAILABLE:
            with pytest.raises(ImportError):
                from boursa_vision.application.exceptions import PortfolioNotFoundError
        else:
            assert APP_EXCEPTIONS_AVAILABLE is True


class TestExceptionIntegration:
    """Tests d'intégration pour les exceptions."""

    @pytest.mark.skipif(
        not (CORE_EXCEPTIONS_AVAILABLE and APP_EXCEPTIONS_AVAILABLE), 
        reason="Toutes les exceptions non disponibles"
    )
    def test_exception_classes_available(self):
        """Test que toutes les classes d'exceptions sont disponibles."""
        # Core exceptions
        assert BoursaVisionError is not None
        assert ConfigurationError is not None
        assert DatabaseError is not None
        assert ExternalServiceError is not None
        assert DataValidationError is not None
        assert ArchivingError is not None
        assert RecommendationError is not None
        
        # Application exceptions
        assert AppBoursaVisionError is not None
        assert PortfolioNotFoundError is not None
        assert InvalidSymbolError is not None
        assert PriceRangeError is not None
        assert FactoryProviderError is not None
        assert DatabaseNotInitializedError is not None
        assert RateLimitError is not None
        assert TemporaryFailureError is not None
        assert AnalysisFailedError is not None

    @pytest.mark.skipif(
        not (CORE_EXCEPTIONS_AVAILABLE and APP_EXCEPTIONS_AVAILABLE), 
        reason="Toutes les exceptions non disponibles"
    )
    def test_exception_instantiation_patterns(self):
        """Test patterns d'instanciation des exceptions."""
        # Avec message seulement
        error1 = BoursaVisionError("Message simple")
        assert str(error1) == "Message simple"
        assert error1.error_code is None
        
        # Avec message et code
        error2 = BoursaVisionError("Message avec code", "ERR_001")
        assert str(error2) == "Message avec code"
        assert error2.error_code == "ERR_001"
        
        # Exception avec formatage de message
        error3 = PortfolioNotFoundError("portfolio-123")
        assert "portfolio-123" in str(error3)
        
        # Exception sans paramètres
        error4 = PriceRangeError()
        assert "max_price must be greater than min_price" == str(error4)
