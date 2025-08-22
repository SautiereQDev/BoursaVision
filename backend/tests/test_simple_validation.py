"""Test simple pour valider la configuration pytest."""

import pytest


@pytest.mark.fast
@pytest.mark.unit
def test_simple_addition():
    """Test simple pour vérifier que pytest fonctionne."""
    # Arrange
    a = 1
    b = 2
    
    # Act
    result = a + b
    
    # Assert
    assert result == 3


@pytest.mark.fast
@pytest.mark.unit
def test_string_operations():
    """Test simple pour les opérations sur chaînes."""
    # Arrange
    prefix = "Hello"
    suffix = "World"
    
    # Act
    result = f"{prefix} {suffix}"
    
    # Assert
    assert result == "Hello World"
    assert len(result) == 11


@pytest.mark.fast
@pytest.mark.unit
def test_list_operations():
    """Test simple pour les opérations sur listes."""
    # Arrange
    items = [1, 2, 3]
    
    # Act
    items.append(4)
    
    # Assert
    assert len(items) == 4
    assert items[-1] == 4
