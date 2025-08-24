"""
Factory patterns for test data generation.

This module provides factory classes for creating test entities
with realistic data and proper relationships, following the
Factory pattern for maintainable test data management.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from faker import Faker

from boursa_vision.domain.entities.investment import Investment
from boursa_vision.domain.entities.portfolio import Portfolio
from boursa_vision.domain.entities.user import User
from boursa_vision.domain.value_objects.money import Money
from boursa_vision.domain.value_objects.price import Price


# Initialize Faker for realistic test data
fake = Faker()


class UserFactory:
    """Factory for creating User entities with realistic data."""
    
    @staticmethod
    def create(
        user_id: UUID | None = None,
        email: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        is_active: bool = True,
        created_at: datetime | None = None,
        **kwargs
    ) -> User:
        """
        Create a User entity with sensible defaults.
        
        Args:
            user_id: User UUID, auto-generated if not provided
            email: User email, fake email if not provided
            username: Username, fake username if not provided
            first_name: First name, fake first name if not provided
            last_name: Last name, fake last name if not provided
            is_active: Active status, defaults to True
            created_at: Creation timestamp, defaults to now
            **kwargs: Additional user attributes
            
        Returns:
            User entity with provided or generated data
        """
        return User(
            id=user_id or uuid4(),
            email=email or fake.email(),
            username=username or fake.user_name(),
            first_name=first_name or fake.first_name(),
            last_name=last_name or fake.last_name(),
            is_active=is_active,
            created_at=created_at or datetime.now(UTC),
            **kwargs
        )
    
    @staticmethod
    def create_batch(count: int, **common_attrs) -> list[User]:
        """Create multiple users with common attributes."""
        return [
            UserFactory.create(**common_attrs)
            for _ in range(count)
        ]


class PortfolioFactory:
    """Factory for creating Portfolio entities with realistic data."""
    
    @staticmethod
    def create(
        portfolio_id: UUID | None = None,
        user_id: UUID | None = None,
        name: str | None = None,
        description: str | None = None,
        created_at: datetime | None = None,
        **kwargs
    ) -> Portfolio:
        """
        Create a Portfolio entity with sensible defaults.
        
        Args:
            portfolio_id: Portfolio UUID, auto-generated if not provided
            user_id: Owner user UUID, auto-generated if not provided
            name: Portfolio name, fake company name if not provided
            description: Portfolio description, fake text if not provided
            created_at: Creation timestamp, defaults to now
            **kwargs: Additional portfolio attributes
            
        Returns:
            Portfolio entity with provided or generated data
        """
        return Portfolio(
            id=portfolio_id or uuid4(),
            user_id=user_id or uuid4(),
            name=name or f"{fake.company()} Portfolio",
            description=description or fake.text(max_nb_chars=200),
            created_at=created_at or datetime.now(UTC),
            **kwargs
        )
    
    @staticmethod
    def create_with_user(
        user: User | None = None,
        **portfolio_attrs
    ) -> tuple[User, Portfolio]:
        """Create a portfolio with its associated user."""
        if user is None:
            user = UserFactory.create()
        
        portfolio = PortfolioFactory.create(
            user_id=user.id,
            **portfolio_attrs
        )
        
        return user, portfolio


class InvestmentFactory:
    """Factory for creating Investment entities with realistic data."""
    
    @staticmethod
    def create(
        investment_id: UUID | None = None,
        portfolio_id: UUID | None = None,
        symbol: str | None = None,
        quantity: int | None = None,
        purchase_price: Money | None = None,
        purchase_date: datetime | None = None,
        investment_type: str = "STOCK",
        **kwargs
    ) -> Investment:
        """
        Create an Investment entity with sensible defaults.
        
        Args:
            investment_id: Investment UUID, auto-generated if not provided
            portfolio_id: Portfolio UUID, auto-generated if not provided
            symbol: Stock symbol, random symbol if not provided
            quantity: Number of shares, random if not provided
            purchase_price: Purchase price, random if not provided
            purchase_date: Purchase date, recent date if not provided
            investment_type: Type of investment, defaults to STOCK
            **kwargs: Additional investment attributes
            
        Returns:
            Investment entity with provided or generated data
        """
        # Common stock symbols for realistic data
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        
        return Investment(
            id=investment_id or uuid4(),
            portfolio_id=portfolio_id or uuid4(),
            symbol=symbol or fake.random_element(symbols),
            quantity=quantity or fake.random_int(min=1, max=1000),
            purchase_price=purchase_price or Money(
                amount=Decimal(str(fake.random_int(min=10, max=500))),
                currency="USD"
            ),
            purchase_date=purchase_date or fake.date_time_between(
                start_date="-2y", 
                end_date="now",
                tzinfo=UTC
            ),
            investment_type=investment_type,
            **kwargs
        )
    
    @staticmethod
    def create_batch(
        count: int,
        portfolio_id: UUID | None = None,
        **common_attrs
    ) -> list[Investment]:
        """Create multiple investments for a portfolio."""
        portfolio_uuid = portfolio_id or uuid4()
        
        return [
            InvestmentFactory.create(
                portfolio_id=portfolio_uuid,
                **common_attrs
            )
            for _ in range(count)
        ]
    
    @staticmethod
    def create_with_portfolio(
        portfolio: Portfolio | None = None,
        **investment_attrs
    ) -> tuple[Portfolio, Investment]:
        """Create an investment with its associated portfolio."""
        if portfolio is None:
            portfolio = PortfolioFactory.create()
        
        investment = InvestmentFactory.create(
            portfolio_id=portfolio.id,
            **investment_attrs
        )
        
        return portfolio, investment


class MarketDataFactory:
    """Factory for creating market data entities with realistic data."""
    
    @staticmethod
    def create_stock_price(
        symbol: str | None = None,
        price: Decimal | None = None,
        volume: int | None = None,
        timestamp: datetime | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """
        Create market data for a stock.
        
        Args:
            symbol: Stock symbol, random if not provided
            price: Stock price, random if not provided
            volume: Trading volume, random if not provided
            timestamp: Data timestamp, now if not provided
            **kwargs: Additional market data attributes
            
        Returns:
            Dictionary representing market data
        """
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        
        return {
            "symbol": symbol or fake.random_element(symbols),
            "price": price or Decimal(str(fake.random_int(min=10, max=500))),
            "volume": volume or fake.random_int(min=100000, max=50000000),
            "timestamp": timestamp or datetime.now(UTC),
            "change": Decimal(str(fake.random_int(min=-50, max=50) / 10)),
            "change_percent": fake.random_int(min=-10, max=10) / 100,
            "market_cap": fake.random_int(min=1000000000, max=3000000000000),
            "pe_ratio": fake.random_int(min=5, max=50),
            **kwargs
        }
    
    @staticmethod
    def create_historical_data(
        symbol: str | None = None,
        days: int = 30
    ) -> list[dict[str, Any]]:
        """Create historical price data for a symbol."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
        target_symbol = symbol or fake.random_element(symbols)
        
        base_price = fake.random_int(min=50, max=300)
        historical_data = []
        
        for i in range(days):
            # Simulate realistic price movement
            price_change = fake.random_int(min=-5, max=5) / 100
            price = base_price * (1 + price_change)
            
            historical_data.append({
                "symbol": target_symbol,
                "date": fake.date_between(start_date=f"-{days-i}d", end_date=f"-{days-i-1}d"),
                "open": price * fake.random_int(min=995, max=1005) / 1000,
                "high": price * fake.random_int(min=1000, max=1020) / 1000,
                "low": price * fake.random_int(min=980, max=1000) / 1000,
                "close": price,
                "volume": fake.random_int(min=100000, max=50000000),
            })
            
            base_price = price  # Use current price as next base
        
        return historical_data


class CompletePortfolioFactory:
    """
    Factory for creating complete portfolio scenarios with users,
    portfolios, investments, and market data for integration testing.
    """
    
    @staticmethod
    def create_scenario(
        scenario_name: str = "balanced_portfolio",
        user_attrs: dict[str, Any] | None = None,
        portfolio_attrs: dict[str, Any] | None = None,
        investment_count: int = 5
    ) -> dict[str, Any]:
        """
        Create a complete testing scenario.
        
        Args:
            scenario_name: Type of scenario to create
            user_attrs: Custom user attributes
            portfolio_attrs: Custom portfolio attributes
            investment_count: Number of investments to create
            
        Returns:
            Dictionary containing all created entities
        """
        # Create user
        user = UserFactory.create(**(user_attrs or {}))
        
        # Create portfolio
        portfolio = PortfolioFactory.create(
            user_id=user.id,
            **(portfolio_attrs or {})
        )
        
        # Create investments based on scenario
        if scenario_name == "balanced_portfolio":
            investments = [
                InvestmentFactory.create(
                    portfolio_id=portfolio.id,
                    symbol="AAPL",
                    quantity=100,
                    purchase_price=Money(Decimal("150.00"), "USD")
                ),
                InvestmentFactory.create(
                    portfolio_id=portfolio.id,
                    symbol="GOOGL",
                    quantity=50,
                    purchase_price=Money(Decimal("2800.00"), "USD")
                ),
                InvestmentFactory.create(
                    portfolio_id=portfolio.id,
                    symbol="JPM",
                    quantity=200,
                    purchase_price=Money(Decimal("155.00"), "USD")
                ),
            ]
        elif scenario_name == "tech_heavy":
            tech_symbols = ["AAPL", "GOOGL", "MSFT", "NVDA", "META"]
            investments = [
                InvestmentFactory.create(
                    portfolio_id=portfolio.id,
                    symbol=symbol,
                    quantity=fake.random_int(min=10, max=200)
                )
                for symbol in tech_symbols[:investment_count]
            ]
        else:
            # Default random investments
            investments = InvestmentFactory.create_batch(
                investment_count,
                portfolio_id=portfolio.id
            )
        
        # Create market data for all symbols
        symbols = {inv.symbol for inv in investments}
        market_data = {
            symbol: MarketDataFactory.create_stock_price(symbol=symbol)
            for symbol in symbols
        }
        
        return {
            "user": user,
            "portfolio": portfolio,
            "investments": investments,
            "market_data": market_data,
            "scenario": scenario_name
        }
    
    @staticmethod
    def create_multiple_portfolios(
        user: User | None = None,
        portfolio_count: int = 3
    ) -> dict[str, Any]:
        """Create a user with multiple portfolios and investments."""
        if user is None:
            user = UserFactory.create()
        
        portfolios = []
        all_investments = []
        all_market_data = {}
        
        for i in range(portfolio_count):
            portfolio = PortfolioFactory.create(
                user_id=user.id,
                name=f"Portfolio {i+1}"
            )
            
            investments = InvestmentFactory.create_batch(
                fake.random_int(min=2, max=8),
                portfolio_id=portfolio.id
            )
            
            portfolios.append(portfolio)
            all_investments.extend(investments)
            
            # Add market data for new symbols
            symbols = {inv.symbol for inv in investments}
            for symbol in symbols:
                if symbol not in all_market_data:
                    all_market_data[symbol] = MarketDataFactory.create_stock_price(
                        symbol=symbol
                    )
        
        return {
            "user": user,
            "portfolios": portfolios,
            "investments": all_investments,
            "market_data": all_market_data,
            "scenario": "multiple_portfolios"
        }
