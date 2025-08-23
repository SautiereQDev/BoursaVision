"""
Commands for Investment Management
=================================

Commands represent write operations that change the state of the system.
Following CQRS principles, commands are separate from queries.
"""

from .investment.create_investment_command import CreateInvestmentCommand
from .investment.update_investment_price_command import UpdateInvestmentPriceCommand
from .portfolio.add_investment_to_portfolio_command import (
    AddInvestmentToPortfolioCommand,
)
from .portfolio.create_portfolio_command import CreatePortfolioCommand
from .portfolio.remove_investment_from_portfolio_command import (
    RemoveInvestmentFromPortfolioCommand,
)
from .portfolio.update_portfolio_command import UpdatePortfolioCommand
from .signal.generate_signal_command import GenerateSignalCommand

__all__ = [
    "AddInvestmentToPortfolioCommand",
    "CreateInvestmentCommand",
    "CreatePortfolioCommand",
    "GenerateSignalCommand",
    "RemoveInvestmentFromPortfolioCommand",
    "UpdateInvestmentPriceCommand",
    "UpdatePortfolioCommand",
]
