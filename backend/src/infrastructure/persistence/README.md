# Repository Factory Pattern

Ce système utilise le pattern Factory pour gérer les repositories selon l'environnement.

## Architecture

### Factories disponibles

1. **MockRepositoryFactory** : Implémentations mock pour le développement et les tests
2. **SQLAlchemyRepositoryFactory** : Implémentations SQLAlchemy pour la production (à terme)

### Configuration par environnement

Le système sélectionne automatiquement la factory appropriée selon :

- **Variable ENVIRONMENT** : `development`, `testing`, `production`, `staging`
- **Variable USE_MOCK_REPOSITORIES** : `true`/`false`

## Usage

### Développement

```bash
export ENVIRONMENT=development
export USE_MOCK_REPOSITORIES=true
```

```python
from src.infrastructure.persistence import get_user_repository

# Utilise automatiquement MockUserRepository
user_repo = get_user_repository()
```

### Production (futur)

```bash
export ENVIRONMENT=production
export USE_MOCK_REPOSITORIES=false
```

```python
from src.infrastructure.persistence import get_user_repository

# Utilisera SQLAlchemyUserRepository quand disponible
user_repo = get_user_repository()
```

### Tests

```python
import pytest
from src.infrastructure.persistence.repository_factory import MockRepositoryFactory, configure_repositories

@pytest.fixture
def setup_mock_repositories():
    """Force l'utilisation des mocks pour les tests."""
    configure_repositories(MockRepositoryFactory())
    yield
    # Cleanup sera automatique
```

## Configuration personnalisée

```python
from src.infrastructure.persistence.repository_factory import (
    configure_repositories, 
    SQLAlchemyRepositoryFactory,
    MockRepositoryFactory
)

# Forcer l'utilisation d'une factory spécifique
configure_repositories(MockRepositoryFactory())

# Ou créer une factory personnalisée
class CustomRepositoryFactory(IRepositoryFactory):
    def create_user_repository(self):
        return CustomUserRepository()

configure_repositories(CustomRepositoryFactory())
```

## Migration vers SQLAlchemy

Quand les repositories SQLAlchemy seront complets :

1. Implémenter les méthodes manquantes dans `SQLAlchemyUserRepository`, etc.
2. Corriger les problèmes de session dans `SQLAlchemyRepositoryFactory`
3. Modifier `get_default_factory()` pour utiliser `SQLAlchemyRepositoryFactory` en production
4. Supprimer le TODO dans le code

## Fichiers de configuration

- `.env.development` : Configuration pour le développement
- `.env.production` : Configuration pour la production

## Status actuel

✅ **Mocks** : Complets et fonctionnels  
🚧 **SQLAlchemy** : En cours de développement (utilise les mocks en fallback)  
✅ **Tests** : Tous les tests passent avec les mocks  
✅ **Factory Pattern** : Implémenté et fonctionnel
