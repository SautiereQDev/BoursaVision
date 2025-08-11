import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.infrastructure.persistence.models  # Ensure all model modules are loaded

# Import Base after loading models
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.models.instruments import Instrument
from src.infrastructure.persistence.models.portfolios import Portfolio
from src.infrastructure.persistence.models.transactions import Transaction
from src.infrastructure.persistence.models.users import User

# Configuration de la base de données de test


@pytest.fixture(scope="function")
def db_session():
    # Explicit import of models to register tables
    # Ensure all model modules are loaded

    # Engine en mémoire et création des tables
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    # Suppression des tables
    Base.metadata.drop_all(engine)


def test_transactions_example():
    # Exemple de test pour transactions
    pass  # Supprimé l'assertion constante inutile


def test_transaction_creation(db_session):
    # Create user first
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        username="testuser",  # Ajout du champ obligatoire
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()  # Get the user ID

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(
        id=uuid.uuid4(), symbol="AAPL", instrument_type="stock"  # Add required field
    )
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("10.0"),
        price=Decimal("150.0"),
        amount=Decimal("1500.0"),
        fees=Decimal("10.0"),
        taxes=Decimal("5.0"),
        net_amount=Decimal("1485.0"),
        currency="USD",
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()

    assert transaction.id is not None
    assert transaction.symbol == "AAPL"
    assert transaction.transaction_type == "BUY"
    assert transaction.net_amount == Decimal("1485.0")


def test_transaction_constraints(db_session):
    with pytest.raises(Exception):
        transaction = Transaction(
            portfolio_id=None,  # Manque de portfolio_id
            instrument_id=None,  # Manque de instrument_id
            symbol="AAPL",
            transaction_type="INVALID_TYPE",  # Type invalide
            quantity=Decimal("10.0"),
            price=Decimal("150.0"),
            amount=Decimal("1500.0"),
            fees=Decimal("10.0"),
            taxes=Decimal("5.0"),
            net_amount=Decimal("1485.0"),
            currency="USD",
            executed_at="2025-08-08 12:00:00",
        )
        db_session.add(transaction)
        db_session.commit()


def test_transaction_relations(db_session):
    user = User(
        id=uuid.uuid4(),
        email="relations@example.com",
        username="relationuser",  # Ajout du champ obligatoire
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(id=uuid.uuid4(), symbol="AAPL", instrument_type="stock")
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("10.0"),
        price=Decimal("150.0"),
        amount=Decimal("1500.0"),
        fees=Decimal("10.0"),
        taxes=Decimal("5.0"),
        net_amount=Decimal("1485.0"),
        currency="USD",
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()

    # Vérifier les relations
    assert transaction.portfolio.id == portfolio.id
    assert transaction.instrument.id == instrument.id


def test_transaction_negative_values(db_session):
    user = User(
        id=uuid.uuid4(),
        email="negative@example.com",
        username="negativeuser",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(id=uuid.uuid4(), symbol="AAPL", instrument_type="stock")
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("-10.0"),  # Valeur négative
        price=Decimal("150.0"),
        amount=Decimal("-1500.0"),  # Valeur négative
        fees=Decimal("10.0"),
        taxes=Decimal("5.0"),
        net_amount=Decimal("1485.0"),
        currency="USD",
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()
    assert transaction.id is not None


def test_transaction_calculated_fields(db_session):
    user = User(
        id=uuid.uuid4(),
        email="fields@example.com",
        username="fieldsuser",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(id=uuid.uuid4(), symbol="AAPL", instrument_type="stock")
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("10.0"),
        price=Decimal("150.0"),
        amount=Decimal("1500.0"),
        fees=Decimal("10.0"),
        taxes=Decimal("5.0"),
        net_amount=Decimal("1485.0"),
        currency="USD",
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()

    # Vérifier les champs calculés
    assert transaction.amount == transaction.quantity * transaction.price
    assert transaction.net_amount == (
        transaction.amount - transaction.fees - transaction.taxes
    )


def test_transaction_zero_fees_and_taxes(db_session):
    user = User(
        id=uuid.uuid4(),
        email="zero@example.com",
        username="zerouser",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(id=uuid.uuid4(), symbol="AAPL", instrument_type="stock")
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("10.0"),
        price=Decimal("150.0"),
        amount=Decimal("1500.0"),
        fees=Decimal("0.0"),  # Frais nuls
        taxes=Decimal("0.0"),  # Taxes nulles
        net_amount=Decimal("1500.0"),
        currency="USD",
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()

    # Vérifier les champs calculés
    assert transaction.net_amount == transaction.amount


def test_transaction_invalid_currency(db_session):
    user = User(
        id=uuid.uuid4(),
        email="invalid@example.com",
        username="invaliduser",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.flush()

    portfolio = Portfolio(
        id=uuid.uuid4(), user_id=user.id, name="Test Portfolio", base_currency="USD"
    )
    instrument = Instrument(id=uuid.uuid4(), symbol="AAPL", instrument_type="stock")
    db_session.add(portfolio)
    db_session.add(instrument)
    db_session.commit()

    transaction = Transaction(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        symbol="AAPL",
        transaction_type="BUY",
        quantity=Decimal("10.0"),
        price=Decimal("150.0"),
        amount=Decimal("1500.0"),
        fees=Decimal("10.0"),
        taxes=Decimal("5.0"),
        net_amount=Decimal("1485.0"),
        currency="INVALID",  # Devise invalide
        executed_at=datetime(2025, 8, 8, 12, 0, 0),
    )
    db_session.add(transaction)
    db_session.commit()
    assert transaction.id is not None
