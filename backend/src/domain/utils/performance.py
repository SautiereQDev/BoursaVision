"""
Performance utility functions for domain services.
"""
from typing import List


def calculate_max_drawdown(returns: List[float]) -> float:
    """Calculate maximum drawdown from a list of returns."""
    if not returns:
        return 0.0

    cumulative = [1.0]
    for ret in returns:
        cumulative.append(cumulative[-1] * (1 + ret))

    max_drawdown = 0.0
    peak = cumulative[0]

    for value in cumulative:
        if value > peak:
            peak = value
        else:
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown
