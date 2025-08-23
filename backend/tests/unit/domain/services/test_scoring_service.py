"""
Tests for Scoring Service - Domain Layer
========================================

Comprehensive tests for scoring service with strategies and protocols following DDD principles.
Tests scoring calculations, strategy pattern implementation, and metric weightings.
"""

from unittest.mock import Mock

import pytest

from boursa_vision.domain.services.scoring_service import (
    FundamentalScoringStrategy,
    Scorable,
    ScoringService,
    ScoringStrategy,
)

"""
Tests for Scoring Service - Domain Layer
========================================

Comprehensive tests for scoring service with strategies and protocols following DDD principles.
Tests scoring calculations, strategy pattern implementation, and metric weightings.
"""


class MockScorableInvestment:
    """Mock implementation of Scorable protocol for testing"""

    def __init__(
        self,
        pe_ratio_score: float = 50.0,
        pe_ratio_weight: float = 1.0,
        roe_score: float = 50.0,
        roe_weight: float = 1.0,
        revenue_growth_score: float = 50.0,
        revenue_growth_weight: float = 1.0,
        debt_to_equity_score: float = 50.0,
        debt_to_equity_weight: float = 1.0,
    ):
        self._pe_ratio = (pe_ratio_score, pe_ratio_weight)
        self._roe = (roe_score, roe_weight)
        self._revenue_growth = (revenue_growth_score, revenue_growth_weight)
        self._debt_to_equity = (debt_to_equity_score, debt_to_equity_weight)

    def _score_pe_ratio(self) -> tuple[float, float]:
        return self._pe_ratio

    def _score_roe(self) -> tuple[float, float]:
        return self._roe

    def _score_revenue_growth(self) -> tuple[float, float]:
        return self._revenue_growth

    def _score_debt_to_equity(self) -> tuple[float, float]:
        return self._debt_to_equity


class MockScoringStrategy(ScoringStrategy):
    """Mock scoring strategy for testing"""

    def __init__(self, score_to_return: float = 75.0):
        self.score_to_return = score_to_return
        self.calculate_score_calls = []

    def calculate_score(self, investment) -> float:
        self.calculate_score_calls.append(investment)
        return self.score_to_return


class TestScorable:
    """Tests for Scorable protocol"""

    def test_scorable_protocol_methods(self):
        """Test that Scorable protocol defines required methods"""
        # Verify protocol methods exist
        assert hasattr(Scorable, "_score_pe_ratio")
        assert hasattr(Scorable, "_score_roe")
        assert hasattr(Scorable, "_score_revenue_growth")
        assert hasattr(Scorable, "_score_debt_to_equity")

    def test_mock_scorable_implementation(self):
        """Test mock implementation implements Scorable correctly"""
        scorable = MockScorableInvestment(
            pe_ratio_score=80.0, pe_ratio_weight=0.5, roe_score=60.0, roe_weight=0.3
        )

        pe_result = scorable._score_pe_ratio()
        roe_result = scorable._score_roe()

        assert abs(pe_result[0] - 80.0) < 0.001
        assert abs(pe_result[1] - 0.5) < 0.001
        assert abs(roe_result[0] - 60.0) < 0.001
        assert abs(roe_result[1] - 0.3) < 0.001


class TestScoringStrategy:
    """Tests for ScoringStrategy abstract base class"""

    def test_scoring_strategy_is_abstract(self):
        """Test that ScoringStrategy is abstract and cannot be instantiated"""
        with pytest.raises(TypeError):
            ScoringStrategy()

    def test_mock_strategy_implementation(self):
        """Test mock strategy implementation"""
        strategy = MockScoringStrategy(score_to_return=85.0)
        mock_investment = MockScorableInvestment()

        score = strategy.calculate_score(mock_investment)

        assert abs(score - 85.0) < 0.001
        assert len(strategy.calculate_score_calls) == 1
        assert strategy.calculate_score_calls[0] is mock_investment


class TestFundamentalScoringStrategy:
    """Tests for FundamentalScoringStrategy implementation"""

    def setup_method(self):
        """Setup for each test method"""
        self.strategy = FundamentalScoringStrategy()

    def test_calculate_score_with_default_values(self):
        """Test scoring with default balanced values (50.0)"""
        scorable = MockScorableInvestment()  # All defaults to 50.0

        score = self.strategy.calculate_score(scorable)

        # Expected: (50*0.3 + 50*0.3 + 50*0.2 + 50*0.2) / 1.0 = 50.0
        assert abs(score - 50.0) < 0.001

    def test_calculate_score_with_excellent_metrics(self):
        """Test scoring with excellent financial metrics"""
        scorable = MockScorableInvestment(
            pe_ratio_score=90.0,  # Excellent P/E
            roe_score=95.0,  # Excellent ROE
            revenue_growth_score=88.0,  # Excellent growth
            debt_to_equity_score=85.0,  # Low debt
        )

        score = self.strategy.calculate_score(scorable)

        # Expected: (90*0.3 + 95*0.3 + 88*0.2 + 85*0.2) / 1.0 = 90.1
        expected = 90.0 * 0.3 + 95.0 * 0.3 + 88.0 * 0.2 + 85.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 90.1) < 0.001

    def test_calculate_score_with_poor_metrics(self):
        """Test scoring with poor financial metrics"""
        scorable = MockScorableInvestment(
            pe_ratio_score=20.0,  # Poor P/E
            roe_score=15.0,  # Poor ROE
            revenue_growth_score=25.0,  # Poor growth
            debt_to_equity_score=30.0,  # High debt
        )

        score = self.strategy.calculate_score(scorable)

        # Expected: (20*0.3 + 15*0.3 + 25*0.2 + 30*0.2) / 1.0 = 21.5
        expected = 20.0 * 0.3 + 15.0 * 0.3 + 25.0 * 0.2 + 30.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 21.5) < 0.001

    def test_calculate_score_with_mixed_metrics(self):
        """Test scoring with mixed financial metrics"""
        scorable = MockScorableInvestment(
            pe_ratio_score=70.0,  # Good P/E (weight 0.3)
            roe_score=40.0,  # Average ROE (weight 0.3)
            revenue_growth_score=80.0,  # Good growth (weight 0.2)
            debt_to_equity_score=60.0,  # Decent debt (weight 0.2)
        )

        score = self.strategy.calculate_score(scorable)

        # Expected: (70*0.3 + 40*0.3 + 80*0.2 + 60*0.2) / 1.0 = 61.0
        expected = 70.0 * 0.3 + 40.0 * 0.3 + 80.0 * 0.2 + 60.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 61.0) < 0.001

    def test_calculate_score_with_extreme_values_clamped(self):
        """Test that extreme values are clamped to 0-100 range"""
        scorable = MockScorableInvestment(
            pe_ratio_score=-50.0,  # Below 0, should be clamped to 0
            roe_score=150.0,  # Above 100, should be clamped to 100
            revenue_growth_score=25.0,
            debt_to_equity_score=75.0,
        )

        score = self.strategy.calculate_score(scorable)

        # Expected: (0*0.3 + 100*0.3 + 25*0.2 + 75*0.2) / 1.0 = 50.0
        expected = 0.0 * 0.3 + 100.0 * 0.3 + 25.0 * 0.2 + 75.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 50.0) < 0.001

    def test_calculate_score_boundary_values(self):
        """Test scoring with boundary values (0.0 and 100.0)"""
        scorable = MockScorableInvestment(
            pe_ratio_score=0.0,  # Minimum
            roe_score=100.0,  # Maximum
            revenue_growth_score=0.0,  # Minimum
            debt_to_equity_score=100.0,  # Maximum
        )

        score = self.strategy.calculate_score(scorable)

        # Expected: (0*0.3 + 100*0.3 + 0*0.2 + 100*0.2) / 1.0 = 50.0
        expected = 0.0 * 0.3 + 100.0 * 0.3 + 0.0 * 0.2 + 100.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 50.0) < 0.001

    def test_calculate_score_weights_distribution(self):
        """Test that weights are correctly distributed (P/E:30%, ROE:30%, Growth:20%, Debt:20%)"""
        # Test with score=100 for single metric, others=0
        test_cases = [
            # (metric_scores, expected_contribution)
            ((100.0, 0.0, 0.0, 0.0), 30.0),  # P/E only
            ((0.0, 100.0, 0.0, 0.0), 30.0),  # ROE only
            ((0.0, 0.0, 100.0, 0.0), 20.0),  # Revenue growth only
            ((0.0, 0.0, 0.0, 100.0), 20.0),  # Debt-to-equity only
        ]

        for (pe, roe, growth, debt), expected in test_cases:
            scorable = MockScorableInvestment(
                pe_ratio_score=pe,
                roe_score=roe,
                revenue_growth_score=growth,
                debt_to_equity_score=debt,
            )

            score = self.strategy.calculate_score(scorable)
            assert abs(score - expected) < 0.001, (
                f"Failed for scores ({pe}, {roe}, {growth}, {debt})"
            )

    def test_calculate_score_zero_total_weight_fallback(self):
        """Test fallback when total weight is zero (defensive test)"""
        scorable = MockScorableInvestment()
        score = self.strategy.calculate_score(scorable)

        # With normal implementation, this should never hit the fallback
        # But ensures score is valid
        assert isinstance(score, int | float)
        assert 0.0 <= score <= 100.0

    def test_calculate_score_perfect_scores(self):
        """Test with all perfect scores"""
        scorable = MockScorableInvestment(
            pe_ratio_score=100.0,
            roe_score=100.0,
            revenue_growth_score=100.0,
            debt_to_equity_score=100.0,
        )

        score = self.strategy.calculate_score(scorable)
        assert abs(score - 100.0) < 0.001

    def test_calculate_score_all_zero_scores(self):
        """Test with all zero scores"""
        scorable = MockScorableInvestment(
            pe_ratio_score=0.0,
            roe_score=0.0,
            revenue_growth_score=0.0,
            debt_to_equity_score=0.0,
        )

        score = self.strategy.calculate_score(scorable)
        assert abs(score - 0.0) < 0.001


class TestScoringService:
    """Tests for ScoringService orchestrator"""

    def test_init_with_strategy(self):
        """Test ScoringService initialization with strategy"""
        strategy = MockScoringStrategy(score_to_return=80.0)
        service = ScoringService(strategy)

        assert service.strategy is strategy

    def test_calculate_score_delegates_to_strategy(self):
        """Test that calculate_score delegates to the configured strategy"""
        strategy = MockScoringStrategy(score_to_return=75.5)
        service = ScoringService(strategy)
        scorable = MockScorableInvestment()

        score = service.calculate_score(scorable)

        assert abs(score - 75.5) < 0.001
        assert len(strategy.calculate_score_calls) == 1
        assert strategy.calculate_score_calls[0] is scorable

    def test_calculate_score_with_fundamental_strategy(self):
        """Test ScoringService integration with FundamentalScoringStrategy"""
        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)
        scorable = MockScorableInvestment(
            pe_ratio_score=80.0,
            roe_score=70.0,
            revenue_growth_score=60.0,
            debt_to_equity_score=90.0,
        )

        score = service.calculate_score(scorable)

        # Expected: (80*0.3 + 70*0.3 + 60*0.2 + 90*0.2) / 1.0 = 75.0
        expected = 80.0 * 0.3 + 70.0 * 0.3 + 60.0 * 0.2 + 90.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 75.0) < 0.001

    def test_calculate_score_multiple_calls(self):
        """Test multiple calls to calculate_score"""
        strategy = MockScoringStrategy(score_to_return=85.0)
        service = ScoringService(strategy)
        scorable1 = MockScorableInvestment()
        scorable2 = MockScorableInvestment()

        score1 = service.calculate_score(scorable1)
        score2 = service.calculate_score(scorable2)

        assert abs(score1 - 85.0) < 0.001
        assert abs(score2 - 85.0) < 0.001
        assert len(strategy.calculate_score_calls) == 2
        assert strategy.calculate_score_calls[0] is scorable1
        assert strategy.calculate_score_calls[1] is scorable2

    def test_strategy_can_be_changed(self):
        """Test that service strategy can be replaced"""
        initial_strategy = MockScoringStrategy(score_to_return=60.0)
        service = ScoringService(initial_strategy)
        scorable = MockScorableInvestment()

        # Test with initial strategy
        score1 = service.calculate_score(scorable)
        assert abs(score1 - 60.0) < 0.001

        # Change strategy
        new_strategy = MockScoringStrategy(score_to_return=90.0)
        service.strategy = new_strategy

        # Test with new strategy
        score2 = service.calculate_score(scorable)
        assert abs(score2 - 90.0) < 0.001

        # Verify both strategies were called appropriately
        assert len(initial_strategy.calculate_score_calls) == 1
        assert len(new_strategy.calculate_score_calls) == 1


class TestScoringServiceIntegration:
    """Integration tests for scoring service components"""

    def test_end_to_end_scoring_workflow(self):
        """Test complete scoring workflow from service to strategy"""
        # Setup
        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)

        # Create test investment with varied metrics
        investment = MockScorableInvestment(
            pe_ratio_score=85.0,  # Strong P/E
            roe_score=75.0,  # Good ROE
            revenue_growth_score=65.0,  # Decent growth
            debt_to_equity_score=80.0,  # Good debt management
        )

        # Execute scoring
        final_score = service.calculate_score(investment)

        # Verify result
        expected = 85.0 * 0.3 + 75.0 * 0.3 + 65.0 * 0.2 + 80.0 * 0.2
        assert abs(final_score - expected) < 0.001
        assert abs(final_score - 77.0) < 0.001
        assert 0.0 <= final_score <= 100.0

    def test_scoring_with_multiple_strategies(self):
        """Test service with different strategy implementations"""
        scorable = MockScorableInvestment(
            pe_ratio_score=70.0,
            roe_score=80.0,
            revenue_growth_score=60.0,
            debt_to_equity_score=75.0,
        )

        # Test with FundamentalScoringStrategy
        fundamental_strategy = FundamentalScoringStrategy()
        service = ScoringService(fundamental_strategy)
        fundamental_score = service.calculate_score(scorable)

        expected_fundamental = 70.0 * 0.3 + 80.0 * 0.3 + 60.0 * 0.2 + 75.0 * 0.2
        assert abs(fundamental_score - expected_fundamental) < 0.001
        assert abs(fundamental_score - 72.0) < 0.001

        # Test with mock strategy
        mock_strategy = MockScoringStrategy(score_to_return=95.0)
        service.strategy = mock_strategy
        mock_score = service.calculate_score(scorable)

        assert abs(mock_score - 95.0) < 0.001
        assert len(mock_strategy.calculate_score_calls) == 1

    def test_scoring_consistency(self):
        """Test that scoring is consistent for same inputs"""
        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)
        scorable = MockScorableInvestment(
            pe_ratio_score=60.0,
            roe_score=70.0,
            revenue_growth_score=55.0,
            debt_to_equity_score=65.0,
        )

        # Multiple calls should return same result
        scores = [service.calculate_score(scorable) for _ in range(5)]

        first_score = scores[0]
        for score in scores[1:]:
            assert abs(score - first_score) < 0.001

        # Calculate expected score: (60*0.3 + 70*0.3 + 55*0.2 + 65*0.2) = 64.0
        expected = 60.0 * 0.3 + 70.0 * 0.3 + 55.0 * 0.2 + 65.0 * 0.2
        assert abs(first_score - expected) < 0.001

    def test_extreme_scenario_handling(self):
        """Test service behavior with extreme scoring scenarios"""
        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)

        # Test with all zeros
        zero_scorable = MockScorableInvestment(
            pe_ratio_score=0.0,
            roe_score=0.0,
            revenue_growth_score=0.0,
            debt_to_equity_score=0.0,
        )
        zero_score = service.calculate_score(zero_scorable)
        assert abs(zero_score - 0.0) < 0.001

        # Test with all max values
        max_scorable = MockScorableInvestment(
            pe_ratio_score=100.0,
            roe_score=100.0,
            revenue_growth_score=100.0,
            debt_to_equity_score=100.0,
        )
        max_score = service.calculate_score(max_scorable)
        assert abs(max_score - 100.0) < 0.001

        # Test with extreme values that need clamping
        extreme_scorable = MockScorableInvestment(
            pe_ratio_score=200.0,  # Should clamp to 100
            roe_score=-50.0,  # Should clamp to 0
            revenue_growth_score=120.0,  # Should clamp to 100
            debt_to_equity_score=-10.0,  # Should clamp to 0
        )
        extreme_score = service.calculate_score(extreme_scorable)
        # Expected: (100*0.3 + 0*0.3 + 100*0.2 + 0*0.2) = 50.0
        assert abs(extreme_score - 50.0) < 0.001


class TestScoringServiceErrorHandling:
    """Tests for error handling and edge cases"""

    def test_scoring_service_requires_strategy(self):
        """Test that ScoringService requires a strategy parameter"""
        with pytest.raises(TypeError):
            ScoringService()  # Missing required strategy parameter

    def test_none_strategy_handling(self):
        """Test behavior with None strategy"""
        # ScoringService should accept None but may fail during usage
        try:
            service = ScoringService(None)
            scorable = MockScorableInvestment()
            # This should fail when trying to call None.calculate_score()
            with pytest.raises(AttributeError):
                service.calculate_score(scorable)
        except TypeError:
            # If the constructor itself raises TypeError, that's also acceptable
            pass

    def test_invalid_strategy_type(self):
        """Test behavior with invalid strategy type"""
        # ScoringService might accept invalid types but fail during usage
        try:
            service = ScoringService("not_a_strategy")
            scorable = MockScorableInvestment()
            # This should fail when trying to call string.calculate_score()
            with pytest.raises(AttributeError):
                service.calculate_score(scorable)
        except TypeError:
            # If the constructor itself raises TypeError, that's also acceptable
            pass

    def test_strategy_exception_propagation(self):
        """Test that strategy exceptions are properly propagated"""

        class FailingStrategy(ScoringStrategy):
            def calculate_score(self, investment):
                raise ValueError("Strategy calculation failed")

        strategy = FailingStrategy()
        service = ScoringService(strategy)
        scorable = MockScorableInvestment()

        with pytest.raises(ValueError, match="Strategy calculation failed"):
            service.calculate_score(scorable)


class TestScoringServiceWithMockInvestment:
    """Tests using Mock objects to simulate Investment entities"""

    def test_scoring_service_with_mock_investment(self):
        """Test ScoringService integration with mock Investment using standard Mock"""
        # Arrange
        mock_investment = Mock()
        mock_investment._score_pe_ratio.return_value = (75.0, 0.3)
        mock_investment._score_roe.return_value = (85.0, 0.3)
        mock_investment._score_revenue_growth.return_value = (65.0, 0.2)
        mock_investment._score_debt_to_equity.return_value = (80.0, 0.2)

        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)

        # Act
        score = service.calculate_score(mock_investment)

        # Assert
        expected = 75.0 * 0.3 + 85.0 * 0.3 + 65.0 * 0.2 + 80.0 * 0.2
        assert abs(score - expected) < 0.001
        assert abs(score - 77.0) < 0.001

    def test_scoring_different_performance_levels(self):
        """Test scoring with different investment performance levels"""
        strategy = FundamentalScoringStrategy()
        service = ScoringService(strategy)

        # Low performer
        low_performer = Mock()
        low_performer._score_pe_ratio.return_value = (30.0, 0.3)
        low_performer._score_roe.return_value = (40.0, 0.3)
        low_performer._score_revenue_growth.return_value = (25.0, 0.2)
        low_performer._score_debt_to_equity.return_value = (35.0, 0.2)

        # High performer
        high_performer = Mock()
        high_performer._score_pe_ratio.return_value = (90.0, 0.3)
        high_performer._score_roe.return_value = (95.0, 0.3)
        high_performer._score_revenue_growth.return_value = (85.0, 0.2)
        high_performer._score_debt_to_equity.return_value = (80.0, 0.2)

        # Act
        low_score = service.calculate_score(low_performer)
        high_score = service.calculate_score(high_performer)

        # Assert
        expected_low = 30.0 * 0.3 + 40.0 * 0.3 + 25.0 * 0.2 + 35.0 * 0.2
        expected_high = 90.0 * 0.3 + 95.0 * 0.3 + 85.0 * 0.2 + 80.0 * 0.2

        assert abs(low_score - expected_low) < 0.001
        assert abs(high_score - expected_high) < 0.001
        assert abs(low_score - 33.0) < 0.001
        assert abs(high_score - 88.5) < 0.001
        assert high_score > low_score
