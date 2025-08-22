from src.infrastructure.persistence.unit_of_work import (
    IUnitOfWork,
    SQLAlchemyUnitOfWork,
    get_uow,
)


def test_uow_import():
    # Simple smoke test to ensure classes and function are importable
    assert IUnitOfWork is not None
    assert SQLAlchemyUnitOfWork is not None
    assert get_uow is not None


# Ajoutez ici des tests unitaires plus détaillés pour chaque méthode si besoin
