"""
Tests unitaires pour AlertProcessor
===================================

Tests unitaires complets pour le service de gestion des alertes du domaine.
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4, UUID

from boursa_vision.domain.services.alert_service import (
    AlertProcessor,
    AlertNotificationMethod,
)
from boursa_vision.domain.entities.market_data import MarketData
from boursa_vision.domain.value_objects.alert import (
    Alert,
    AlertCondition,
    AlertType,
    AlertPriority,
)


@pytest.fixture
def alert_processor():
    """Instance d'AlertProcessor pour les tests."""
    return AlertProcessor()


@pytest.fixture
def sample_market_data():
    """Données de marché échantillons."""
    return MarketData(
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        open_price=Decimal("150.00"),
        high_price=Decimal("155.00"),
        low_price=Decimal("148.00"),
        close_price=Decimal("152.50"),
        volume=1000000,
        adjusted_close=Decimal("152.50")
    )


@pytest.fixture
def sample_alert():
    """Alerte échantillon pour les tests."""
    alert = Mock(spec=Alert)
    alert.id = uuid4()
    alert.user_id = uuid4()
    alert.symbol = "AAPL"
    alert.alert_type = AlertType.PRICE_ABOVE
    alert.condition = AlertCondition.GREATER_THAN
    alert.target_value = Decimal("150.00")
    alert.is_active = True
    alert.priority = AlertPriority.MEDIUM
    alert.created_at = datetime.now(timezone.utc)
    alert.min_value = None
    alert.max_value = None
    
    # Mock methods
    alert.should_trigger.return_value = True
    alert.trigger.return_value = alert
    
    return alert


@pytest.fixture
def sample_volume_alert():
    """Alerte de volume échantillon."""
    alert = Mock(spec=Alert)
    alert.id = uuid4()
    alert.user_id = uuid4()
    alert.symbol = "AAPL"
    alert.alert_type = AlertType.VOLUME_SPIKE
    alert.condition = AlertCondition.GREATER_THAN
    alert.target_value = Decimal("2.0")  # 2x volume multiplier
    alert.is_active = True
    alert.priority = AlertPriority.HIGH
    alert.should_trigger.return_value = True
    alert.trigger.return_value = alert
    return alert


@pytest.fixture
def sample_percentage_alert():
    """Alerte de pourcentage échantillon."""
    alert = Mock(spec=Alert)
    alert.id = uuid4()
    alert.user_id = uuid4()
    alert.symbol = "AAPL"
    alert.alert_type = AlertType.PRICE_CHANGE_PERCENT
    alert.condition = AlertCondition.GREATER_THAN
    alert.target_value = Decimal("5.0")  # 5% change
    alert.is_active = True
    alert.priority = AlertPriority.MEDIUM
    alert.should_trigger.return_value = True
    alert.trigger.return_value = alert
    return alert


class TestAlertProcessorCreation:
    """Tests pour la création du processeur d'alertes."""

    def test_should_create_alert_processor(self):
        """Test la création du processeur d'alertes."""
        # Act
        processor = AlertProcessor()
        
        # Assert
        assert isinstance(processor, AlertProcessor)
        assert AlertNotificationMethod.IN_APP in processor._notification_methods
        assert AlertNotificationMethod.EMAIL in processor._notification_methods


class TestAlertProcessorMarketDataAlerts:
    """Tests pour le traitement des alertes de données de marché."""

    def test_should_process_market_data_alerts_successfully(
        self, alert_processor, sample_market_data, sample_alert
    ):
        """Test le traitement réussi des alertes de données de marché."""
        # Arrange
        active_alerts = [sample_alert]
        
        # Act
        triggered_alerts = alert_processor.process_market_data_alerts(
            sample_market_data, active_alerts
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0] == sample_alert
        sample_alert.trigger.assert_called_once_with(
            sample_market_data.close_price, sample_market_data.timestamp
        )

    def test_should_filter_alerts_by_symbol(
        self, alert_processor, sample_market_data, sample_alert
    ):
        """Test le filtrage des alertes par symbole."""
        # Arrange
        different_symbol_alert = Mock(spec=Alert)
        different_symbol_alert.symbol = "GOOGL"
        different_symbol_alert.is_active = True
        
        active_alerts = [sample_alert, different_symbol_alert]
        
        # Act
        triggered_alerts = alert_processor.process_market_data_alerts(
            sample_market_data, active_alerts
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0] == sample_alert

    def test_should_handle_empty_alerts_list(
        self, alert_processor, sample_market_data
    ):
        """Test la gestion d'une liste d'alertes vide."""
        # Arrange
        active_alerts = []
        
        # Act
        triggered_alerts = alert_processor.process_market_data_alerts(
            sample_market_data, active_alerts
        )
        
        # Assert
        assert len(triggered_alerts) == 0

    def test_should_skip_inactive_alerts(
        self, alert_processor, sample_market_data, sample_alert
    ):
        """Test l'ignorance des alertes inactives."""
        # Arrange
        sample_alert.is_active = False
        active_alerts = [sample_alert]
        
        # Act
        triggered_alerts = alert_processor.process_market_data_alerts(
            sample_market_data, active_alerts
        )
        
        # Assert
        assert len(triggered_alerts) == 0

    def test_should_handle_case_insensitive_symbols(
        self, alert_processor, sample_market_data, sample_alert
    ):
        """Test la gestion des symboles insensibles à la casse."""
        # Arrange
        sample_alert.symbol = "aapl"  # Minuscule
        active_alerts = [sample_alert]
        
        # Act
        triggered_alerts = alert_processor.process_market_data_alerts(
            sample_market_data, active_alerts
        )
        
        # Assert
        assert len(triggered_alerts) == 1


class TestAlertProcessorVolumeAlerts:
    """Tests pour le traitement des alertes de volume."""

    def test_should_process_volume_alerts_successfully(
        self, alert_processor, sample_market_data, sample_volume_alert
    ):
        """Test le traitement réussi des alertes de volume."""
        # Arrange
        active_alerts = [sample_volume_alert]
        average_volume = 500000  # Volume moyen
        
        # Act
        triggered_alerts = alert_processor.process_volume_alerts(
            sample_market_data, active_alerts, average_volume
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        volume_multiplier = Decimal(sample_market_data.volume) / Decimal(average_volume)
        sample_volume_alert.trigger.assert_called_once_with(
            volume_multiplier, sample_market_data.timestamp
        )

    def test_should_handle_zero_average_volume(
        self, alert_processor, sample_market_data, sample_volume_alert
    ):
        """Test la gestion d'un volume moyen nul."""
        # Arrange
        active_alerts = [sample_volume_alert]
        average_volume = 0
        sample_volume_alert.should_trigger.return_value = False  # Ne devrait pas déclencher
        
        # Act
        triggered_alerts = alert_processor.process_volume_alerts(
            sample_market_data, active_alerts, average_volume
        )
        
        # Assert
        sample_volume_alert.should_trigger.assert_called_once_with(Decimal("0"))
        assert len(triggered_alerts) == 0

    def test_should_filter_volume_alerts_only(
        self, alert_processor, sample_market_data, sample_alert, sample_volume_alert
    ):
        """Test le filtrage des alertes de volume seulement."""
        # Arrange
        active_alerts = [sample_alert, sample_volume_alert]  # Mélange d'alertes
        average_volume = 500000
        
        # Act
        triggered_alerts = alert_processor.process_volume_alerts(
            sample_market_data, active_alerts, average_volume
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        assert triggered_alerts[0] == sample_volume_alert


class TestAlertProcessorPercentageChangeAlerts:
    """Tests pour le traitement des alertes de changement de pourcentage."""

    def test_should_process_percentage_change_alerts_successfully(
        self, alert_processor, sample_market_data, sample_percentage_alert
    ):
        """Test le traitement réussi des alertes de changement de pourcentage."""
        # Arrange
        active_alerts = [sample_percentage_alert]
        previous_close = Decimal("145.00")  # Prix de clôture précédent
        
        # Act
        triggered_alerts = alert_processor.process_percentage_change_alerts(
            sample_market_data, active_alerts, previous_close
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        expected_percentage = (
            (sample_market_data.close_price - previous_close) / previous_close
        ) * Decimal("100")
        sample_percentage_alert.trigger.assert_called_once_with(
            expected_percentage, sample_market_data.timestamp
        )

    def test_should_handle_zero_previous_close(
        self, alert_processor, sample_market_data, sample_percentage_alert
    ):
        """Test la gestion d'un prix de clôture précédent nul."""
        # Arrange
        active_alerts = [sample_percentage_alert]
        previous_close = Decimal("0")
        
        # Act
        triggered_alerts = alert_processor.process_percentage_change_alerts(
            sample_market_data, active_alerts, previous_close
        )
        
        # Assert
        assert len(triggered_alerts) == 0

    def test_should_handle_negative_previous_close(
        self, alert_processor, sample_market_data, sample_percentage_alert
    ):
        """Test la gestion d'un prix de clôture précédent négatif."""
        # Arrange
        active_alerts = [sample_percentage_alert]
        previous_close = Decimal("-10.00")
        
        # Act
        triggered_alerts = alert_processor.process_percentage_change_alerts(
            sample_market_data, active_alerts, previous_close
        )
        
        # Assert
        assert len(triggered_alerts) == 0

    def test_should_use_absolute_value_for_percentage_change(
        self, alert_processor, sample_market_data, sample_percentage_alert
    ):
        """Test l'utilisation de la valeur absolue pour le changement de pourcentage."""
        # Arrange
        active_alerts = [sample_percentage_alert]
        previous_close = Decimal("160.00")  # Prix plus élevé pour changement négatif
        
        # Act
        triggered_alerts = alert_processor.process_percentage_change_alerts(
            sample_market_data, active_alerts, previous_close
        )
        
        # Assert
        assert len(triggered_alerts) == 1
        expected_percentage = (
            (sample_market_data.close_price - previous_close) / previous_close
        ) * Decimal("100")
        sample_percentage_alert.should_trigger.assert_called_once_with(
            abs(expected_percentage)
        )


class TestAlertProcessorValidation:
    """Tests pour la validation des alertes."""

    def test_should_validate_alert_creation_successfully(self, alert_processor, sample_alert):
        """Test la validation réussie de création d'alerte."""
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert errors == []

    def test_should_detect_missing_symbol(self, alert_processor, sample_alert):
        """Test la détection d'un symbole manquant."""
        # Arrange
        sample_alert.symbol = ""
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert "Symbol is required" in errors

    def test_should_detect_invalid_target_value(self, alert_processor, sample_alert):
        """Test la détection d'une valeur cible invalide."""
        # Arrange
        sample_alert.target_value = Decimal("-10.00")
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert "Target value must be positive" in errors

    def test_should_validate_between_condition(self, alert_processor, sample_alert):
        """Test la validation de la condition BETWEEN."""
        # Arrange
        sample_alert.condition = AlertCondition.BETWEEN
        sample_alert.min_value = None
        sample_alert.max_value = Decimal("200.00")
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert any("requires both min_value and max_value" in error for error in errors)

    def test_should_validate_min_max_order(self, alert_processor, sample_alert):
        """Test la validation de l'ordre min/max."""
        # Arrange
        sample_alert.condition = AlertCondition.BETWEEN
        sample_alert.min_value = Decimal("200.00")
        sample_alert.max_value = Decimal("100.00")  # Max < Min
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert "min_value must be less than max_value" in errors

    def test_should_validate_percentage_change_limit(self, alert_processor, sample_alert):
        """Test la validation de la limite de changement de pourcentage."""
        # Arrange
        sample_alert.alert_type = AlertType.PRICE_CHANGE_PERCENT
        sample_alert.target_value = Decimal("150.00")  # > 100%
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert "Percentage change cannot exceed 100%" in errors

    def test_should_validate_volume_spike_minimum(self, alert_processor, sample_alert):
        """Test la validation du minimum pour le pic de volume."""
        # Arrange
        sample_alert.alert_type = AlertType.VOLUME_SPIKE
        sample_alert.target_value = Decimal("0.5")  # < 1.0
        
        # Act
        errors = alert_processor.validate_alert_creation(sample_alert)
        
        # Assert
        assert "Volume spike multiplier must be at least 1.0" in errors


class TestAlertProcessorPriorityScore:
    """Tests pour le calcul du score de priorité."""

    def test_should_calculate_priority_score_with_defaults(
        self, alert_processor, sample_alert
    ):
        """Test le calcul du score de priorité avec valeurs par défaut."""
        # Arrange
        current_value = Decimal("152.00")
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value
        )
        
        # Assert
        assert isinstance(score, Decimal)
        assert score > 0

    def test_should_calculate_priority_score_with_volatility(
        self, alert_processor, sample_alert
    ):
        """Test le calcul avec volatilité."""
        # Arrange
        current_value = Decimal("152.00")
        market_volatility = Decimal("10.0")  # 10% volatilité
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value, market_volatility
        )
        
        # Assert
        assert isinstance(score, Decimal)
        assert score > 0

    def test_should_handle_high_volatility_cap(self, alert_processor, sample_alert):
        """Test la gestion du plafond de volatilité élevée."""
        # Arrange
        current_value = Decimal("152.00")
        market_volatility = Decimal("50.0")  # 50% volatilité (très élevée)
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value, market_volatility
        )
        
        # Assert
        assert isinstance(score, Decimal)
        assert score > 0

    def test_should_calculate_distance_factor(self, alert_processor, sample_alert):
        """Test le calcul du facteur de distance."""
        # Arrange
        current_value = sample_alert.target_value  # Exactement sur la cible
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value
        )
        
        # Assert
        assert isinstance(score, Decimal)
        # Le score devrait inclure le bonus de distance (distance = 0)


class TestAlertProcessorGrouping:
    """Tests pour le regroupement des alertes."""

    def test_should_group_alerts_by_symbol(self, alert_processor, sample_alert):
        """Test le regroupement des alertes par symbole."""
        # Arrange
        alert1 = sample_alert
        alert2 = Mock(spec=Alert)
        alert2.symbol = "GOOGL"
        alert3 = Mock(spec=Alert)
        alert3.symbol = "AAPL"
        
        alerts = [alert1, alert2, alert3]
        
        # Act
        grouped = alert_processor.group_alerts_by_symbol(alerts)
        
        # Assert
        assert "AAPL" in grouped
        assert "GOOGL" in grouped
        assert len(grouped["AAPL"]) == 2
        assert len(grouped["GOOGL"]) == 1

    def test_should_handle_empty_alerts_list_for_grouping(self, alert_processor):
        """Test la gestion d'une liste vide pour le regroupement."""
        # Arrange
        alerts = []
        
        # Act
        grouped = alert_processor.group_alerts_by_symbol(alerts)
        
        # Assert
        assert grouped == {}

    def test_should_handle_case_insensitive_grouping(
        self, alert_processor, sample_alert
    ):
        """Test le regroupement insensible à la casse."""
        # Arrange
        alert1 = sample_alert  # AAPL
        alert2 = Mock(spec=Alert)
        alert2.symbol = "aapl"  # Minuscule
        
        alerts = [alert1, alert2]
        
        # Act
        grouped = alert_processor.group_alerts_by_symbol(alerts)
        
        # Assert
        assert "AAPL" in grouped
        assert len(grouped["AAPL"]) == 2


class TestAlertProcessorDuplicateFiltering:
    """Tests pour le filtrage des doublons."""

    def test_should_detect_duplicate_alert(self, alert_processor, sample_alert):
        """Test la détection d'alertes en double."""
        # Arrange
        user_id = sample_alert.user_id
        new_alert = Mock(spec=Alert)
        new_alert.symbol = sample_alert.symbol
        new_alert.alert_type = sample_alert.alert_type
        new_alert.condition = sample_alert.condition
        new_alert.target_value = sample_alert.target_value
        
        existing_alerts = [sample_alert]
        
        # Act
        is_duplicate = alert_processor.filter_duplicate_alerts(
            user_id, new_alert, existing_alerts
        )
        
        # Assert
        assert is_duplicate is True

    def test_should_not_detect_duplicate_for_different_user(
        self, alert_processor, sample_alert
    ):
        """Test de non-détection de doublon pour un utilisateur différent."""
        # Arrange
        different_user_id = uuid4()
        new_alert = Mock(spec=Alert)
        new_alert.symbol = sample_alert.symbol
        new_alert.alert_type = sample_alert.alert_type
        new_alert.condition = sample_alert.condition
        new_alert.target_value = sample_alert.target_value
        
        existing_alerts = [sample_alert]
        
        # Act
        is_duplicate = alert_processor.filter_duplicate_alerts(
            different_user_id, new_alert, existing_alerts
        )
        
        # Assert
        assert is_duplicate is False

    def test_should_not_detect_duplicate_for_different_symbol(
        self, alert_processor, sample_alert
    ):
        """Test de non-détection de doublon pour un symbole différent."""
        # Arrange
        user_id = sample_alert.user_id
        new_alert = Mock(spec=Alert)
        new_alert.symbol = "GOOGL"  # Différent
        new_alert.alert_type = sample_alert.alert_type
        new_alert.condition = sample_alert.condition
        new_alert.target_value = sample_alert.target_value
        
        existing_alerts = [sample_alert]
        
        # Act
        is_duplicate = alert_processor.filter_duplicate_alerts(
            user_id, new_alert, existing_alerts
        )
        
        # Assert
        assert is_duplicate is False

    def test_should_not_detect_duplicate_for_inactive_alert(
        self, alert_processor, sample_alert
    ):
        """Test de non-détection de doublon pour alerte inactive."""
        # Arrange
        user_id = sample_alert.user_id
        sample_alert.is_active = False  # Inactive
        
        new_alert = Mock(spec=Alert)
        new_alert.symbol = sample_alert.symbol
        new_alert.alert_type = sample_alert.alert_type
        new_alert.condition = sample_alert.condition
        new_alert.target_value = sample_alert.target_value
        
        existing_alerts = [sample_alert]
        
        # Act
        is_duplicate = alert_processor.filter_duplicate_alerts(
            user_id, new_alert, existing_alerts
        )
        
        # Assert
        assert is_duplicate is False

    def test_should_not_detect_duplicate_for_different_target_value(
        self, alert_processor, sample_alert
    ):
        """Test de non-détection de doublon pour valeur cible différente."""
        # Arrange
        user_id = sample_alert.user_id
        new_alert = Mock(spec=Alert)
        new_alert.symbol = sample_alert.symbol
        new_alert.alert_type = sample_alert.alert_type
        new_alert.condition = sample_alert.condition
        new_alert.target_value = sample_alert.target_value + Decimal("10.00")  # Différent
        
        existing_alerts = [sample_alert]
        
        # Act
        is_duplicate = alert_processor.filter_duplicate_alerts(
            user_id, new_alert, existing_alerts
        )
        
        # Assert
        assert is_duplicate is False


class TestAlertProcessorPrivateMethods:
    """Tests pour les méthodes privées."""

    def test_should_trigger_alert_for_active_price_above(
        self, alert_processor, sample_alert, sample_market_data
    ):
        """Test le déclenchement d'alerte pour prix au-dessus (active)."""
        # Arrange
        sample_alert.alert_type = AlertType.PRICE_ABOVE
        sample_alert.is_active = True
        
        # Act
        should_trigger = alert_processor._should_trigger_alert(
            sample_alert, sample_market_data
        )
        
        # Assert
        assert should_trigger is True
        sample_alert.should_trigger.assert_called_once_with(
            sample_market_data.close_price
        )

    def test_should_not_trigger_alert_for_inactive_alert(
        self, alert_processor, sample_alert, sample_market_data
    ):
        """Test le non-déclenchement d'alerte inactive."""
        # Arrange
        sample_alert.is_active = False
        
        # Act
        should_trigger = alert_processor._should_trigger_alert(
            sample_alert, sample_market_data
        )
        
        # Assert
        assert should_trigger is False

    def test_should_not_trigger_volume_alert_in_private_method(
        self, alert_processor, sample_volume_alert, sample_market_data
    ):
        """Test le non-déclenchement d'alerte de volume dans la méthode privée."""
        # Arrange - Les alertes de volume nécessitent un contexte supplémentaire
        
        # Act
        should_trigger = alert_processor._should_trigger_alert(
            sample_volume_alert, sample_market_data
        )
        
        # Assert
        assert should_trigger is False

    def test_should_not_trigger_percentage_alert_in_private_method(
        self, alert_processor, sample_percentage_alert, sample_market_data
    ):
        """Test le non-déclenchement d'alerte de pourcentage dans la méthode privée."""
        # Arrange - Les alertes de pourcentage nécessitent un prix de clôture précédent
        
        # Act
        should_trigger = alert_processor._should_trigger_alert(
            sample_percentage_alert, sample_market_data
        )
        
        # Assert
        assert should_trigger is False

    def test_should_handle_none_current_value(
        self, alert_processor, sample_market_data
    ):
        """Test la gestion d'une valeur actuelle None."""
        # Arrange
        alert = Mock(spec=Alert)
        alert.is_active = True
        alert.alert_type = "UNKNOWN_TYPE"  # Type non reconnu
        
        # Act
        should_trigger = alert_processor._should_trigger_alert(
            alert, sample_market_data
        )
        
        # Assert
        assert should_trigger is False


class TestAlertProcessorEdgeCases:
    """Tests pour les cas limites."""

    def test_should_handle_none_market_data(self, alert_processor, sample_alert):
        """Test la gestion de données de marché None."""
        # Act & Assert - Cela devrait lever une exception ou être géré gracieusement
        with pytest.raises(AttributeError):
            alert_processor.process_market_data_alerts(None, [sample_alert])

    def test_should_handle_alerts_with_none_symbol(
        self, alert_processor, sample_market_data
    ):
        """Test la gestion d'alertes avec symbole None."""
        # Arrange
        alert = Mock(spec=Alert)
        alert.symbol = None
        alert.is_active = True
        
        # Act & Assert - Cela devrait être géré gracieusement
        with pytest.raises(AttributeError):
            alert_processor.process_market_data_alerts(sample_market_data, [alert])

    def test_should_handle_very_old_alerts(self, alert_processor, sample_alert):
        """Test la gestion d'alertes très anciennes."""
        # Arrange
        sample_alert.created_at = datetime.now(timezone.utc) - timedelta(days=100)
        current_value = Decimal("152.00")
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value
        )
        
        # Assert
        assert isinstance(score, Decimal)
        assert score >= 0  # Le score ne devrait pas être négatif

    def test_should_handle_alerts_without_created_at(
        self, alert_processor, sample_alert
    ):
        """Test la gestion d'alertes sans date de création."""
        # Arrange
        sample_alert.created_at = None
        current_value = Decimal("152.00")
        
        # Act
        score = alert_processor.calculate_alert_priority_score(
            sample_alert, current_value
        )
        
        # Assert
        assert isinstance(score, Decimal)
        assert score > 0


class TestAlertNotificationMethod:
    """Tests pour l'énumération des méthodes de notification."""

    def test_should_have_all_notification_methods(self):
        """Test la présence de toutes les méthodes de notification."""
        # Assert
        assert AlertNotificationMethod.EMAIL == "email"
        assert AlertNotificationMethod.SMS == "sms"
        assert AlertNotificationMethod.PUSH == "push"
        assert AlertNotificationMethod.WEBHOOK == "webhook"
        assert AlertNotificationMethod.IN_APP == "in_app"

    def test_should_inherit_from_str_and_enum(self):
        """Test l'héritage de str et Enum."""
        # Assert
        assert isinstance(AlertNotificationMethod.EMAIL, str)
        assert hasattr(AlertNotificationMethod, '__members__')
