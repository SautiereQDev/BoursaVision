"""
Scoring Service Implementation
=============================

Provides scoring strategies for investments and other scorable entities.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from boursa_vision.domain.entities.investment import Investment


class Scorable(Protocol):
    """
    Protocol for objects that can be scored by the ScoringService.
    """

    def _score_pe_ratio(self) -> tuple[float, float]:
        """
        Placeholder for scoring P/E ratio. Must be implemented by concrete classes.
        """
        ...

    def _score_roe(self) -> tuple[float, float]:
        """
        Placeholder for scoring ROE. Must be implemented by concrete classes.
        """
        ...

    def _score_revenue_growth(self) -> tuple[float, float]:
        """
        Placeholder for scoring revenue growth. Must be implemented by concrete classes.
        """
        ...

    def _score_debt_to_equity(self) -> tuple[float, float]:
        """
        Placeholder for scoring debt-to-equity ratio. Must be implemented by concrete classes.
        """
        ...


class ScoringStrategy(ABC):
    """
    Abstract base class for scoring strategies.
    """

    @abstractmethod
    def calculate_score(self, investment: Investment) -> float:
        """
        Calculate the score for the given investment.

        Args:
            investment (Investment): The investment to calculate the score for.

        Returns:
            float: The calculated score.
        """
        pass


class FundamentalScoringStrategy(ScoringStrategy):
    """
    Strategy for calculating fundamental scores.
    """

    def calculate_score(
        self, investment: Scorable
    ) -> float:  # pylint: disable=protected-access
        """
        Calculate the fundamental score for a given scorable entity.

        Args:
            scorable (Scorable): The scorable entity (e.g., an investment).

        Returns:
            float: The calculated fundamental score.
        """
        total_weight = 0.0
        weighted_sum = 0.0

        # Adjusted weights for metrics
        for score, weight in (
            (investment._score_pe_ratio()[0], 0.3),  # P/E ratio weight
            (investment._score_roe()[0], 0.3),  # ROE weight
            (investment._score_revenue_growth()[0], 0.2),  # Revenue growth weight
            (investment._score_debt_to_equity()[0], 0.2),  # Debt-to-equity weight
        ):
            if weight > 0:
                scaled_score = max(0.0, min(100.0, score))
                weighted_sum += scaled_score * weight
                total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        return 50.0


class ScoringService:
    """Service for calculating scores."""

    def __init__(self, strategy: ScoringStrategy):
        """
        Initialize the scoring service with a specific strategy.

        Args:
            strategy (ScoringStrategy): The scoring strategy to use.
        """
        self.strategy = strategy

    def calculate_score(self, scorable: Scorable) -> float:
        """
        Calculate the score for a given scorable entity using the configured strategy.

        Args:
            scorable (Scorable): The scorable entity (e.g., an investment).

        Returns:
            float: The calculated score.
        """
        # Delegate score calculation to the strategy.
        return self.strategy.calculate_score(scorable)
