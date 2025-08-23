"""
Base Interfaces for CQRS Pattern
================================

Defines the core interfaces for Command and Query handling
following CQRS (Command Query Responsibility Segregation) principles.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for commands, queries and results
TCommand = TypeVar("TCommand")
TQuery = TypeVar("TQuery")
TResult = TypeVar("TResult")


class ICommand(ABC):
    """Marker interface for commands"""

    @abstractmethod
    def __repr__(self) -> str:
        """Required abstract method for command identification"""
        ...


class IQuery(ABC):
    """Marker interface for queries"""

    @abstractmethod
    def __repr__(self) -> str:
        """Required abstract method for query identification"""
        ...


class ICommandHandler(ABC, Generic[TCommand, TResult]):
    """Interface for command handlers"""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """Handle the command and return result"""


class IQueryHandler(ABC, Generic[TQuery, TResult]):
    """Interface for query handlers"""

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """Handle the query and return result"""


class IEventHandler(ABC, Generic[TCommand]):
    """Interface for domain event handlers"""

    @abstractmethod
    async def handle(self, event: TCommand) -> None:
        """Handle the domain event"""


class IUseCase(ABC, Generic[TCommand, TResult]):
    """Interface for use case implementations"""

    @abstractmethod
    async def execute(self, request: TCommand) -> TResult:
        """Execute the use case"""
