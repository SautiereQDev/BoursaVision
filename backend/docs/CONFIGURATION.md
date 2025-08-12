# Guide d'Utilisation de la Configuration Globale

## 🎯 Vue d'ensemble

Le système de configuration globale de Boursa Vision utilise **Pydantic Settings** pour centraliser et valider toute la configuration de l'application. Ce système remplace l'approche dispersée avec de multiples fichiers `.env`.

## 🏗️ Architecture

```
src/core/
├── config_simple.py      # Configuration globale simplifiée (RECOMMANDÉE)
└── config.py             # Configuration avancée (en développement)
```

## 📋 Configuration Recommandée

### Importation

```python
from src.core.config_simple import settings
```

### Utilisation Basique

```python
# Environnement
print(f"Environment: {settings.environment}")  # development, staging, production, testing
print(f"Debug mode: {settings.debug}")
print(f"Is production: {settings.is_production}")

# Base de données
print(f"Database URL: {settings.database_url}")
print(f"Postgres Host: {settings.postgres_host}")

# Redis
print(f"Redis URL: {settings.redis_url}")

# Sécurité
print(f"Secret Key: {settings.secret_key}")
print(f"Token expiry: {settings.access_token_expire_minutes}")
```

## 🔧 Configuration par Environnement

### Development (par défaut)
```bash
ENVIRONMENT=development
DEBUG=false
USE_MOCK_REPOSITORIES=false
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/0
```

### Testing
```bash
ENVIRONMENT=testing
USE_MOCK_REPOSITORIES=true
DATABASE_URL=sqlite:///:memory:
```

### Production
```bash
ENVIRONMENT=production
DEBUG=false
POSTGRES_HOST=your-postgres-host
POSTGRES_DB=boursa_vision
POSTGRES_USER=your-user
POSTGRES_PASSWORD=your-password
REDIS_HOST=your-redis-host
SECRET_KEY=your-secret-key
```

## 📚 Variables Disponibles

### Environnement & Application
- `environment`: "development" | "staging" | "production" | "testing"
- `debug`: Mode debug (bool)
- `app_name`: Nom de l'application
- `app_version`: Version
- `log_level`: Niveau de logging

### Base de Données
- `database_url`: URL complète de la base de données (auto-générée)
- `postgres_host`: Hôte PostgreSQL
- `postgres_port`: Port PostgreSQL (5432)
- `postgres_db`: Nom de la base
- `postgres_user`: Utilisateur
- `postgres_password`: Mot de passe

### Redis
- `redis_url`: URL complète Redis (auto-générée)
- `redis_host`: Hôte Redis
- `redis_port`: Port Redis (6379)
- `redis_db`: Base Redis (0)
- `redis_password`: Mot de passe Redis

### Sécurité
- `secret_key`: Clé secrète JWT
- `access_token_expire_minutes`: Durée de validité des tokens (1440)

### Services Externes
- `yfinance_rate_limit`: Limite de taux YFinance (10)
- `market_data_cache_ttl`: TTL du cache des données marché (300s)

### Développement
- `use_mock_repositories`: Utiliser des repositories mock (bool)

## 🚀 Migration depuis os.getenv()

### Avant
```python
import os

env = os.getenv("ENVIRONMENT", "development")
debug = os.getenv("DEBUG", "false").lower() == "true"
db_host = os.getenv("POSTGRES_HOST", "localhost")
```

### Après
```python
from src.core.config_simple import settings

env = settings.environment
debug = settings.debug  # Déjà un bool
db_host = settings.postgres_host
```

## 🧪 Tests

### Configuration de Test
```python
import os

# Forcer l'environnement de test
os.environ['ENVIRONMENT'] = 'testing'
os.environ['USE_MOCK_REPOSITORIES'] = 'true'

# Recharger la configuration si nécessaire
from importlib import reload
import src.core.config_simple
reload(src.core.config_simple)
from src.core.config_simple import settings
```

### Vérification
```python
assert settings.environment == "testing"
assert settings.use_mock_repositories is True
```

## 🏭 Factory Pattern

La configuration s'intègre parfaitement avec le factory pattern :

```python
from src.infrastructure.persistence.repository_factory import get_default_factory

# La factory utilise automatiquement settings.environment et settings.use_mock_repositories
factory = get_default_factory()

# En test/development avec USE_MOCK_REPOSITORIES=true → MockRepositoryFactory
# En production → SQLAlchemyRepositoryFactory
```

## 📁 Fichiers .env

### Structure Recommandée
```
.env                    # Variables communes à tous les environnements
.env.development        # Spécifique au développement
.env.production         # Spécifique à la production
.env.local              # Local, ignoré par git
```

### Ordre de Priorité
1. Variables d'environnement système
2. `.env.local`
3. `.env.{environment}` (ex: `.env.development`)
4. `.env`
5. Valeurs par défaut dans la classe

## 🔍 Propriétés Calculées

La configuration inclut des propriétés pratiques :

```python
# URLs construites automatiquement
print(settings.database_url)  # postgresql://user:pass@host:5432/db ou sqlite:///:memory:
print(settings.redis_url)     # redis://host:6379/0

# Booléens d'environnement
print(settings.is_development)  # True si environment == "development"
print(settings.is_production)   # True si environment == "production"
print(settings.is_testing)      # True si environment == "testing"
```

## 🛠️ Bonnes Pratiques

### 1. Import Unique
```python
# ✅ Bon - import au niveau module
from src.core.config_simple import settings

def my_function():
    return settings.database_url
```

### 2. Type Safety
```python
# ✅ Bon - les types sont garantis par Pydantic
port: int = settings.postgres_port  # Toujours un int
debug: bool = settings.debug        # Toujours un bool
```

### 3. Validation Automatique
```python
# ❌ Erreur si valeur invalide
os.environ['ENVIRONMENT'] = 'invalid'
settings = GlobalSettings()  # ValidationError
```

### 4. Documentation
```python
# ✅ Toutes les variables sont documentées
help(settings.environment)  # Voir la description
```

## 🔧 Customisation

Pour ajouter une nouvelle variable :

```python
class GlobalSettings(BaseSettings):
    # Nouvelle variable
    new_feature_enabled: bool = Field(
        default=False, 
        description="Active la nouvelle fonctionnalité"
    )
    
    # Variable d'environnement correspondante : NEW_FEATURE_ENABLED
```

## 📝 Exemple Complet

```python
#!/usr/bin/env python3
"""Exemple d'utilisation de la configuration globale."""

from src.core.config_simple import settings
from src.infrastructure.persistence.repository_factory import get_default_factory

def main():
    print(f"🚀 Démarrage de {settings.app_name} v{settings.app_version}")
    print(f"📊 Environnement: {settings.environment}")
    print(f"🔧 Debug: {settings.debug}")
    
    # Configuration automatique des repositories
    factory = get_default_factory()
    user_repo = factory.create_user_repository()
    
    print(f"🏭 Factory: {type(factory).__name__}")
    print(f"👤 User Repository: {type(user_repo).__name__}")
    
    # Utilisation des URLs construites
    print(f"🗄️  Database: {settings.database_url}")
    print(f"📡 Redis: {settings.redis_url}")

if __name__ == "__main__":
    main()
```

## 🎉 Avantages

1. **Centralisation** : Une seule source de vérité pour toute la configuration
2. **Validation** : Types et valeurs automatiquement validés
3. **Documentation** : Chaque variable est documentée
4. **Flexibilité** : Support de multiples sources (.env, variables système)
5. **Type Safety** : IntelliSense et vérification de types
6. **Performance** : Configuration chargée une seule fois au démarrage
