"""
External Service Mocks for Testing.

This module provides intelligent mocks for external services used in the
BoursaVision application, enabling fast and reliable testing without
dependencies on external APIs.
"""

from datetime import UTC, datetime
from typing import Any


# Constants
NETWORK_ERROR_MESSAGE = "Network error"
DEFAULT_EMAIL_FROM = "noreply@boursa-vision.com"


class YFinanceServiceError(Exception):
    """Custom exception for YFinance service errors."""


class EmailServiceError(Exception):
    """Custom exception for email service errors."""


class MockYFinanceClient:
    """
    Intelligent mock for YFinance API client.
    
    This mock provides realistic market data responses and tracks
    API calls for verification in tests.
    """
    
    def __init__(self):
        self.call_count = 0
        self.call_history: list[dict[str, Any]] = []
        self._market_data = {
            # Technology stocks
            "AAPL": {
                "price": 175.50,
                "volume": 45000000,
                "change": 2.50,
                "change_percent": 1.45,
                "market_cap": 2800000000000,
                "pe_ratio": 28.5,
                "sector": "Technology"
            },
            "GOOGL": {
                "price": 2850.75,
                "volume": 1200000,
                "change": -15.25,
                "change_percent": -0.53,
                "market_cap": 1900000000000,
                "pe_ratio": 25.8,
                "sector": "Technology"
            },
            "MSFT": {
                "price": 380.25,
                "volume": 25000000,
                "change": 5.75,
                "change_percent": 1.54,
                "market_cap": 2850000000000,
                "pe_ratio": 32.1,
                "sector": "Technology"
            },
            
            # Other sectors for diversification testing
            "JPM": {
                "price": 155.80,
                "volume": 12000000,
                "change": 1.20,
                "change_percent": 0.78,
                "market_cap": 450000000000,
                "pe_ratio": 12.5,
                "sector": "Financial"
            },
            "JNJ": {
                "price": 165.90,
                "volume": 8000000,
                "change": -0.50,
                "change_percent": -0.30,
                "market_cap": 430000000000,
                "pe_ratio": 15.8,
                "sector": "Healthcare"
            }
        }
    
    def get_stock_price(self, symbol: str) -> float | None:
        """Get current stock price for a symbol."""
        self._record_call("get_stock_price", {"symbol": symbol})
        
        if symbol in self._market_data:
            return self._market_data[symbol]["price"]
        
        # Default price for unknown symbols
        return 100.0
    
    def get_stock_info(self, symbol: str) -> dict[str, Any]:
        """Get comprehensive stock information."""
        self._record_call("get_stock_info", {"symbol": symbol})
        
        if symbol in self._market_data:
            data = self._market_data[symbol].copy()
            data["symbol"] = symbol
            data["timestamp"] = datetime.now(UTC).isoformat()
            return data
        
        # Default info for unknown symbols
        return {
            "symbol": symbol,
            "price": 100.0,
            "volume": 1000000,
            "change": 0.0,
            "change_percent": 0.0,
            "market_cap": 10000000000,
            "pe_ratio": 20.0,
            "sector": "Unknown",
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1mo",
        interval: str = "1d"
    ) -> list[dict[str, Any]]:
        """Get historical price data."""
        self._record_call("get_historical_data", {
            "symbol": symbol,
            "period": period,
            "interval": interval
        })
        
        # Generate mock historical data
        base_price = self._market_data.get(symbol, {"price": 100.0})["price"]
        historical_data = []
        
        # Generate 30 days of mock data
        for i in range(30):
            # Simulate price volatility
            price_change = (i % 5 - 2) * 0.02  # ±4% variation
            price = base_price * (1 + price_change)
            
            historical_data.append({
                "date": datetime.now(UTC).date(),
                "open": price * 0.995,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": 1000000 + (i * 50000)
            })
        
        return historical_data
    
    def get_multiple_quotes(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Get quotes for multiple symbols efficiently."""
        self._record_call("get_multiple_quotes", {"symbols": symbols})
        
        quotes = {}
        for symbol in symbols:
            quotes[symbol] = self.get_stock_info(symbol)
        
        return quotes
    
    def set_stock_price(self, symbol: str, price: float):
        """Set custom price for testing scenarios."""
        if symbol not in self._market_data:
            self._market_data[symbol] = {
                "volume": 1000000,
                "change": 0.0,
                "change_percent": 0.0,
                "market_cap": 10000000000,
                "pe_ratio": 20.0,
                "sector": "Test"
            }
        self._market_data[symbol]["price"] = price
    
    def set_market_scenario(self, scenario: str):
        """Set predefined market scenarios for testing."""
        if scenario == "bull_market":
            for symbol in self._market_data:
                self._market_data[symbol]["change_percent"] = abs(
                    self._market_data[symbol]["change_percent"]
                ) + 2.0
                
        elif scenario == "bear_market":
            for symbol in self._market_data:
                self._market_data[symbol]["change_percent"] = -(
                    abs(self._market_data[symbol]["change_percent"]) + 3.0
                )
                
        elif scenario == "volatile_market":
            for i, symbol in enumerate(self._market_data):
                change = (i % 2 * 2 - 1) * 5.0  # Alternating ±5%
                self._market_data[symbol]["change_percent"] = change
    
    def _record_call(self, method: str, params: dict[str, Any]):
        """Record API call for verification in tests."""
        self.call_count += 1
        self.call_history.append({
            "method": method,
            "params": params,
            "timestamp": datetime.now(UTC)
        })
    
    def reset_mock(self):
        """Reset mock state for clean tests."""
        self.call_count = 0
        self.call_history = []


class MockEmailService:
    """
    Mock email service for testing notification functionality.
    
    This mock captures email sending attempts and provides
    verification methods for tests.
    """
    
    def __init__(self):
        self.sent_emails: list[dict[str, Any]] = []
        self.should_fail = False
        self.failure_reason = NETWORK_ERROR_MESSAGE
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str | None = None,
        html_body: str | None = None
    ) -> bool:
        """Send an email (mocked)."""
        if self.should_fail:
            raise EmailServiceError(self.failure_reason)
        
        email_data = {
            "to": to,
            "subject": subject,
            "body": body,
            "from_email": from_email or DEFAULT_EMAIL_FROM,
            "html_body": html_body,
            "timestamp": datetime.now(UTC),
            "status": "sent"
        }
        
        self.sent_emails.append(email_data)
        return True
    
    def send_bulk_email(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        html_body: str | None = None
    ) -> dict[str, int]:
        """Send bulk emails (mocked)."""
        if self.should_fail:
            return {"failed": len(recipients), "success": 0}
        
        for recipient in recipients:
            self.send_email(recipient, subject, body, html_body=html_body)
        
        return {"success": len(recipients), "failed": 0}
    
    def send_template_email(
        self,
        to: str,
        template_name: str,
        template_data: dict[str, Any]
    ) -> bool:
        """Send templated email (mocked)."""
        subject = f"Template: {template_name}"
        body = f"Template data: {template_data}"
        
        return self.send_email(to, subject, body)
    
    def get_sent_emails(self, to_email: str | None = None) -> list[dict[str, Any]]:
        """Get sent emails, optionally filtered by recipient."""
        if to_email:
            return [email for email in self.sent_emails if email["to"] == to_email]
        return self.sent_emails.copy()
    
    def get_email_count(self, subject_contains: str | None = None) -> int:
        """Get count of sent emails, optionally filtered by subject."""
        if subject_contains:
            return len([
                email for email in self.sent_emails 
                if subject_contains.lower() in email["subject"].lower()
            ])
        return len(self.sent_emails)
    
    def set_failure_mode(self, should_fail: bool, reason: str = NETWORK_ERROR_MESSAGE):
        """Configure the mock to simulate failures."""
        self.should_fail = should_fail
        self.failure_reason = reason
    
    def reset_mock(self):
        """Reset mock state for clean tests."""
        self.sent_emails = []
        self.should_fail = False
        self.failure_reason = NETWORK_ERROR_MESSAGE


class MockCeleryApp:
    """
    Mock Celery application for testing background tasks.
    
    This mock executes tasks synchronously and provides
    tracking for verification in tests.
    """
    
    def __init__(self):
        self.executed_tasks: list[dict[str, Any]] = []
        self.task_results: dict[str, Any] = {}
        self.should_fail_tasks: set[str] = set()
    
    def send_task(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
        countdown: int = 0,
        eta: datetime | None = None
    ) -> "MockAsyncResult":
        """Send a task for execution (mocked)."""
        task_id = f"task_{len(self.executed_tasks)}"
        
        task_data = {
            "id": task_id,
            "name": task_name,
            "args": args,
            "kwargs": kwargs or {},
            "countdown": countdown,
            "eta": eta,
            "timestamp": datetime.now(UTC),
            "status": "SUCCESS" if task_name not in self.should_fail_tasks else "FAILURE"
        }
        
        self.executed_tasks.append(task_data)
        
        # Store mock result
        if task_name in self.should_fail_tasks:
            self.task_results[task_id] = Exception("Task failed")
        else:
            self.task_results[task_id] = {"status": "completed"}
        
        return MockAsyncResult(task_id, self.task_results[task_id])
    
    def delay(self, task_name: str, *args, **kwargs) -> "MockAsyncResult":
        """Delay a task execution (shortcut for send_task)."""
        return self.send_task(task_name, args, kwargs)
    
    def apply_async(
        self,
        task_name: str,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None
    ) -> "MockAsyncResult":
        """Apply task asynchronously (mocked as synchronous)."""
        return self.send_task(task_name, args, kwargs)
    
    def get_executed_tasks(self, task_name: str | None = None) -> list[dict[str, Any]]:
        """Get executed tasks, optionally filtered by name."""
        if task_name:
            return [task for task in self.executed_tasks if task["name"] == task_name]
        return self.executed_tasks.copy()
    
    def get_task_count(self, task_name: str | None = None) -> int:
        """Get count of executed tasks."""
        return len(self.get_executed_tasks(task_name))
    
    def set_task_failure(self, task_name: str, should_fail: bool = True):
        """Configure specific tasks to fail."""
        if should_fail:
            self.should_fail_tasks.add(task_name)
        else:
            self.should_fail_tasks.discard(task_name)
    
    def reset_mock(self):
        """Reset mock state for clean tests."""
        self.executed_tasks = []
        self.task_results = {}
        self.should_fail_tasks = set()


class MockAsyncResult:
    """Mock result object for Celery tasks."""
    
    def __init__(self, task_id: str, result: Any):
        self.id = task_id
        self.result = result
        self.successful = not isinstance(result, Exception)
        self.failed = isinstance(result, Exception)
    
    def get(self) -> Any:
        """Get task result."""
        if isinstance(self.result, Exception):
            raise self.result
        return self.result
    
    def ready(self) -> bool:
        """Check if task is ready (always True for mocks)."""
        return True
    
    def status(self) -> str:
        """Get task status."""
        return "SUCCESS" if self.successful else "FAILURE"


# Convenience function to create all mocks
def create_all_mocks() -> dict[str, Any]:
    """
    Create all external service mocks.
    
    Returns:
        Dictionary containing all initialized mock services.
    """
    return {
        "yfinance_client": MockYFinanceClient(),
        "email_service": MockEmailService(),
        "celery_app": MockCeleryApp(),
    }
