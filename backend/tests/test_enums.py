import pytest

from infrastructure.persistence.models.enums import InstrumentType, TransactionType


def test_enums():
    # Teste l'accessibilité d'un enum existant
    from infrastructure.persistence.models.enums import TransactionType

    assert TransactionType.BUY.name == "BUY"
    assert TransactionType.BUY.value == "BUY"


def test_enums_example():
    # Exemple de test pour enums
    from infrastructure.persistence.models.enums import InstrumentType

    assert InstrumentType.STOCK.name == "STOCK"
    assert InstrumentType.STOCK.value == "stock"
