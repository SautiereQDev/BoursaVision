import pytest

from src.infrastructure.persistence.models.enums import InstrumentType, TransactionType


def test_enums():
    # Teste l'accessibilité d'un enum existant
    from src.infrastructure.persistence.models.enums import TransactionType

    assert TransactionType.BUY.name == "BUY"
    assert TransactionType.BUY.value == "BUY"


def test_enums_example():
    # Exemple de test pour enums
    from src.infrastructure.persistence.models.enums import InstrumentType

    assert InstrumentType.STOCK.name == "STOCK"
    assert InstrumentType.STOCK.value == "stock"
