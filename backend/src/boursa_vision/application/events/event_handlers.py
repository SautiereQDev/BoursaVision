"""
Domain Event Handlers
====================

Handlers for processing domain events raised by aggregates.
These handlers implement cross-cutting concerns and side effects.
"""

from typing import Any

from ..common import IEventHandler


class PortfolioCreatedEventHandler(IEventHandler[Any]):
    """Handler for portfolio created events"""

    def __init__(self, notification_service, audit_service):
        self._notification_service = notification_service
        self._audit_service = audit_service

    async def handle(self, event: Any) -> None:
        """
        Handle portfolio created event.

        Args:
            event: Portfolio created domain event
        """
        # Log audit event
        await self._audit_service.log_event(
            event_type="PORTFOLIO_CREATED",
            user_id=getattr(event, "user_id", None),
            entity_id=getattr(event, "portfolio_id", None),
            timestamp=getattr(event, "occurred_at", None),
            details={"portfolio_name": getattr(event, "name", ""), "action": "CREATE"},
        )

        # Send welcome notification
        await self._notification_service.send_notification(
            user_id=getattr(event, "user_id", None),
            message=f"Portfolio '{getattr(event, 'name', '')}' has been created successfully",
            notification_type="PORTFOLIO_CREATED",
        )


class InvestmentAddedEventHandler(IEventHandler[Any]):
    """Handler for investment added to portfolio events"""

    def __init__(self, notification_service, audit_service, analytics_service):
        self._notification_service = notification_service
        self._audit_service = audit_service
        self._analytics_service = analytics_service

    async def handle(self, event: Any) -> None:
        """
        Handle investment added event.

        Args:
            event: Investment added domain event
        """
        # Log audit event
        await self._audit_service.log_event(
            event_type="INVESTMENT_ADDED",
            user_id=getattr(event, "user_id", None),
            entity_id=getattr(event, "portfolio_id", None),
            timestamp=getattr(event, "occurred_at", None),
            details={
                "investment_id": getattr(event, "investment_id", ""),
                "symbol": getattr(event, "symbol", ""),
                "quantity": getattr(event, "quantity", 0),
                "price": getattr(event, "price", 0),
                "action": "ADD_INVESTMENT",
            },
        )

        # Update analytics
        await self._analytics_service.track_investment_activity(
            user_id=getattr(event, "user_id", None),
            portfolio_id=getattr(event, "portfolio_id", None),
            investment_id=getattr(event, "investment_id", None),
            action="BUY",
            quantity=getattr(event, "quantity", 0),
            price=getattr(event, "price", 0),
        )

        # Send notification
        await self._notification_service.send_notification(
            user_id=getattr(event, "user_id", None),
            message=f"Added {getattr(event, 'quantity', 0)} shares of "
            "{getattr(event, 'symbol', '')} to portfolio",
            notification_type="INVESTMENT_ADDED",
        )


class InvestmentCreatedEventHandler(IEventHandler[Any]):
    """Handler for investment created events"""

    def __init__(self, market_data_service, cache_service):
        self._market_data_service = market_data_service
        self._cache_service = cache_service

    async def handle(self, event: Any) -> None:
        """
        Handle investment created event.

        Args:
            event: Investment created domain event
        """
        symbol = getattr(event, "symbol", "")

        # Start tracking market data for new investment
        await self._market_data_service.start_tracking(symbol)

        # Invalidate investment cache
        await self._cache_service.invalidate_pattern("investment:*")
        await self._cache_service.invalidate_pattern("search:*")

        # Pre-load initial market data
        try:
            await self._market_data_service.fetch_current_price(symbol)
        except Exception:
            # Don't fail if market data unavailable
            pass


class SignalGeneratedEventHandler(IEventHandler[Any]):
    """Handler for trading signal generated events"""

    def __init__(self, notification_service, alert_service):
        self._notification_service = notification_service
        self._alert_service = alert_service

    async def handle(self, event: Any) -> None:
        """
        Handle signal generated event.

        Args:
            event: Signal generated domain event
        """
        signal = getattr(event, "signal", None)
        if not signal:
            return

        symbol = getattr(signal, "symbol", "")
        action = getattr(signal, "action", "")
        confidence = getattr(signal, "confidence", 0)

        # Send high-confidence signal alerts
        if confidence > 0.7 and action in ["BUY", "SELL"]:
            await self._alert_service.create_alert(
                symbol=symbol,
                alert_type=f"SIGNAL_{action}",
                message=f"High confidence {action} signal for {symbol} ({confidence:.2%})",
                confidence=confidence,
            )

            # Notify users with this investment in watchlist
            await self._notification_service.notify_watchlist_users(
                symbol=symbol,
                message=f"Trading signal: {action} {symbol} (Confidence: {confidence:.2%})",
                notification_type="TRADING_SIGNAL",
            )


class PerformanceCalculatedEventHandler(IEventHandler[Any]):
    """Handler for performance calculated events"""

    def __init__(self, analytics_service, reporting_service):
        self._analytics_service = analytics_service
        self._reporting_service = reporting_service

    async def handle(self, event: Any) -> None:
        """
        Handle performance calculated event.

        Args:
            event: Performance calculated domain event
        """
        portfolio_id = getattr(event, "portfolio_id", None)
        performance_data = getattr(event, "performance_data", {})

        # Store performance metrics for trending
        await self._analytics_service.store_performance_snapshot(
            portfolio_id=portfolio_id,
            performance_data=performance_data,
            timestamp=getattr(event, "occurred_at", None),
        )

        # Generate monthly report if end of month
        from datetime import datetime

        if datetime.now().day == 1:  # First day of month
            await self._reporting_service.generate_monthly_report(
                portfolio_id=portfolio_id
            )
