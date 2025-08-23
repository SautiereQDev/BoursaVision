"""
Command Handlers Implementation
==============================

Handlers for processing commands following CQRS pattern.
Each handler is responsible for executing a specific command.
"""

from typing import Any
from uuid import UUID

from ..commands import (
    AddInvestmentToPortfolioCommand,
    CreateInvestmentCommand,
    CreatePortfolioCommand,
    GenerateSignalCommand,
)
from ..common import ICommandHandler


class CreateInvestmentCommandHandler(ICommandHandler[CreateInvestmentCommand, UUID]):
    """Handler for creating new investments"""

    def __init__(self, investment_repository, unit_of_work):
        self._investment_repository = investment_repository
        self._unit_of_work = unit_of_work

    async def handle(self, command: CreateInvestmentCommand) -> UUID:
        """
        Handle the create investment command.

        Args:
            command: Create investment command

        Returns:
            ID of the created investment
        """
        async with self._unit_of_work:
            # Create investment entity using factory
            from uuid import uuid4

            investment_id = uuid4()

            # This would use domain factory
            investment_data = {
                "id": investment_id,
                "symbol": command.symbol,
                "name": command.name,
                "investment_type": command.investment_type,
                "sector": command.sector,
                "market_cap": command.market_cap,
                "currency": command.currency,
                "exchange": command.exchange,
                "isin": command.isin,
            }

            # Save to repository
            await self._investment_repository.save(investment_data)

            # Commit transaction
            await self._unit_of_work.commit()

            return investment_id


class CreatePortfolioCommandHandler(ICommandHandler[CreatePortfolioCommand, UUID]):
    """Handler for creating new portfolios"""

    def __init__(self, portfolio_repository, user_repository, unit_of_work):
        self._portfolio_repository = portfolio_repository
        self._user_repository = user_repository
        self._unit_of_work = unit_of_work

    async def handle(self, command: CreatePortfolioCommand) -> UUID:
        """
        Handle the create portfolio command.

        Args:
            command: Create portfolio command

        Returns:
            ID of the created portfolio
        """
        async with self._unit_of_work:
            # Verify user exists
            user = await self._user_repository.find_by_id(command.user_id)
            if not user:
                raise ValueError(f"User {command.user_id} not found")

            # Create portfolio entity
            from uuid import uuid4

            portfolio_id = uuid4()

            portfolio_data = {
                "id": portfolio_id,
                "user_id": command.user_id,
                "name": command.name,
                "description": command.description,
                "cash_balance": {
                    "amount": command.initial_cash_amount,
                    "currency": command.currency,
                },
            }

            # Save to repository
            await self._portfolio_repository.save(portfolio_data)

            # Commit transaction
            await self._unit_of_work.commit()

            return portfolio_id


class AddInvestmentToPortfolioCommandHandler(
    ICommandHandler[AddInvestmentToPortfolioCommand, bool]
):
    """Handler for adding investments to portfolios"""

    def __init__(self, portfolio_repository, investment_repository, unit_of_work):
        self._portfolio_repository = portfolio_repository
        self._investment_repository = investment_repository
        self._unit_of_work = unit_of_work

    async def handle(self, command: AddInvestmentToPortfolioCommand) -> bool:
        """
        Handle the add investment to portfolio command.

        Args:
            command: Add investment command

        Returns:
            True if successful
        """
        async with self._unit_of_work:
            # Get portfolio
            portfolio = await self._portfolio_repository.find_by_id(
                command.portfolio_id
            )
            if not portfolio:
                raise ValueError(f"Portfolio {command.portfolio_id} not found")

            # Get investment
            investment = await self._investment_repository.find_by_id(
                command.investment_id
            )
            if not investment:
                raise ValueError(f"Investment {command.investment_id} not found")

            # Calculate total cost
            total_cost = command.quantity * command.purchase_price

            # Check if sufficient cash
            if portfolio.cash_balance.amount < total_cost:
                raise ValueError("Insufficient cash balance")

            # Add investment to portfolio (domain logic)
            portfolio.add_investment(
                investment, command.quantity, command.purchase_price
            )

            # Save updated portfolio
            await self._portfolio_repository.save(portfolio)

            # Commit transaction
            await self._unit_of_work.commit()

            return True


class GenerateSignalCommandHandler(
    ICommandHandler[GenerateSignalCommand, dict[str, Any]]
):
    """Handler for generating trading signals"""

    def __init__(self, signal_generator):
        self._signal_generator = signal_generator

    async def handle(self, command: GenerateSignalCommand) -> dict[str, Any]:
        """
        Handle the generate signal command.

        Args:
            command: Generate signal command

        Returns:
            Generated signal data
        """
        # Get investment symbol
        # This would typically get the symbol from the investment repository
        symbol = "PLACEHOLDER"  # Would be fetched from investment

        # Generate signal
        signal = await self._signal_generator.generate_signal(symbol)

        return {
            "investment_id": command.investment_id,
            "signal": signal,
            "generated_at": signal.timestamp,
        }
