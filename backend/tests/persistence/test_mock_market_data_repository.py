import pytest
from src.infrastructure.persistence.mock_repositories import MockMarketDataRepository
from uuid import uuid4

@pytest.fixture
def market_data_repo():
    return MockMarketDataRepository()

@pytest.mark.asyncio
async def test_save_and_find_by_symbol(market_data_repo):
    # save returns the entity, but find_by_symbol always returns [] in the mock
    result = await market_data_repo.save(None)
    found = await market_data_repo.find_by_symbol("AAPL")
    assert found == []

@pytest.mark.asyncio
async def test_exists_by_symbol_and_timestamp(market_data_repo):
    exists = await market_data_repo.exists_by_symbol_and_timestamp("AAPL", None)
    assert exists is False

@pytest.mark.asyncio
async def test_delete_by_symbol_and_date_range(market_data_repo):
    deleted = await market_data_repo.delete_by_symbol_and_date_range("AAPL", None, None)
    assert deleted == 0 or deleted is None
