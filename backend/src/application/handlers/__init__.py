"""
CQRS Handlers
=============

Command and Query handlers implementing the CQRS pattern.
"""

from .command_handlers import (
    AddInvestmentToPortfolioCommandHandler,
    CreateInvestmentCommandHandler,
    CreatePortfolioCommandHandler,
    GenerateSignalCommandHandler,
)
from .query_handlers import (
    AnalyzePortfolioQueryHandler,
    FindInvestmentsQueryHandler,
    GetInvestmentByIdQueryHandler,
    GetPortfolioByIdQueryHandler,
    GetUserPortfoliosQueryHandler,
)

__all__ = [
    # Command Handlers
    "CreateInvestmentCommandHandler",
    "CreatePortfolioCommandHandler",
    "AddInvestmentToPortfolioCommandHandler",
    "GenerateSignalCommandHandler",
    # Query Handlers
    "FindInvestmentsQueryHandler",
    "GetInvestmentByIdQueryHandler",
    "GetPortfolioByIdQueryHandler",
    "AnalyzePortfolioQueryHandler",
    "GetUserPortfoliosQueryHandler",
]
