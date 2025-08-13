"""
Queries for Investment and Portfolio Data
=========================================

Queries represent read operations that retrieve data without changing state.
Following CQRS principles, queries are separate from commands.
"""

# Investment-related queries
from .investment.find_investments_query import FindInvestmentsQuery
from .investment.get_investment_by_id_query import GetInvestmentByIdQuery
from .investment.get_investment_by_symbol_query import GetInvestmentBySymbolQuery
from .investment.get_market_data_query import GetMarketDataQuery

# Portfolio-related queries
from .portfolio.analyze_portfolio_query import AnalyzePortfolioQuery
from .portfolio.get_portfolio_by_id_query import GetPortfolioByIdQuery
from .portfolio.get_user_portfolios_query import GetUserPortfoliosQuery

# Signal-related queries
from .signal.get_signals_query import GetSignalsQuery
from .signal.get_technical_analysis_query import GetTechnicalAnalysisQuery

__all__ = [
    # Investment queries
    "FindInvestmentsQuery",
    "GetInvestmentByIdQuery",
    "GetInvestmentBySymbolQuery",
    "GetMarketDataQuery",
    # Portfolio queries
    "AnalyzePortfolioQuery",
    "GetPortfolioByIdQuery",
    "GetUserPortfoliosQuery",
    # Signal queries
    "GetSignalsQuery",
    "GetTechnicalAnalysisQuery",
]
