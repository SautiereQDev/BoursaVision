# Configuration Globale Centralisée - Boursa Vision

## Vue d'ensemble

Le système de configuration globale centralisée remplace l'ancien système dispersé de fichiers `.env` pour offrir une approche unifiée et robuste de la gestion des paramètres d'application.

## Architecture

```
📁 Configuration Architecture
├── 🔧 src/core/config.py          # Configuration globale (Pydantic Settings)
├── 📄 .env                        # Variables d'environnement principales
├── 📄 .env.local                  # Configuration locale (non versionnée)
├── 📄 .env.template               # Template de configuration
└── 📚 examples/                   # Exemples d'utilisation
    ├── config_examples.py
    └── config_usage.py
```

## Avantages

### ✅ Centralisé
- **Un seul point de vérité** pour toute la configuration
- **Import uniforme** : `from src.core.config import settings`
- **Validation automatique** avec Pydantic

### ✅ Type-Safe
- **Types stricts** avec validation automatique
- **Auto-complétion** dans l'IDE
- **Erreurs détectées** au démarrage

### ✅ Environnement-Aware
- **Détection automatique** de l'environnement
- **Configuration conditionnelle** selon dev/staging/prod
- **Valeurs par défaut** intelligentes

### ✅ Sécurisé
- **Variables sensibles** protégées
- **Validation** des paramètres critiques
- **Pas de secrets** hardcodés

## Utilisation

### Import et Accès Basique

```python
from src.core.config import settings

# Accès direct aux paramètres
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
print(f"Debug mode: {settings.debug}")

# Vérifications d'environnement
if settings.is_development:
    print("Mode développement")

if settings.is_production:
    print("Mode production")
```

### Configuration de Base de Données

```python
from sqlalchemy.ext.asyncio import create_async_engine

# Configuration automatique depuis les paramètres globaux
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_pool_overflow,
    echo=settings.debug,
)
```

### Configuration Conditionnelle

```python
# Repositories selon l'environnement
if settings.use_mock_repositories:
    repo = MockUserRepository()
else:
    repo = SQLAlchemyUserRepository()

# Logging selon l'environnement
log_level = "DEBUG" if settings.debug else "INFO"
```

## Variables d'Environnement

### 🌍 Environment & Application
```bash
ENVIRONMENT=development              # development|staging|production
DEBUG=true                          # Mode debug
APP_NAME="Boursa Vision"            # Nom de l'application
APP_VERSION="1.0.0"                 # Version
LOG_LEVEL=DEBUG                     # Niveau de log
```

### 📊 Database Configuration
```bash
POSTGRES_USER=boursa_user           # Utilisateur PostgreSQL
POSTGRES_PASSWORD=secure_password   # Mot de passe
POSTGRES_DB=boursa_vision           # Base de données
POSTGRES_HOST=localhost             # Hôte
POSTGRES_PORT=5432                  # Port

# Pool de connexions
DB_POOL_SIZE=5                      # Taille du pool
DB_POOL_OVERFLOW=10                 # Connexions supplémentaires
DB_POOL_TIMEOUT=30                  # Timeout en secondes
```

### 📡 Redis Configuration
```bash
REDIS_HOST=localhost                # Hôte Redis
REDIS_PORT=6379                     # Port Redis
REDIS_PASSWORD=                     # Mot de passe (optionnel)
REDIS_DB=0                          # Base de données Redis
```

### 🔒 Security & Auth
```bash
SECRET_KEY=your_32_char_secret_key  # Clé secrète (minimum 32 caractères)
ACCESS_TOKEN_EXPIRE_MINUTES=1440    # Expiration token (minutes)
REFRESH_TOKEN_EXPIRE_DAYS=30        # Expiration refresh token (jours)
```

### 🌐 API Configuration
```bash
API_V1_STR=/api/v1                  # Préfixe API
ALLOWED_HOSTS=localhost,127.0.0.1   # Hôtes autorisés
CORS_ORIGINS=http://localhost:3000  # Origines CORS
```

### 📈 External Services
```bash
# YFinance
YFINANCE_RATE_LIMIT=10              # Limite de taux
YFINANCE_BATCH_SIZE=50              # Taille des lots
YFINANCE_TIMEOUT=30                 # Timeout requêtes
YFINANCE_RETRY_ATTEMPTS=3           # Tentatives de retry

# Cache
MARKET_DATA_CACHE_TTL=300           # TTL données marché (secondes)
REAL_TIME_DATA_CACHE_TTL=60         # TTL données temps réel
```

### 🔧 Development & Testing
```bash
USE_MOCK_REPOSITORIES=true          # Utiliser des mocks
TESTING=false                       # Mode test
```

## Configuration par Environnement

### 🟢 Development (.env)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
USE_MOCK_REPOSITORIES=true
DATABASE_URL=sqlite:///:memory:
```

### 🟡 Staging (.env.staging)
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
USE_MOCK_REPOSITORIES=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/boursa_staging
```

### 🔴 Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
USE_MOCK_REPOSITORIES=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/boursa_vision
```

## Migration depuis l'Ancien Système

### 1. Script de Migration Automatique

```bash
cd backend
python scripts/migrate_config.py
```

### 2. Migration Manuelle

1. **Identifiez** les fichiers `.env` existants
2. **Consolidez** les variables dans `.env` à la racine
3. **Mettez à jour** vos imports :
   ```python
   # Ancien
   import os
   db_url = os.getenv("DATABASE_URL")
   
   # Nouveau
   from src.core.config import settings
   db_url = settings.database_url
   ```

### 3. Suppression des Anciens Fichiers

```bash
# Supprimez après vérification
rm backend/.env.development
rm backend/.env.production
rm docker/.env
```

## Validation et Debugging

### Validation de Configuration

```python
from examples.config_examples import validate_configuration

# Valide la configuration actuelle
validate_configuration()
```

### Affichage de Configuration

```python
from examples.config_examples import display_configuration

# Affiche la configuration (masque les mots de passe)
display_configuration()
```

## Bonnes Pratiques

### ✅ À Faire
- **Utilisez** toujours `settings` au lieu de `os.getenv()`
- **Validez** la configuration au démarrage
- **Utilisez** des valeurs par défaut sensées
- **Documentez** les nouvelles variables

### ❌ À Éviter
- **Ne hardcodez** jamais de secrets
- **N'utilisez pas** `os.getenv()` directement
- **Ne dupliquez pas** les fichiers `.env`
- **Ne versionnez pas** `.env.local`

## Déploiement

### Docker
```dockerfile
# Copiez le fichier .env
COPY .env /app/.env

# Ou utilisez des variables d'environnement
ENV ENVIRONMENT=production
ENV DATABASE_URL=postgresql://...
```

### Kubernetes
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: boursa-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: boursa-secrets
data:
  SECRET_KEY: <base64-encoded>
  DATABASE_URL: <base64-encoded>
```

## Dépannage

### Problème : Configuration non trouvée
```bash
# Vérifiez que le fichier .env existe à la racine
ls -la .env

# Vérifiez les permissions
chmod 644 .env
```

### Problème : Variables non chargées
```python
# Debug du chargement
from src.core.config import load_env_variables
env_vars = load_env_variables()
print(env_vars)
```

### Problème : Validation échoue
```python
# Vérifiez la configuration
from src.core.config import settings
print(f"Current environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
```

## Support

- 📚 **Documentation** : Voir les exemples dans `examples/`
- 🐛 **Issues** : Créez une issue GitHub
- 💬 **Questions** : Utilisez les discussions GitHub

---

**Note** : Cette configuration remplace l'ancien système dispersé. Assurez-vous de migrer tous vos modules pour utiliser le nouveau système centralisé.
