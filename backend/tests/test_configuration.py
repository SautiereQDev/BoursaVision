"""
Basic configuration test to validate pytest setup.

This test validates that our modern pytest configuration works
correctly without complex dependencies.
"""

import pytest


@pytest.mark.fast
@pytest.mark.unit
def test_pytest_basic_functionality():
    """Test basic pytest functionality."""
    assert True


@pytest.mark.fast 
@pytest.mark.unit
def test_pytest_marks_are_working():
    """Test that pytest marks are properly configured."""
    # This test should be automatically marked as 'fast' and 'unit'
    # based on our pytest configuration
    assert 2 + 2 == 4


class TestPytestConfiguration:
    """Test class to validate pytest class detection."""
    
    @pytest.mark.fast
    def test_class_based_test(self):
        """Test that class-based tests work."""
        assert "pytest" in "pytest configuration"
    
    @pytest.mark.parametrize("value,expected", [
        (1, True),
        (0, False),
        (-1, True),
    ])
    def test_parametrized_test(self, value, expected):
        """Test parametrized tests work correctly."""
        assert bool(value) == expected


@pytest.mark.asyncio
async def test_async_support():
    """Test that async tests work with pytest 8.4.1."""
    import asyncio
    
    # Simple async operation
    await asyncio.sleep(0.01)
    
    result = "async test"
    assert result == "async test"


def test_fixtures_basic_functionality(sample_user_data):
    """Test that basic fixtures work."""
    assert sample_user_data["email"] == "test@example.com"
    assert sample_user_data["id"] == "test-user-123"


def should_support_different_naming_convention():
    """Test that 'should_*' naming convention works."""
    assert True
