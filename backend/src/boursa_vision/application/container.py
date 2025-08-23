"""Application Container for Dependency Injection."""

from dataclasses import dataclass
from typing import Any, Protocol


class ApplicationContainerProtocol(Protocol):
    """Protocol for application container."""

    def get_technical_analyzer(self) -> Any: ...

    def get_signal_generator(self) -> Any: ...


@dataclass
class ApplicationContainerDependencies:
    """Dependencies for application container."""

    investment_repository: Any
    market_data_repository: Any
    scoring_service: Any


class ApplicationContainer:
    """Main application container for dependency injection."""

    def __init__(self, dependencies: ApplicationContainerDependencies) -> None:
        """Initialize container with dependencies."""
        self._deps = dependencies
        self._technical_analyzer: Any = None
        self._signal_generator: Any = None

    def get_technical_analyzer(self) -> Any:
        """Get technical analyzer service."""
        if self._technical_analyzer is None:
            from .services import TechnicalAnalyzer

            self._technical_analyzer = TechnicalAnalyzer(
                investment_repository=self._deps.investment_repository,
                market_data_repository=self._deps.market_data_repository,
                scoring_service=self._deps.scoring_service,
            )
        return self._technical_analyzer

    def get_signal_generator(self) -> Any:
        """Get signal generator service."""
        if self._signal_generator is None:
            from .services import SignalGenerator

            self._signal_generator = SignalGenerator(
                technical_analyzer=self.get_technical_analyzer()
            )
        return self._signal_generator
