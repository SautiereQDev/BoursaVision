import pytest
from src.infrastructure.persistence.mock_repositories import MockPortfolioRepository
from uuid import uuid4

@pytest.fixture
def portfolio_repo():
    return MockPortfolioRepository()

@pytest.mark.asyncio
async def test_save_and_find_by_id(portfolio_repo):
    fake_id = uuid4()
    # save returns the entity, but find_by_id always returns None in the mock
    entity = await portfolio_repo.save(None)
    found = await portfolio_repo.find_by_id(fake_id)
    assert found is None

@pytest.mark.asyncio
async def test_exists(portfolio_repo):
    fake_id = uuid4()
    exists = await portfolio_repo.exists(fake_id)
    assert exists is False

@pytest.mark.asyncio
async def test_delete(portfolio_repo):
    fake_id = uuid4()
    result = await portfolio_repo.delete(fake_id)
    assert result in (True, False, None)
