"""Integration tests for the advanced portfolio FastAPI router."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from fastapi import FastAPI

from boursa_vision.infrastructure.web.routers.advanced_portfolio import router


# Test FastAPI app setup
app = FastAPI()
app.include_router(router, prefix="/api/v1/portfolios")
client = TestClient(app)


class TestAdvancedPortfolioRouter:
    """Test suite for advanced portfolio router integration."""

    def test_create_portfolio_endpoint_structure(self):
        """Test that create portfolio endpoint accepts correct request structure."""
        request_data = {
            "name": "Test Portfolio",
            "base_currency": "USD",
            "initial_cash_amount": "10000.00",
            "description": "Test portfolio for integration testing"
        }
        
        response = client.post("/api/v1/portfolios", json=request_data)
        
        # Should return success (mocked response)
        assert response.status_code == 201
        assert "message" in response.json()
        assert "portfolio_id" in response.json()
        assert "status" in response.json()
        
    def test_create_portfolio_validation(self):
        """Test validation for create portfolio endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/portfolios", json={})
        assert response.status_code == 422
        
        # Test invalid currency
        invalid_request = {
            "name": "Test Portfolio",
            "base_currency": "INVALID",
            "initial_cash_amount": "10000.00"
        }
        response = client.post("/api/v1/portfolios", json=invalid_request)
        assert response.status_code == 422

    def test_add_investment_endpoint_structure(self):
        """Test that add investment endpoint accepts correct request structure."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        request_data = {
            "symbol": "AAPL",
            "quantity": "100",
            "price": "150.00",
            "side": "buy",
            "notes": "Initial AAPL position"
        }
        
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/investments", json=request_data)
        
        # Should return success (mocked response)  
        assert response.status_code == 201
        assert "message" in response.json()
        assert "portfolio_id" in response.json()
        assert "symbol" in response.json()
        assert "status" in response.json()

    def test_add_investment_validation(self):
        """Test validation for add investment endpoint."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Test missing required fields
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/investments", json={})
        assert response.status_code == 422
        
        # Test invalid side
        invalid_request = {
            "symbol": "AAPL",
            "quantity": "100", 
            "price": "150.00",
            "side": "invalid"
        }
        response = client.post(f"/api/v1/portfolios/{portfolio_id}/investments", json=invalid_request)
        assert response.status_code == 422

    def test_get_portfolio_summary_endpoint(self):
        """Test portfolio summary endpoint returns correct structure."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
        
        # Should return success with mock data
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_id" in data
        assert "name" in data
        assert "base_currency" in data
        assert "current_value" in data
        assert "cash_balance" in data
        assert "created_at" in data

    def test_get_portfolio_performance_endpoint(self):
        """Test portfolio performance endpoint returns correct structure."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/performance")
        
        # Should return success with mock data
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_id" in data
        assert "performance_summary" in data
        assert "position_attribution" in data
        assert "historical_performance" in data

    def test_get_portfolio_valuation_endpoint(self):
        """Test portfolio valuation endpoint returns correct structure."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/valuation")
        
        # Should return success with mock data
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_id" in data
        assert "total_value" in data
        assert "valuation_timestamp" in data
        assert "use_market_prices" in data
        assert "positions_breakdown" in data

    def test_get_portfolio_positions_endpoint(self):
        """Test portfolio positions endpoint returns correct structure."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/portfolios/{portfolio_id}/positions")
        
        # Should return success with mock data
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_id" in data
        assert "positions" in data
        assert "total_positions" in data
        assert "sort_by" in data
        assert "sort_desc" in data
        
        # Check position structure
        if data["positions"]:
            position = data["positions"][0]
            assert "symbol" in position
            assert "quantity" in position
            assert "market_value" in position
            assert "cost_basis" in position
            assert "unrealized_pnl" in position
            assert "weight_percent" in position
            assert "status" in position

    def test_get_user_portfolio_analytics_endpoint(self):
        """Test user portfolio analytics endpoint returns correct structure."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/portfolios/users/{user_id}/analytics")
        
        # Should return success with mock data
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "total_portfolios" in data
        assert "analytics_timestamp" in data
        assert "aggregate_metrics" in data
        assert "portfolios" in data

    def test_query_parameters(self):
        """Test query parameters are handled correctly."""
        portfolio_id = "123e4567-e89b-12d3-a456-426614174000"
        
        # Test portfolio summary with parameters
        response = client.get(
            f"/api/v1/portfolios/{portfolio_id}/summary",
            params={"calculate_unrealized_pnl": False, "include_position_count": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unrealized_pnl"] is None
        assert data["positions_count"] is None

        # Test portfolio positions with sorting parameters
        response = client.get(
            f"/api/v1/portfolios/{portfolio_id}/positions",
            params={"sort_by": "symbol", "sort_desc": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sort_by"] == "symbol"
        assert data["sort_desc"] is False

    def test_invalid_uuid_handling(self):
        """Test handling of invalid UUID parameters."""
        invalid_id = "invalid-uuid"
        
        response = client.get(f"/api/v1/portfolios/{invalid_id}/summary")
        assert response.status_code == 422

    def test_endpoint_documentation(self):
        """Test that endpoints have proper OpenAPI documentation."""
        # Test that we can get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that our routes are documented
        assert "/api/v1/portfolios" in paths
        assert "/api/v1/portfolios/{portfolio_id}/investments" in paths
        assert "/api/v1/portfolios/{portfolio_id}/summary" in paths
        assert "/api/v1/portfolios/{portfolio_id}/performance" in paths


@pytest.mark.asyncio
class TestAdvancedPortfolioRouterAsync:
    """Async test cases for advanced portfolio router."""
    
    async def test_mock_authentication_dependency(self):
        """Test that mock authentication dependency works."""
        from boursa_vision.infrastructure.web.routers.advanced_portfolio import get_current_active_user
        
        # Mock auth should return test user
        user = get_current_active_user()
        assert user["user_id"] == "mock-user-123"
        assert user["username"] == "test_user"
