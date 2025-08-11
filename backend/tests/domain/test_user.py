import pytest
from src.domain.entities.user import User, UserRole
from src.domain.value_objects.money import Currency

def test_user_creation():
    user = User.create(
        email="user@example.com",
        username="user",
        first_name="John",
        last_name="Doe",
        role=UserRole.VIEWER,
        preferred_currency=Currency.USD,
    )
    assert user.email == "user@example.com"
    assert user.role == UserRole.VIEWER
    assert user.is_active
    assert not user.email_verified

def test_user_role_admin():
    user = User.create(
        email="admin@example.com",
        username="admin",
        first_name="Alice",
        last_name="Smith",
        role=UserRole.ADMIN,
        preferred_currency=Currency.USD,
    )
    assert user.role == UserRole.ADMIN
    assert user.is_active

def test_user_set_email_verified():
    user = User.create(
        email="user2@example.com",
        username="user2",
        first_name="Jane",
        last_name="Roe",
        role=UserRole.VIEWER,
        preferred_currency=Currency.USD,
    )
    user.email_verified = True
    assert user.email_verified

def test_user_inactive():
    user = User.create(
        email="inactive@example.com",
        username="inactive",
        first_name="Inactive",
        last_name="User",
        role=UserRole.VIEWER,
        preferred_currency=Currency.USD,
    )
    user.is_active = False
    assert not user.is_active
