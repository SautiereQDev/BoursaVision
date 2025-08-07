"""
Base classes for Domain Layer
============================

Contains base classes and interfaces for Clean Architecture domain layer.
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import List, Any
from datetime import datetime


@dataclass
class DomainEvent:
    """Base class for domain events"""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    

class AggregateRoot(ABC):
    """
    Base class for aggregate roots in DDD
    
    Manages domain events and provides common functionality
    for all aggregate roots in the domain.
    """
    
    def __init__(self):
        self._domain_events: List[DomainEvent] = []
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event to be published"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events after publishing"""
        self._domain_events.clear()


class Entity(ABC):
    """Base class for domain entities"""
    pass


class ValueObject(ABC):
    """Base class for value objects"""
    pass
