"""
Alert Management Service
========================

Domain service for managing price alerts and notifications.
Implements alert processing logic following DDD principles.

Classes:
    AlertNotificationMethod: Enum for notification delivery methods.
    AlertProcessor: Domain service for processing alerts.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from ..entities.market_data import MarketData
from ..value_objects.alert import Alert, AlertCondition, AlertType


class AlertNotificationMethod(str, Enum):
    """Methods for delivering alert notifications"""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class AlertProcessor:
    """
    Domain service for processing and managing alerts.

    Handles alert evaluation, triggering, and notification logic
    without dependencies on external infrastructure.
    """

    def __init__(self):
        self._notification_methods = [
            AlertNotificationMethod.IN_APP,
            AlertNotificationMethod.EMAIL,
        ]

    def process_market_data_alerts(
        self, market_data: MarketData, active_alerts: list[Alert]
    ) -> list[Alert]:
        """
        Process alerts against new market data.

        Returns list of triggered alerts.
        """
        triggered_alerts = []
        current_price = market_data.close_price
        current_time = market_data.timestamp

        # Filter alerts for this symbol
        symbol_alerts = [
            alert
            for alert in active_alerts
            if alert.symbol.upper() == market_data.symbol.upper()
        ]

        for alert in symbol_alerts:
            if self._should_trigger_alert(alert, market_data):
                triggered_alert = alert.trigger(current_price, current_time)
                triggered_alerts.append(triggered_alert)

        return triggered_alerts

    def process_volume_alerts(
        self, market_data: MarketData, active_alerts: list[Alert], average_volume: int
    ) -> list[Alert]:
        """Process volume-based alerts"""
        triggered_alerts = []
        current_time = market_data.timestamp

        # Filter volume alerts for this symbol
        volume_alerts = [
            alert
            for alert in active_alerts
            if (
                alert.symbol.upper() == market_data.symbol.upper()
                and alert.alert_type == AlertType.VOLUME_SPIKE
            )
        ]

        for alert in volume_alerts:
            volume_multiplier = (
                Decimal(market_data.volume) / Decimal(average_volume)
                if average_volume > 0
                else Decimal("0")
            )

            if alert.should_trigger(volume_multiplier):
                triggered_alert = alert.trigger(volume_multiplier, current_time)
                triggered_alerts.append(triggered_alert)

        return triggered_alerts

    def process_percentage_change_alerts(
        self,
        market_data: MarketData,
        active_alerts: list[Alert],
        previous_close: Decimal,
    ) -> list[Alert]:
        """Process percentage change alerts"""
        triggered_alerts = []
        current_time = market_data.timestamp

        if previous_close <= 0:
            return triggered_alerts

        percentage_change = (
            (market_data.close_price - previous_close) / previous_close
        ) * Decimal("100")

        # Filter percentage change alerts for this symbol
        percent_alerts = [
            alert
            for alert in active_alerts
            if (
                alert.symbol.upper() == market_data.symbol.upper()
                and alert.alert_type == AlertType.PRICE_CHANGE_PERCENT
            )
        ]

        for alert in percent_alerts:
            if alert.should_trigger(abs(percentage_change)):
                triggered_alert = alert.trigger(percentage_change, current_time)
                triggered_alerts.append(triggered_alert)

        return triggered_alerts

    def validate_alert_creation(self, alert: Alert) -> list[str]:
        """
        Validate alert parameters for creation.

        Returns list of validation error messages.
        """
        errors = []

        # Basic validation
        if not alert.symbol:
            errors.append("Symbol is required")

        if alert.target_value <= 0:
            errors.append("Target value must be positive")

        # Condition-specific validation
        if alert.condition in [AlertCondition.BETWEEN, AlertCondition.OUTSIDE_RANGE]:
            if alert.min_value is None or alert.max_value is None:
                errors.append(
                    f"{alert.condition} requires both min_value and max_value"
                )
            elif alert.min_value >= alert.max_value:
                errors.append("min_value must be less than max_value")

        # Type-specific validation
        if (
            alert.alert_type == AlertType.PRICE_CHANGE_PERCENT
            and alert.target_value > 100
        ):
            errors.append("Percentage change cannot exceed 100%")
        elif alert.alert_type == AlertType.VOLUME_SPIKE and alert.target_value < 1:
            errors.append("Volume spike multiplier must be at least 1.0")

        return errors

    def calculate_alert_priority_score(
        self,
        alert: Alert,
        current_value: Decimal,
        market_volatility: Decimal | None = None,
    ) -> Decimal:
        """
        Calculate priority score for alert notification.

        Higher score means higher priority.
        """
        base_score = Decimal(alert.priority.weight)

        # Distance from target (closer = higher priority)
        if alert.target_value > 0:
            distance_factor = (
                abs(current_value - alert.target_value) / alert.target_value
            )
            distance_score = max(Decimal("0"), Decimal("1") - distance_factor)
            base_score += distance_score

        # Volatility adjustment (more volatile = higher priority)
        if market_volatility is not None and market_volatility > 0:
            volatility_score = min(
                market_volatility / Decimal("20"), Decimal("1")
            )  # Cap at 20%
            base_score += volatility_score

        # Time-based urgency (newer alerts get slight boost)
        if alert.created_at:
            hours_old = (datetime.now(UTC) - alert.created_at).total_seconds() / 3600
            freshness_score = max(
                Decimal("0"), Decimal("1") - Decimal(hours_old) / Decimal("24")
            )
            base_score += freshness_score * Decimal("0.1")  # Small freshness bonus

        return base_score

    def group_alerts_by_symbol(self, alerts: list[Alert]) -> dict[str, list[Alert]]:
        """Group alerts by symbol for batch processing"""
        grouped = {}
        for alert in alerts:
            symbol = alert.symbol.upper()
            if symbol not in grouped:
                grouped[symbol] = []
            grouped[symbol].append(alert)
        return grouped

    def filter_duplicate_alerts(
        self, user_id: UUID, new_alert: Alert, existing_alerts: list[Alert]
    ) -> bool:
        """
        Check if similar alert already exists for user.

        Returns True if duplicate exists.
        """
        for existing in existing_alerts:
            if (
                existing.user_id == user_id
                and existing.symbol.upper() == new_alert.symbol.upper()
                and existing.alert_type == new_alert.alert_type
                and existing.condition == new_alert.condition
                and existing.is_active
                and abs(existing.target_value - new_alert.target_value)
                < Decimal("0.01")
            ):
                return True
        return False

    def _should_trigger_alert(self, alert: Alert, market_data: MarketData) -> bool:
        """Check if alert should trigger based on market data"""
        if not alert.is_active:
            return False

        current_value = None

        if alert.alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW]:
            current_value = market_data.close_price
        elif alert.alert_type == AlertType.VOLUME_SPIKE:
            # Volume alerts need additional context (average volume)
            # This would be handled by process_volume_alerts
            return False
        elif alert.alert_type == AlertType.PRICE_CHANGE_PERCENT:
            # Percentage change alerts need previous close
            # This would be handled by process_percentage_change_alerts
            return False

        return current_value is not None and alert.should_trigger(current_value)
