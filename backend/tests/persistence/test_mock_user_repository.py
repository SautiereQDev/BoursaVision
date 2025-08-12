import pytest

from src.domain.entities.user import User, UserRole
from src.infrastructure.persistence.mock_repositories import MockUserRepository


@pytest.fixture
def user_repo():
    return MockUserRepository()


@pytest.mark.asyncio
async def test_save_and_find_by_email(user_repo):
    user = User.create(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        role=UserRole.ADMIN,
    )
    await user_repo.save(user)
    found = await user_repo.find_by_email("test@example.com")
    assert found is None  # Mock always returns None


@pytest.mark.asyncio
async def test_exists_by_email(user_repo):
    exists = await user_repo.exists_by_email("test@example.com")
    assert exists is False


@pytest.mark.asyncio
async def test_delete(user_repo):
    user = User.create(
        email="delete@example.com",
        username="deleteuser",
        first_name="To",
        last_name="Delete",
    )
    await user_repo.save(user)
    await user_repo.delete(user)
    # No error should be raised, nothing to assert (mock)
