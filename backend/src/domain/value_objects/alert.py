"""
Alert Value Objects
==================

Value objects for representing different types of alerts and notifications.

Classes:
    AlertType: Enum representing different alert types.
    AlertCondition: Enum representing alert trigger conditions.
    Alert: Value object representing a price or condition alert.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from .money import Money


class AlertType(str, Enum):
    """Types of alerts that can be created"""
    
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PERCENT = "price_change_percent"
    VOLUME_SPIKE = "volume_spike"
    TECHNICAL_INDICATOR = "technical_indicator"
    NEWS_SENTIMENT = "news_sentiment"


class AlertCondition(str, Enum):
    """Conditions for triggering alerts"""
    
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL_TO = "eq"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"
    OUTSIDE_RANGE = "outside_range"


class AlertPriority(str, Enum):
    """Alert priority levels"""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        """Numeric weight for priority ordering"""
        weights = {
            self.LOW: 1,
            self.MEDIUM: 2,
            self.HIGH: 3,
            self.CRITICAL: 4
        }
        return weights.get(self, 1)


@dataclass(frozen=True)
class Alert:
    """
    Value object representing an alert condition.
    
    Immutable representation of alert parameters and state.
    """
    
    id: UUID
    symbol: str
    alert_type: AlertType
    condition: AlertCondition
    target_value: Decimal
    current_value: Optional[Decimal] = None
    priority: AlertPriority = AlertPriority.MEDIUM
    message: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    user_id: Optional[UUID] = None
    
    # Optional range values for BETWEEN and OUTSIDE_RANGE conditions
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    
    def __post_init__(self):
        """Validate alert parameters"""
        if not self.symbol:
            raise ValueError("Symbol is required")
            
        if self.target_value <= 0:
            raise ValueError("Target value must be positive")
            
        if self.condition in [AlertCondition.BETWEEN, AlertCondition.OUTSIDE_RANGE]:
            if self.min_value is None or self.max_value is None:
                raise ValueError(f"{self.condition} requires min_value and max_value")
            if self.min_value >= self.max_value:
                raise ValueError("min_value must be less than max_value")
    
    def should_trigger(self, current_value: Decimal) -> bool:
        """Check if alert should trigger based on current value"""
        if not self.is_active:
            return False
            
        condition_checks = {
            AlertCondition.GREATER_THAN: current_value > self.target_value,
            AlertCondition.LESS_THAN: current_value < self.target_value,
            AlertCondition.EQUAL_TO: current_value == self.target_value,
            AlertCondition.GREATER_THAN_OR_EQUAL: current_value >= self.target_value,
            AlertCondition.LESS_THAN_OR_EQUAL: current_value <= self.target_value,
            AlertCondition.BETWEEN: (
                self.min_value <= current_value <= self.max_value
                if self.min_value and self.max_value else False
            ),
            AlertCondition.OUTSIDE_RANGE: (
                current_value < self.min_value or current_value > self.max_value
                if self.min_value and self.max_value else False
            )
        }
        
        return condition_checks.get(self.condition, False)
    
    def get_trigger_message(self, current_value: Decimal) -> str:
        """Generate trigger message for the alert"""
        if self.message:
            return self.message
            
        condition_messages = {
            AlertCondition.GREATER_THAN: f"{self.symbol} price ${current_value} is above ${self.target_value}",
            AlertCondition.LESS_THAN: f"{self.symbol} price ${current_value} is below ${self.target_value}",
            AlertCondition.EQUAL_TO: f"{self.symbol} price has reached ${self.target_value}",
            AlertCondition.GREATER_THAN_OR_EQUAL: f"{self.symbol} price ${current_value} has reached or exceeded ${self.target_value}",
            AlertCondition.LESS_THAN_OR_EQUAL: f"{self.symbol} price ${current_value} has fallen to or below ${self.target_value}",
            AlertCondition.BETWEEN: f"{self.symbol} price ${current_value} is within target range ${self.min_value}-${self.max_value}",
            AlertCondition.OUTSIDE_RANGE: f"{self.symbol} price ${current_value} is outside target range ${self.min_value}-${self.max_value}"
        }
        
        return condition_messages.get(
            self.condition, 
            f"{self.symbol} alert triggered: ${current_value}"
        )
    
    def trigger(self, current_value: Decimal, timestamp: datetime) -> "Alert":
        """Create a triggered version of this alert"""
        return Alert(
            id=self.id,
            symbol=self.symbol,
            alert_type=self.alert_type,
            condition=self.condition,
            target_value=self.target_value,
            current_value=current_value,
            priority=self.priority,
            message=self.message,
            is_active=False,  # Deactivate after triggering
            created_at=self.created_at,
            triggered_at=timestamp,
            user_id=self.user_id,
            min_value=self.min_value,
            max_value=self.max_value
        )
    
    def deactivate(self) -> "Alert":
        """Create a deactivated version of this alert"""
        return Alert(
            id=self.id,
            symbol=self.symbol,
            alert_type=self.alert_type,
            condition=self.condition,
            target_value=self.target_value,
            current_value=self.current_value,
            priority=self.priority,
            message=self.message,
            is_active=False,
            created_at=self.created_at,
            triggered_at=self.triggered_at,
            user_id=self.user_id,
            min_value=self.min_value,
            max_value=self.max_value
        )
    
    @property
    def is_triggered(self) -> bool:
        """Check if alert has been triggered"""
        return self.triggered_at is not None
    
    @property
    def days_active(self) -> int:
        """Get number of days alert has been active"""
        if not self.created_at:
            return 0
        end_time = self.triggered_at or datetime.now()
        return (end_time - self.created_at).days
    
    def __str__(self) -> str:
        if self.is_triggered:
            status = "TRIGGERED"
        elif self.is_active:
            status = "ACTIVE"
        else:
            status = "INACTIVE"
        return f"Alert({self.symbol}, {self.condition.value} ${self.target_value}, {status})"
    
    def __repr__(self) -> str:
        return (
            f"Alert(id={self.id}, symbol='{self.symbol}', "
            f"condition='{self.condition.value}', target_value={self.target_value}, "
            f"is_active={self.is_active})"
        )
