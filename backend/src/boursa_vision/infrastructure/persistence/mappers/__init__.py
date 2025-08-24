"""
Unified Mappers Module - Complete Financial Schema Support
=========================================================

Provides consolidated access to all domain/persistence mappers
with complete financial schema support.
"""

from .investment_mapper import SimpleInvestmentMapper as InvestmentMapper
from .market_data_mapper import SimpleMarketDataMapper as MarketDataMapper
from .portfolio_mapper import CompletePortfolioMapper as PortfolioMapper
from .user_mapper import SimpleUserMapper as UserMapper

__all__ = [
    "InvestmentMapper",
    "MarketDataMapper",
    "PortfolioMapper",
    "UserMapper",
]
