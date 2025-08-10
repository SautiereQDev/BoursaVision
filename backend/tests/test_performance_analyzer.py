"""
Tests for PerformanceAnalyzerService (domain/services/performance_analyzer.py)
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from src.domain.entities.investment import (
    Investment,
    InvestmentSector,
    InvestmentType,
    MarketCap,
)
from src.domain.entities.portfolio import PerformanceMetrics, Portfolio, Position
from src.domain.services.performance_analyzer import PerformanceAnalyzerService
from src.domain.value_objects.money import Currency, Money


def make_portfolio_and_positions():
    portfolio = Portfolio.create(
        user_id="user-1",
        name="Test Portfolio",
        base_currency=Currency.USD.value,
        initial_cash=Money(Decimal("10000.00"), Currency.USD),
    )
    investment = Investment.create(
        symbol="AAPL",
        name="Apple Inc.",
        investment_type=InvestmentType.STOCK,
        sector=InvestmentSector.TECHNOLOGY,
        market_cap=MarketCap.MEGA,
        currency=Currency.USD,
        exchange="NASDAQ",
    )
    position = Position(
        symbol="AAPL",
        quantity=10,
        average_price=Money(Decimal("150.00"), Currency.USD),
        first_purchase_date=datetime.now(timezone.utc) - timedelta(days=365),
        last_update=datetime.now(timezone.utc),
    )
    return portfolio, [position], {"AAPL": investment}


def test_calculate_portfolio_performance_basic():
    portfolio, positions, _ = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    current_prices = {"AAPL": Money(Decimal("160.00"), Currency.USD)}
    historical_prices = {"AAPL": [Money(Decimal("150.00"), Currency.USD)] * 30}
    metrics = analyzer.calculate_portfolio_performance(
        portfolio, positions, current_prices, historical_prices
    )
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.total_value.amount > 0
    assert metrics.daily_return is not None
    assert metrics.annual_return is not None
    assert metrics.volatility is not None
    assert metrics.sharpe_ratio is not None
    assert metrics.max_drawdown is not None
    assert metrics.beta is not None


def test_calculate_portfolio_performance_with_benchmark():
    portfolio, positions, _ = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    current_prices = {"AAPL": Money(Decimal("160.00"), Currency.USD)}
    historical_prices = {"AAPL": [Money(Decimal("150.00"), Currency.USD)] * 30}
    benchmark_returns = [0.01] * 30
    metrics = analyzer.calculate_portfolio_performance(
        portfolio,
        positions,
        current_prices,
        historical_prices,
        benchmark_returns=benchmark_returns,
    )
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.beta is not None


def test_calculate_portfolio_performance_empty_positions():
    portfolio, _, _ = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    current_prices = {}
    historical_prices = {}
    metrics = analyzer.calculate_portfolio_performance(
        portfolio, [], current_prices, historical_prices
    )
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.total_value.amount >= 0


def test_calculate_position_performance_basic():
    portfolio, positions, _ = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    position = positions[0]
    current_price = Money(Decimal("160.00"), Currency.USD)
    historical_prices = [Money(Decimal("150.00"), Currency.USD)] * 30
    perf = analyzer.calculate_position_performance(
        position, current_price, historical_prices
    )
    assert isinstance(perf, dict)
    assert "unrealized_pnl" in perf
    assert "annual_return" in perf
    assert perf["market_value"] > 0


def test_calculate_risk_adjusted_metrics_empty():
    analyzer = PerformanceAnalyzerService()
    metrics = analyzer.calculate_risk_adjusted_metrics([])
    assert metrics.sharpe_ratio == 0.0
    assert metrics.sortino_ratio == 0.0


def test_calculate_risk_adjusted_metrics_full():
    analyzer = PerformanceAnalyzerService()
    returns = [0.01, 0.02, -0.01, 0.03, 0.00]
    benchmark = [0.01, 0.01, 0.00, 0.02, 0.01]
    metrics = analyzer.calculate_risk_adjusted_metrics(returns, benchmark)
    assert isinstance(metrics.sharpe_ratio, float)
    assert isinstance(metrics.treynor_ratio, float)
    assert isinstance(metrics.jensen_alpha, float)


def test_compare_with_benchmark_empty():
    analyzer = PerformanceAnalyzerService()
    comp = analyzer.compare_with_benchmark([], [])
    assert comp.portfolio_return == 0.0
    assert comp.benchmark_return == 0.0


def test_compare_with_benchmark_full():
    analyzer = PerformanceAnalyzerService()
    returns = [0.01, 0.02, -0.01, 0.03, 0.00]
    benchmark = [0.01, 0.01, 0.00, 0.02, 0.01]
    comp = analyzer.compare_with_benchmark(returns, benchmark)
    assert isinstance(comp.alpha, float)
    assert isinstance(comp.tracking_error, float)


def test_calculate_attribution_analysis():
    portfolio, positions, investments = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    current_prices = {"AAPL": Money(Decimal("160.00"), Currency.USD)}
    historical_prices = {"AAPL": [Money(Decimal("150.00"), Currency.USD)] * 30}
    result = analyzer.calculate_attribution_analysis(
        positions, investments, current_prices, historical_prices
    )
    assert "assets" in result
    assert "sectors" in result
    assert "AAPL" in result["assets"]


def test_suggest_rebalancing_equal_weight():
    portfolio, positions, investments = make_portfolio_and_positions()
    analyzer = PerformanceAnalyzerService()
    current_prices = {"AAPL": Money(Decimal("160.00"), Currency.USD)}
    suggestions = analyzer.suggest_rebalancing(
        portfolio, positions, investments, current_prices
    )
    assert isinstance(suggestions, list)
