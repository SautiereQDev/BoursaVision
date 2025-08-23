"""
Tests for Domain Event Handlers
===============================

Comprehensive test suite for event handlers that process domain events
and implement cross-cutting concerns and side effects.

Coverage:
- PortfolioCreatedEventHandler
- InvestmentAddedEventHandler
- InvestmentCreatedEventHandler
- SignalGeneratedEventHandler
- PerformanceCalculatedEventHandler
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from boursa_vision.application.events.event_handlers import (
    InvestmentAddedEventHandler,
    InvestmentCreatedEventHandler,
    PerformanceCalculatedEventHandler,
    PortfolioCreatedEventHandler,
    SignalGeneratedEventHandler,
)


class TestPortfolioCreatedEventHandler:
    """Tests pour PortfolioCreatedEventHandler"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service"""
        return AsyncMock()

    @pytest.fixture
    def mock_audit_service(self):
        """Mock audit service"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_notification_service, mock_audit_service):
        """Handler instance"""
        return PortfolioCreatedEventHandler(
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
        )

    @pytest.fixture
    def portfolio_created_event(self):
        """Mock portfolio created event"""
        event = MagicMock()
        event.user_id = uuid4()
        event.portfolio_id = uuid4()
        event.name = "Test Portfolio"
        event.occurred_at = datetime.now()
        return event

    def test_handler_initialization(
        self, mock_notification_service, mock_audit_service
    ):
        """Test l'initialisation du handler"""
        handler = PortfolioCreatedEventHandler(
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
        )

        assert handler._notification_service == mock_notification_service
        assert handler._audit_service == mock_audit_service

    async def test_handle_portfolio_created_success(
        self,
        handler,
        portfolio_created_event,
        mock_audit_service,
        mock_notification_service,
    ):
        """Test traitement event portfolio créé avec succès"""
        # Act
        await handler.handle(portfolio_created_event)

        # Assert audit service called
        mock_audit_service.log_event.assert_called_once_with(
            event_type="PORTFOLIO_CREATED",
            user_id=portfolio_created_event.user_id,
            entity_id=portfolio_created_event.portfolio_id,
            timestamp=portfolio_created_event.occurred_at,
            details={
                "portfolio_name": portfolio_created_event.name,
                "action": "CREATE",
            },
        )

        # Assert notification service called
        mock_notification_service.send_notification.assert_called_once_with(
            user_id=portfolio_created_event.user_id,
            message=f"Portfolio '{portfolio_created_event.name}' has been created successfully",
            notification_type="PORTFOLIO_CREATED",
        )

    async def test_handle_event_with_missing_attributes(
        self, handler, mock_audit_service, mock_notification_service
    ):
        """Test traitement event avec attributs manquants"""
        # Arrange
        incomplete_event = MagicMock()
        del incomplete_event.user_id
        del incomplete_event.portfolio_id
        del incomplete_event.name
        del incomplete_event.occurred_at

        # Act
        await handler.handle(incomplete_event)

        # Assert - should handle gracefully with None values
        mock_audit_service.log_event.assert_called_once_with(
            event_type="PORTFOLIO_CREATED",
            user_id=None,
            entity_id=None,
            timestamp=None,
            details={"portfolio_name": "", "action": "CREATE"},
        )

        mock_notification_service.send_notification.assert_called_once_with(
            user_id=None,
            message="Portfolio '' has been created successfully",
            notification_type="PORTFOLIO_CREATED",
        )

    async def test_handle_audit_service_error(
        self,
        handler,
        portfolio_created_event,
        mock_audit_service,
        mock_notification_service,
    ):
        """Test erreur du service audit"""
        # Arrange
        mock_audit_service.log_event.side_effect = Exception("Audit service error")

        # Act & Assert
        with pytest.raises(Exception, match="Audit service error"):
            await handler.handle(portfolio_created_event)

    async def test_handle_notification_service_error(
        self,
        handler,
        portfolio_created_event,
        mock_audit_service,
        mock_notification_service,
    ):
        """Test erreur du service notification"""
        # Arrange
        mock_notification_service.send_notification.side_effect = Exception(
            "Notification error"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Notification error"):
            await handler.handle(portfolio_created_event)


class TestInvestmentAddedEventHandler:
    """Tests pour InvestmentAddedEventHandler"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service"""
        return AsyncMock()

    @pytest.fixture
    def mock_audit_service(self):
        """Mock audit service"""
        return AsyncMock()

    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service"""
        return AsyncMock()

    @pytest.fixture
    def handler(
        self, mock_notification_service, mock_audit_service, mock_analytics_service
    ):
        """Handler instance"""
        return InvestmentAddedEventHandler(
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
            analytics_service=mock_analytics_service,
        )

    @pytest.fixture
    def investment_added_event(self):
        """Mock investment added event"""
        event = MagicMock()
        event.user_id = uuid4()
        event.portfolio_id = uuid4()
        event.investment_id = uuid4()
        event.symbol = "AAPL"
        event.quantity = 10
        event.price = 150.50
        event.occurred_at = datetime.now()
        return event

    def test_handler_initialization(
        self, mock_notification_service, mock_audit_service, mock_analytics_service
    ):
        """Test l'initialisation du handler"""
        handler = InvestmentAddedEventHandler(
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
            analytics_service=mock_analytics_service,
        )

        assert handler._notification_service == mock_notification_service
        assert handler._audit_service == mock_audit_service
        assert handler._analytics_service == mock_analytics_service

    async def test_handle_investment_added_success(
        self,
        handler,
        investment_added_event,
        mock_audit_service,
        mock_analytics_service,
        mock_notification_service,
    ):
        """Test traitement event investment ajouté avec succès"""
        # Act
        await handler.handle(investment_added_event)

        # Assert audit service called
        mock_audit_service.log_event.assert_called_once_with(
            event_type="INVESTMENT_ADDED",
            user_id=investment_added_event.user_id,
            entity_id=investment_added_event.portfolio_id,
            timestamp=investment_added_event.occurred_at,
            details={
                "investment_id": investment_added_event.investment_id,
                "symbol": investment_added_event.symbol,
                "quantity": investment_added_event.quantity,
                "price": investment_added_event.price,
                "action": "ADD_INVESTMENT",
            },
        )

        # Assert analytics service called
        mock_analytics_service.track_investment_activity.assert_called_once_with(
            user_id=investment_added_event.user_id,
            portfolio_id=investment_added_event.portfolio_id,
            investment_id=investment_added_event.investment_id,
            action="BUY",
            quantity=investment_added_event.quantity,
            price=investment_added_event.price,
        )

        # Assert notification service called
        expected_message = (
            f"Added {investment_added_event.quantity} shares of "
            f"{investment_added_event.symbol} to portfolio"
        )
        mock_notification_service.send_notification.assert_called_once_with(
            user_id=investment_added_event.user_id,
            message=expected_message,
            notification_type="INVESTMENT_ADDED",
        )

    async def test_handle_event_with_defaults(
        self,
        handler,
        mock_audit_service,
        mock_analytics_service,
        mock_notification_service,
    ):
        """Test traitement event avec valeurs par défaut"""
        # Arrange
        minimal_event = MagicMock()
        del minimal_event.user_id
        del minimal_event.portfolio_id
        del minimal_event.investment_id
        del minimal_event.symbol
        del minimal_event.quantity
        del minimal_event.price
        del minimal_event.occurred_at

        # Act
        await handler.handle(minimal_event)

        # Assert services called with default values
        mock_audit_service.log_event.assert_called_once()
        mock_analytics_service.track_investment_activity.assert_called_once()
        mock_notification_service.send_notification.assert_called_once()


class TestInvestmentCreatedEventHandler:
    """Tests pour InvestmentCreatedEventHandler"""

    @pytest.fixture
    def mock_market_data_service(self):
        """Mock market data service"""
        return AsyncMock()

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_market_data_service, mock_cache_service):
        """Handler instance"""
        return InvestmentCreatedEventHandler(
            market_data_service=mock_market_data_service,
            cache_service=mock_cache_service,
        )

    @pytest.fixture
    def investment_created_event(self):
        """Mock investment created event"""
        event = MagicMock()
        event.symbol = "AAPL"
        event.investment_id = uuid4()
        event.name = "Apple Inc."
        event.occurred_at = datetime.now()
        return event

    def test_handler_initialization(self, mock_market_data_service, mock_cache_service):
        """Test l'initialisation du handler"""
        handler = InvestmentCreatedEventHandler(
            market_data_service=mock_market_data_service,
            cache_service=mock_cache_service,
        )

        assert handler._market_data_service == mock_market_data_service
        assert handler._cache_service == mock_cache_service

    async def test_handle_investment_created_success(
        self,
        handler,
        investment_created_event,
        mock_market_data_service,
        mock_cache_service,
    ):
        """Test traitement event investment créé avec succès"""
        # Act
        await handler.handle(investment_created_event)

        # Assert market data tracking started
        mock_market_data_service.start_tracking.assert_called_once_with(
            investment_created_event.symbol
        )

        # Assert cache invalidated
        assert mock_cache_service.invalidate_pattern.call_count == 2
        mock_cache_service.invalidate_pattern.assert_any_call("investment:*")
        mock_cache_service.invalidate_pattern.assert_any_call("search:*")

        # Assert initial market data fetch attempted
        mock_market_data_service.fetch_current_price.assert_called_once_with(
            investment_created_event.symbol
        )

    async def test_handle_event_with_missing_symbol(
        self, handler, mock_market_data_service, mock_cache_service
    ):
        """Test traitement event sans symbol"""
        # Arrange
        event_no_symbol = MagicMock()
        del event_no_symbol.symbol

        # Act
        await handler.handle(event_no_symbol)

        # Assert services called with empty string
        mock_market_data_service.start_tracking.assert_called_once_with("")
        mock_market_data_service.fetch_current_price.assert_called_once_with("")

    async def test_handle_market_data_fetch_error(
        self,
        handler,
        investment_created_event,
        mock_market_data_service,
        mock_cache_service,
    ):
        """Test erreur lors du fetch des données marché"""
        # Arrange
        mock_market_data_service.fetch_current_price.side_effect = Exception(
            "Market data unavailable"
        )

        # Act - should not raise exception
        await handler.handle(investment_created_event)

        # Assert other operations still completed
        mock_market_data_service.start_tracking.assert_called_once()
        assert mock_cache_service.invalidate_pattern.call_count == 2

    async def test_handle_cache_service_error(
        self,
        handler,
        investment_created_event,
        mock_market_data_service,
        mock_cache_service,
    ):
        """Test erreur du service cache"""
        # Arrange
        mock_cache_service.invalidate_pattern.side_effect = Exception("Cache error")

        # Act & Assert
        with pytest.raises(Exception, match="Cache error"):
            await handler.handle(investment_created_event)


class TestSignalGeneratedEventHandler:
    """Tests pour SignalGeneratedEventHandler"""

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service"""
        return AsyncMock()

    @pytest.fixture
    def mock_alert_service(self):
        """Mock alert service"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_notification_service, mock_alert_service):
        """Handler instance"""
        return SignalGeneratedEventHandler(
            notification_service=mock_notification_service,
            alert_service=mock_alert_service,
        )

    @pytest.fixture
    def high_confidence_buy_signal(self):
        """High confidence BUY signal"""
        signal = MagicMock()
        signal.symbol = "AAPL"
        signal.action = "BUY"
        signal.confidence = 0.85
        return signal

    @pytest.fixture
    def signal_generated_event(self, high_confidence_buy_signal):
        """Mock signal generated event"""
        event = MagicMock()
        event.signal = high_confidence_buy_signal
        event.occurred_at = datetime.now()
        return event

    def test_handler_initialization(
        self, mock_notification_service, mock_alert_service
    ):
        """Test l'initialisation du handler"""
        handler = SignalGeneratedEventHandler(
            notification_service=mock_notification_service,
            alert_service=mock_alert_service,
        )

        assert handler._notification_service == mock_notification_service
        assert handler._alert_service == mock_alert_service

    async def test_handle_high_confidence_buy_signal(
        self,
        handler,
        signal_generated_event,
        mock_alert_service,
        mock_notification_service,
    ):
        """Test traitement signal BUY haute confiance"""
        # Act
        await handler.handle(signal_generated_event)

        # Assert alert created
        signal = signal_generated_event.signal
        mock_alert_service.create_alert.assert_called_once_with(
            symbol=signal.symbol,
            alert_type="SIGNAL_BUY",
            message=f"High confidence BUY signal for {signal.symbol} ({signal.confidence:.2%})",
            confidence=signal.confidence,
        )

        # Assert notification sent
        mock_notification_service.notify_watchlist_users.assert_called_once_with(
            symbol=signal.symbol,
            message=f"Trading signal: BUY {signal.symbol} (Confidence: {signal.confidence:.2%})",
            notification_type="TRADING_SIGNAL",
        )

    async def test_handle_high_confidence_sell_signal(
        self, handler, mock_alert_service, mock_notification_service
    ):
        """Test traitement signal SELL haute confiance"""
        # Arrange
        sell_signal = MagicMock()
        sell_signal.symbol = "TSLA"
        sell_signal.action = "SELL"
        sell_signal.confidence = 0.90

        event = MagicMock()
        event.signal = sell_signal

        # Act
        await handler.handle(event)

        # Assert alert and notification for SELL
        mock_alert_service.create_alert.assert_called_once_with(
            symbol=sell_signal.symbol,
            alert_type="SIGNAL_SELL",
            message=f"High confidence SELL signal for {sell_signal.symbol} ({sell_signal.confidence:.2%})",
            confidence=sell_signal.confidence,
        )

    async def test_handle_low_confidence_signal(
        self, handler, mock_alert_service, mock_notification_service
    ):
        """Test traitement signal faible confiance"""
        # Arrange
        low_confidence_signal = MagicMock()
        low_confidence_signal.symbol = "MSFT"
        low_confidence_signal.action = "BUY"
        low_confidence_signal.confidence = 0.60  # Below threshold

        event = MagicMock()
        event.signal = low_confidence_signal

        # Act
        await handler.handle(event)

        # Assert no alert or notification for low confidence
        mock_alert_service.create_alert.assert_not_called()
        mock_notification_service.notify_watchlist_users.assert_not_called()

    async def test_handle_hold_signal(
        self, handler, mock_alert_service, mock_notification_service
    ):
        """Test traitement signal HOLD"""
        # Arrange
        hold_signal = MagicMock()
        hold_signal.symbol = "GOOGL"
        hold_signal.action = "HOLD"
        hold_signal.confidence = 0.80  # High confidence but HOLD action

        event = MagicMock()
        event.signal = hold_signal

        # Act
        await handler.handle(event)

        # Assert no alert for HOLD action
        mock_alert_service.create_alert.assert_not_called()
        mock_notification_service.notify_watchlist_users.assert_not_called()

    async def test_handle_event_without_signal(
        self, handler, mock_alert_service, mock_notification_service
    ):
        """Test traitement event sans signal"""
        # Arrange
        event_no_signal = MagicMock()
        event_no_signal.signal = None

        # Act
        await handler.handle(event_no_signal)

        # Assert early return, no services called
        mock_alert_service.create_alert.assert_not_called()
        mock_notification_service.notify_watchlist_users.assert_not_called()

    async def test_handle_event_missing_signal_attribute(
        self, handler, mock_alert_service, mock_notification_service
    ):
        """Test traitement event sans attribut signal"""
        # Arrange
        event_no_signal_attr = MagicMock()
        del event_no_signal_attr.signal

        # Act
        await handler.handle(event_no_signal_attr)

        # Assert early return with None
        mock_alert_service.create_alert.assert_not_called()
        mock_notification_service.notify_watchlist_users.assert_not_called()


class TestPerformanceCalculatedEventHandler:
    """Tests pour PerformanceCalculatedEventHandler"""

    @pytest.fixture
    def mock_analytics_service(self):
        """Mock analytics service"""
        return AsyncMock()

    @pytest.fixture
    def mock_reporting_service(self):
        """Mock reporting service"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_analytics_service, mock_reporting_service):
        """Handler instance"""
        return PerformanceCalculatedEventHandler(
            analytics_service=mock_analytics_service,
            reporting_service=mock_reporting_service,
        )

    @pytest.fixture
    def performance_calculated_event(self):
        """Mock performance calculated event"""
        event = MagicMock()
        event.portfolio_id = uuid4()
        event.performance_data = {
            "total_return": 0.15,
            "monthly_return": 0.05,
            "volatility": 0.12,
            "sharpe_ratio": 1.25,
        }
        event.occurred_at = datetime.now()
        return event

    def test_handler_initialization(
        self, mock_analytics_service, mock_reporting_service
    ):
        """Test l'initialisation du handler"""
        handler = PerformanceCalculatedEventHandler(
            analytics_service=mock_analytics_service,
            reporting_service=mock_reporting_service,
        )

        assert handler._analytics_service == mock_analytics_service
        assert handler._reporting_service == mock_reporting_service

    async def test_handle_performance_calculated_success(
        self,
        handler,
        performance_calculated_event,
        mock_analytics_service,
        mock_reporting_service,
    ):
        """Test traitement event performance calculée avec succès"""
        # Act
        await handler.handle(performance_calculated_event)

        # Assert performance snapshot stored
        mock_analytics_service.store_performance_snapshot.assert_called_once_with(
            portfolio_id=performance_calculated_event.portfolio_id,
            performance_data=performance_calculated_event.performance_data,
            timestamp=performance_calculated_event.occurred_at,
        )

    async def test_handle_first_day_of_month_generates_report(
        self,
        handler,
        performance_calculated_event,
        mock_analytics_service,
        mock_reporting_service,
        monkeypatch,
    ):
        """Test génération rapport mensuel le premier du mois"""
        # Arrange - Mock datetime to return first day of month
        import datetime as dt_module

        mock_datetime = MagicMock()
        mock_datetime.now.return_value.day = 1
        monkeypatch.setattr(dt_module, "datetime", mock_datetime)

        # Act
        await handler.handle(performance_calculated_event)

        # Assert monthly report generated
        mock_reporting_service.generate_monthly_report.assert_called_once_with(
            portfolio_id=performance_calculated_event.portfolio_id
        )

    async def test_handle_not_first_day_no_report(
        self,
        handler,
        performance_calculated_event,
        mock_analytics_service,
        mock_reporting_service,
        monkeypatch,
    ):
        """Test pas de rapport mensuel si pas le premier du mois"""
        # Arrange - Mock datetime to return non-first day
        import datetime as dt_module

        mock_datetime = MagicMock()
        mock_datetime.now.return_value.day = 15  # Mid-month
        monkeypatch.setattr(dt_module, "datetime", mock_datetime)

        # Act
        await handler.handle(performance_calculated_event)

        # Assert no monthly report generated
        mock_reporting_service.generate_monthly_report.assert_not_called()
        # But performance snapshot still stored
        mock_analytics_service.store_performance_snapshot.assert_called_once()

    async def test_handle_event_with_missing_attributes(
        self, handler, mock_analytics_service, mock_reporting_service
    ):
        """Test traitement event avec attributs manquants"""
        # Arrange
        minimal_event = MagicMock()
        del minimal_event.portfolio_id
        del minimal_event.performance_data
        del minimal_event.occurred_at

        # Act
        await handler.handle(minimal_event)

        # Assert service called with None values
        mock_analytics_service.store_performance_snapshot.assert_called_once_with(
            portfolio_id=None,
            performance_data={},
            timestamp=None,
        )

    async def test_handle_analytics_service_error(
        self,
        handler,
        performance_calculated_event,
        mock_analytics_service,
        mock_reporting_service,
    ):
        """Test erreur du service analytics"""
        # Arrange
        mock_analytics_service.store_performance_snapshot.side_effect = Exception(
            "Analytics error"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Analytics error"):
            await handler.handle(performance_calculated_event)


class TestEventHandlersIntegration:
    """Tests d'intégration pour les event handlers"""

    def test_all_handlers_implement_handle_method(self):
        """Test que tous les handlers implémentent la méthode handle"""
        handlers = [
            PortfolioCreatedEventHandler,
            InvestmentAddedEventHandler,
            InvestmentCreatedEventHandler,
            SignalGeneratedEventHandler,
            PerformanceCalculatedEventHandler,
        ]

        for handler_class in handlers:
            assert hasattr(handler_class, "handle")
            assert callable(getattr(handler_class, "handle"))

    def test_handlers_dependency_injection(self):
        """Test injection de dépendances des handlers"""
        # Test handlers with different dependency patterns
        mock_service1 = AsyncMock()
        mock_service2 = AsyncMock()
        mock_service3 = AsyncMock()

        # Portfolio handler - 2 services
        portfolio_handler = PortfolioCreatedEventHandler(mock_service1, mock_service2)
        assert portfolio_handler._notification_service == mock_service1
        assert portfolio_handler._audit_service == mock_service2

        # Investment added handler - 3 services
        investment_handler = InvestmentAddedEventHandler(
            mock_service1, mock_service2, mock_service3
        )
        assert investment_handler._notification_service == mock_service1
        assert investment_handler._audit_service == mock_service2
        assert investment_handler._analytics_service == mock_service3

    async def test_handlers_error_propagation(self):
        """Test propagation des erreurs des handlers"""
        mock_service = AsyncMock()
        mock_service.log_event.side_effect = Exception("Service error")

        handler = PortfolioCreatedEventHandler(AsyncMock(), mock_service)
        event = MagicMock()

        with pytest.raises(Exception, match="Service error"):
            await handler.handle(event)
