"""
Tests for Domain Base Classes
==============================

Tests for base domain layer classes:
- DomainEvent
- AggregateRoot
- Entity
"""
from datetime import datetime
from boursa_vision.domain.entities.base import DomainEvent, AggregateRoot, Entity


class TestDomainEvent:
    """Test DomainEvent base class."""

    def test_domain_event_creation(self):
        """Test creating a DomainEvent instance."""
        event = DomainEvent()
        
        assert hasattr(event, 'occurred_at')
        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_with_custom_timestamp(self):
        """Test creating DomainEvent with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        event = DomainEvent(occurred_at=custom_time)
        
        assert event.occurred_at == custom_time

    def test_domain_event_default_timestamp_recent(self):
        """Test that default timestamp is recent."""
        before = datetime.now()
        event = DomainEvent()
        after = datetime.now()
        
        assert before <= event.occurred_at <= after

    def test_domain_event_dataclass_behavior(self):
        """Test DomainEvent dataclass behavior."""
        event1 = DomainEvent()
        event2 = DomainEvent(occurred_at=event1.occurred_at)
        
        # Same timestamp should make events equal
        assert event1 == event2

    def test_domain_event_keyword_only(self):
        """Test that DomainEvent requires keyword arguments."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # This should work with keyword argument
        event = DomainEvent(occurred_at=custom_time)
        assert event.occurred_at == custom_time


class TestAggregateRoot:
    """Test AggregateRoot base class."""

    def test_aggregate_root_initialization(self):
        """Test AggregateRoot initialization."""
        class ConcreteAggregate(AggregateRoot):
            pass
        
        aggregate = ConcreteAggregate()
        
        assert hasattr(aggregate, '_domain_events')
        assert isinstance(aggregate._domain_events, list)
        assert len(aggregate._domain_events) == 0

    def test_add_domain_event(self):
        """Test adding domain events."""
        class ConcreteAggregate(AggregateRoot):
            def add_event(self):
                event = DomainEvent()
                self._add_domain_event(event)
        
        aggregate = ConcreteAggregate()
        aggregate.add_event()
        
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], DomainEvent)

    def test_get_domain_events_returns_copy(self):
        """Test that get_domain_events returns a copy."""
        class ConcreteAggregate(AggregateRoot):
            def add_event(self):
                event = DomainEvent()
                self._add_domain_event(event)
        
        aggregate = ConcreteAggregate()
        aggregate.add_event()
        
        events1 = aggregate.get_domain_events()
        events2 = aggregate.get_domain_events()
        
        # Should be different objects (copies)
        assert events1 is not events2
        # But with same content
        assert events1 == events2

    def test_clear_domain_events(self):
        """Test clearing domain events."""
        class ConcreteAggregate(AggregateRoot):
            def add_event(self):
                event = DomainEvent()
                self._add_domain_event(event)
        
        aggregate = ConcreteAggregate()
        aggregate.add_event()
        
        # Verify event was added
        assert len(aggregate.get_domain_events()) == 1
        
        # Clear events
        aggregate.clear_domain_events()
        
        # Verify events are cleared
        assert len(aggregate.get_domain_events()) == 0

    def test_multiple_domain_events(self):
        """Test managing multiple domain events."""
        class ConcreteAggregate(AggregateRoot):
            def add_event(self):
                event = DomainEvent()
                self._add_domain_event(event)
        
        aggregate = ConcreteAggregate()
        
        # Add multiple events
        aggregate.add_event()
        aggregate.add_event()
        aggregate.add_event()
        
        events = aggregate.get_domain_events()
        assert len(events) == 3
        
        # All should be DomainEvent instances
        for event in events:
            assert isinstance(event, DomainEvent)

    def test_aggregate_root_is_abstract(self):
        """Test that AggregateRoot is abstract."""
        from abc import ABC
        
        assert issubclass(AggregateRoot, ABC)

    def test_domain_events_isolation_between_instances(self):
        """Test that domain events are isolated between instances."""
        class ConcreteAggregate(AggregateRoot):
            def add_event(self):
                event = DomainEvent()
                self._add_domain_event(event)
        
        aggregate1 = ConcreteAggregate()
        aggregate2 = ConcreteAggregate()
        
        aggregate1.add_event()
        
        assert len(aggregate1.get_domain_events()) == 1
        assert len(aggregate2.get_domain_events()) == 0


class TestEntity:
    """Test Entity base class."""

    def test_entity_creation(self):
        """Test creating Entity instance."""
        class ConcreteEntity(Entity):
            pass
        
        entity = ConcreteEntity()
        
        assert isinstance(entity, Entity)

    def test_entity_is_abstract(self):
        """Test that Entity is abstract."""
        from abc import ABC
        
        assert issubclass(Entity, ABC)

    def test_entity_no_domain_events(self):
        """Test that Entity doesn't manage domain events."""
        class ConcreteEntity(Entity):
            pass
        
        entity = ConcreteEntity()
        
        # Entity should not have domain event methods
        assert not hasattr(entity, '_domain_events')
        assert not hasattr(entity, 'get_domain_events')
        assert not hasattr(entity, 'clear_domain_events')
        assert not hasattr(entity, '_add_domain_event')

    def test_entity_inheritance(self):
        """Test Entity inheritance."""
        class ConcreteEntity(Entity):
            def __init__(self, value: str):
                self.value = value
        
        entity = ConcreteEntity("test")
        
        assert entity.value == "test"
        assert isinstance(entity, Entity)


class TestBaseClassesInteraction:
    """Test interaction between base classes."""

    def test_domain_event_in_aggregate_root(self):
        """Test using DomainEvent with AggregateRoot."""
        class TestEvent(DomainEvent):
            def __init__(self, data: str, **kwargs):
                super().__init__(**kwargs)
                self.data = data

        class TestAggregate(AggregateRoot):
            def trigger_event(self, data: str):
                event = TestEvent(data=data)
                self._add_domain_event(event)
        
        aggregate = TestAggregate()
        aggregate.trigger_event("test_data")
        
        events = aggregate.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], TestEvent)
        assert events[0].data == "test_data"
        assert isinstance(events[0].occurred_at, datetime)

    def test_entity_and_aggregate_root_separation(self):
        """Test that Entity and AggregateRoot are separate concepts."""
        class MyTestEntity(Entity):
            pass
        
        class MyTestAggregate(AggregateRoot):
            pass
        
        entity = MyTestEntity()
        aggregate = MyTestAggregate()
        
        # Both inherit from ABC but are different
        assert not isinstance(entity, AggregateRoot)
        assert not isinstance(aggregate, Entity)
        
        # But both should be ABC instances
        from abc import ABC
        assert isinstance(entity, ABC)
        assert isinstance(aggregate, ABC)
