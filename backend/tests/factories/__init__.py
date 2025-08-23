"""
Factory classes for creating test data
=====================================

Factory classes using factory_boy pour créer des instances de test
cohérentes et réalistes des entités du domaine.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import factory
from faker import Faker

from boursa_vision.domain.entities.investment import (
    Investment,
    InvestmentSector,
    InvestmentType,
    MarketCap,
)
from boursa_vision.domain.entities.portfolio import Portfolio, Position
from boursa_vision.domain.entities.user import User, UserRole
from boursa_vision.domain.value_objects.money import Currency, Money
from boursa_vision.infrastructure.persistence.models.investment import InvestmentModel
from boursa_vision.infrastructure.persistence.models.portfolios import (
    Portfolio as PortfolioModel,
)

# SQLAlchemy models imports
from boursa_vision.infrastructure.persistence.models.users import User as UserModel

fake = Faker()

# ================================================================
# Value Objects Factories
# ================================================================


class MoneyFactory(factory.Factory):
    """Factory for Money value objects."""

    class Meta:
        model = Money

    amount = factory.LazyFunction(
        lambda: Decimal(
            str(fake.pyfloat(min_value=0.01, max_value=10000.0, right_digits=2))
        )
    )
    currency = factory.Iterator([Currency.USD, Currency.EUR, Currency.GBP])


class CurrencyFactory(factory.Factory):
    """Factory for Currency enum."""

    class Meta:
        model = Currency

    # Return random currency
    currency = factory.Iterator(
        [
            Currency.USD,
            Currency.EUR,
            Currency.GBP,
            Currency.CAD,
            Currency.JPY,
            Currency.CHF,
            Currency.AUD,
        ]
    )


# ================================================================
# Domain Entities Factories
# ================================================================


class InvestmentFactory(factory.Factory):
    """Factory for Investment entities."""

    class Meta:
        model = Investment

    # Utilise la méthode create au lieu du constructeur direct
    symbol = factory.LazyFunction(
        lambda: fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )
    name = factory.Faker("company")
    investment_type = factory.Iterator(list(InvestmentType))
    sector = factory.Iterator(list(InvestmentSector))
    market_cap = factory.Iterator(list(MarketCap))
    exchange = factory.Faker(
        "random_element", elements=["NYSE", "NASDAQ", "LSE", "TSE", "EURONEXT"]
    )
    currency = factory.Iterator([Currency.USD, Currency.EUR, Currency.GBP])
    isin = factory.LazyFunction(
        lambda: f"{fake.country_code(representation='alpha-2')}{fake.random_int(min=100000000, max=999999999)}{fake.random_int(min=0, max=9)}"
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use Investment.create method."""
        # Supprimer les clés non supportées
        kwargs.pop("current_price", None)
        kwargs.pop("description", None)
        kwargs.pop("id", None)

        return model_class.create(**kwargs)

    @classmethod
    def create_apple(cls):
        """Create Apple stock for consistent testing."""
        return Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD,
        )

    @classmethod
    def create_microsoft(cls):
        """Create Microsoft stock for consistent testing."""
        return Investment.create(
            symbol="MSFT",
            name="Microsoft Corporation",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD,
        )


class PositionFactory(factory.Factory):
    """Factory for Position value objects."""

    class Meta:
        model = Position

    symbol = factory.LazyFunction(
        lambda: fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )
    quantity = factory.Faker("random_int", min=1, max=1000)
    average_price = factory.SubFactory(MoneyFactory)
    first_purchase_date = factory.LazyFunction(
        lambda: fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.utc
        )
    )
    last_update = factory.LazyFunction(lambda: datetime.now(timezone.utc))

    @classmethod
    def create_apple_position(cls, quantity: int = 100):
        """Create Apple position for testing."""
        return cls.create(
            symbol="AAPL",
            quantity=quantity,
            average_price=MoneyFactory.create(
                amount=Decimal("145.00"), currency=Currency.USD
            ),
        )


class UserFactory(factory.Factory):
    """Factory for User entities."""

    class Meta:
        model = User

    email = factory.Faker("email")
    username = factory.Faker("user_name")
    full_name = factory.Faker("name")
    role = factory.Iterator(list(UserRole))
    is_active = True
    is_verified = True
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.utc
        )
    )
    last_login_at = factory.LazyFunction(
        lambda: fake.date_time_between(
            start_date="-30d", end_date="now", tzinfo=timezone.utc
        )
    )

    @classmethod
    def create_test_user(cls):
        """Create consistent test user."""
        return cls.create(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.TRADER,
        )

    @classmethod
    def create_admin_user(cls):
        """Create admin test user."""
        return cls.create(
            email="admin@example.com",
            username="admin",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )


class PortfolioFactory(factory.Factory):
    """Factory for Portfolio entities."""

    class Meta:
        model = Portfolio

    # These will be used in Portfolio.create()
    name = factory.Faker("catch_phrase")
    description = factory.Faker("sentence", nb_words=10)
    base_currency = factory.Iterator([Currency.USD, Currency.EUR, Currency.GBP])
    initial_cash = factory.SubFactory(MoneyFactory)
    user_id = factory.LazyFunction(uuid4)

    @classmethod
    def create_sample_portfolio(cls, user_id=None):
        """Create sample portfolio with consistent data."""
        if user_id is None:
            user_id = uuid4()

        return Portfolio.create(
            user_id=user_id,
            name="Sample Investment Portfolio",
            base_currency=Currency.USD,
            initial_cash=Money(Decimal("10000.00"), Currency.USD),
        )

    @classmethod
    def create_with_positions(cls, user_id=None, num_positions: int = 3):
        """Create portfolio with positions."""
        portfolio = cls.create_sample_portfolio(user_id)

        # Add some positions
        positions = [
            PositionFactory.create_apple_position(quantity=100),
            PositionFactory.create(
                symbol="GOOGL",
                quantity=50,
                average_price=Money(Decimal("2500.00"), Currency.USD),
            ),
            PositionFactory.create(
                symbol="MSFT",
                quantity=75,
                average_price=Money(Decimal("280.00"), Currency.USD),
            ),
        ][:num_positions]

        for position in positions:
            portfolio.add_position(position)

        return portfolio


# ================================================================
# Database Model Factories (pour tests d'intégration)
# ================================================================


class UserModelFactory(factory.Factory):
    """Factory for User SQLAlchemy models."""

    class Meta:
        model = UserModel

    id = factory.LazyFunction(uuid4)
    email = factory.Faker("email")
    username = factory.Faker("user_name")
    full_name = factory.Faker("name")
    hashed_password = factory.LazyFunction(
        lambda: fake.password(length=60)  # Simulated bcrypt hash
    )
    role = factory.Iterator(["USER", "ADMIN", "MANAGER"])
    is_active = True
    is_verified = True
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.utc
        )
    )
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class InvestmentModelFactory(factory.Factory):
    """Factory for Investment SQLAlchemy models."""

    class Meta:
        model = InvestmentModel

    symbol = factory.LazyFunction(
        lambda: fake.lexify(text="????", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )
    name = factory.Faker("company")
    exchange = factory.Faker("random_element", elements=["NYSE", "NASDAQ", "LSE"])
    sector = factory.Iterator(["TECHNOLOGY", "HEALTHCARE", "FINANCE", "ENERGY"])
    industry = factory.Faker("job")
    market_cap = factory.Faker(
        "random_element",
        elements=[
            "NANO_CAP",
            "MICRO_CAP",
            "SMALL_CAP",
            "MID_CAP",
            "LARGE_CAP",
            "MEGA_CAP",
        ],
    )
    description = factory.Faker("text", max_nb_chars=200)


class PortfolioModelFactory(factory.Factory):
    """Factory for Portfolio SQLAlchemy models."""

    class Meta:
        model = PortfolioModel

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    name = factory.Faker("catch_phrase")
    description = factory.Faker("sentence")
    base_currency = factory.Iterator(["USD", "EUR", "GBP"])
    initial_cash = factory.LazyFunction(
        lambda: Decimal(
            str(fake.pyfloat(min_value=1000, max_value=100000, right_digits=2))
        )
    )
    current_cash = factory.LazyFunction(
        lambda: Decimal(str(fake.pyfloat(min_value=0, max_value=50000, right_digits=2)))
    )
    total_invested = factory.LazyFunction(
        lambda: Decimal(str(fake.pyfloat(min_value=0, max_value=80000, right_digits=2)))
    )
    total_value = factory.LazyFunction(
        lambda: Decimal(
            str(fake.pyfloat(min_value=1000, max_value=120000, right_digits=2))
        )
    )
    is_active = True
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(
            start_date="-1y", end_date="now", tzinfo=timezone.utc
        )
    )
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


# ================================================================
# Utility Functions
# ================================================================


def create_test_investment_batch(count: int = 5) -> list:
    """Create batch of test investments."""
    return InvestmentFactory.create_batch(count)


def create_test_portfolio_with_investments(user_id=None) -> tuple:
    """Create portfolio with investments for comprehensive testing."""
    if user_id is None:
        user_id = uuid4()

    # Create portfolio
    portfolio = PortfolioFactory.create_sample_portfolio(user_id)

    # Create investments
    investments = [
        InvestmentFactory.create_apple(),
        InvestmentFactory.create_microsoft(),
        InvestmentFactory.create(
            symbol="GOOGL",
            name="Alphabet Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE_CAP,
        ),
    ]

    # Add positions to portfolio
    for investment in investments:
        position = PositionFactory.create(
            symbol=investment.symbol,
            quantity=fake.random_int(min=10, max=200),
            average_price=Money(
                investment.current_price.amount
                * Decimal("0.95"),  # Bought at 5% discount
                investment.current_price.currency,
            ),
        )
        portfolio.add_position(position)

    return portfolio, investments


def create_realistic_market_scenario():
    """Create realistic market scenario for testing."""
    # Tech stocks
    tech_stocks = [
        InvestmentFactory.create(
            symbol="AAPL",
            name="Apple Inc.",
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE_CAP,
            current_price=Money(Decimal("150.25"), Currency.USD),
        ),
        InvestmentFactory.create(
            symbol="MSFT",
            name="Microsoft Corp.",
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE_CAP,
            current_price=Money(Decimal("305.15"), Currency.USD),
        ),
        InvestmentFactory.create(
            symbol="GOOGL",
            name="Alphabet Inc.",
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE_CAP,
            current_price=Money(Decimal("2750.80"), Currency.USD),
        ),
    ]

    # Healthcare stocks
    healthcare_stocks = [
        InvestmentFactory.create(
            symbol="JNJ",
            name="Johnson & Johnson",
            sector=InvestmentSector.HEALTHCARE,
            market_cap=MarketCap.LARGE_CAP,
            current_price=Money(Decimal("165.45"), Currency.USD),
        )
    ]

    return tech_stocks + healthcare_stocks
