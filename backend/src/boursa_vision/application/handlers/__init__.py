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
    "AddInvestmentToPortfolioCommandHandler",
    "AnalyzePortfolioQueryHandler",
    # Command Handlers
    "CreateInvestmentCommandHandler",
    "CreatePortfolioCommandHandler",
    # Query Handlers
    "FindInvestmentsQueryHandler",
    "GenerateSignalCommandHandler",
    "GetInvestmentByIdQueryHandler",
    "GetPortfolioByIdQueryHandler",
    "GetUserPortfoliosQueryHandler",
]
