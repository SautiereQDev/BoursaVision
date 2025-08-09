import pytest

from infrastructure.persistence.models.users import User


def test_users_example():
    # Exemple de test pour users
    user = User(email="test@example.com", password_hash="hashed_password")
    assert user.email == "test@example.com"
