# Système d'Archivage Automatique des Données de Marché

Ce module fournit un système d'archivage continu des données financières utilisant Celery et YFinance pour maintenir un historique complet des prix et volumes des instruments financiers.

## 🎯 Objectif

Éviter la perte de précision des données historiques en archivant automatiquement :
- **Données minute** toutes les 5 minutes pendant les heures de marché
- **Données horaires** chaque heure 
- **Données quotidiennes** à 18h00 UTC (après fermeture des marchés)
- **Données hebdomadaires** le dimanche à 20h00

## 🏗️ Architecture

```
src/infrastructure/background/
├── __init__.py                 # Exports publics du module
├── celery_app.py              # Configuration Celery + scheduler
├── market_data_archiver.py    # Service d'archivage principal
├── tasks.py                   # Tâches Celery
├── cli.py                     # Interface en ligne de commande
└── README.md                  # Cette documentation
```

### Design Patterns Utilisés

- **Strategy Pattern** : Différentes stratégies d'archivage selon l'intervalle
- **Repository Pattern** : Accès aux données via les repositories existants
- **Observer Pattern** : Events Celery pour monitoring  
- **Factory Pattern** : Création des entités MarketData
- **Command Pattern** : Tâches Celery comme commandes

## 📊 Indices Supportés

Le système archive automatiquement les données pour :

- **CAC 40** : 40 plus grandes capitalisations françaises
- **NASDAQ 100** : 100 plus grandes capitalisations technologiques
- **FTSE 100** : Principales capitalisations britanniques  
- **DAX 40** : Principales capitalisations allemandes

## 🚀 Démarrage

### 1. Lancement via Docker (Recommandé)

```bash
# Démarrer tous les services incluant Celery
cd docker
docker-compose -f docker-compose.dev.yml up -d

# Vérifier que les workers sont démarrés
docker-compose -f docker-compose.dev.yml ps
```

### 2. Lancement manuel

```bash
# Terminal 1 : Worker Celery
cd backend
poetry run python src/infrastructure/background/cli.py worker

# Terminal 2 : Scheduler Celery Beat
poetry run python src/infrastructure/background/cli.py beat
```

## 🛠️ Interface CLI

Le système fournit une CLI complète pour la gestion manuelle :

### Commandes Principales

```bash
# Archivage manuel de tous les symboles
poetry run python src/infrastructure/background/cli.py archive --interval 1d

# Archivage de symboles spécifiques
poetry run python src/infrastructure/background/cli.py archive-symbols AAPL MSFT GOOGL --interval 1h

# Statut du système d'archivage
poetry run python src/infrastructure/background/cli.py status

# Test des connexions
poetry run python src/infrastructure/background/cli.py test-connection

# Aide détaillée
poetry run python src/infrastructure/background/cli.py --help
```

### Options d'Intervalle

- `1m` : 1 minute (données haute fréquence)
- `5m` : 5 minutes  
- `15m` : 15 minutes
- `30m` : 30 minutes
- `1h` : 1 heure
- `1d` : 1 jour (par défaut)
- `1w` : 1 semaine
- `1M` : 1 mois

## 📅 Programmation Automatique

### Tâches Celery Beat

| Tâche | Fréquence | Intervalle | Description |
|-------|-----------|------------|-------------|
| `archive-market-data-frequent` | Toutes les 5 min | 1m | Données haute fréquence |
| `archive-market-data-hourly` | Toutes les heures | 1h | Données horaires |
| `archive-market-data-daily` | 18h00 UTC | 1d | Données quotidiennes |
| `archive-market-data-weekly` | Dim 20h00 | 1w | Données hebdomadaires |
| `health-check` | Toutes les 30 min | - | Santé du système |

### Configuration des Horaires

Les horaires sont optimisés pour les marchés financiers :
- **Données fréquentes** : Pendant les heures d'ouverture
- **Données quotidiennes** : Après fermeture (18h00 UTC)
- **Données hebdomadaires** : Weekend (dimanche)

## 🗄️ Stockage des Données

### Base de Données TimescaleDB

```sql
-- Table principale : market_data
-- Hypertable optimisée pour les séries temporelles
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    interval_type VARCHAR(5) NOT NULL,
    open_price NUMERIC(15,4),
    high_price NUMERIC(15,4), 
    low_price NUMERIC(15,4),
    close_price NUMERIC(15,4),
    adjusted_close NUMERIC(15,4),
    volume BIGINT,
    source VARCHAR(20) DEFAULT 'yfinance',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, symbol, interval_type)
);
```

### Index Optimisés

- `idx_market_data_symbol_time` : Requêtes par symbole
- `idx_market_data_interval` : Requêtes par intervalle
- Partitioning automatique par TimescaleDB

## 📈 Monitoring et Logs

### Logs Structured

```json
{
  "timestamp": "2024-08-14T10:30:00Z",
  "level": "INFO", 
  "logger": "market_data_archiver",
  "message": "Archival completed: 120/125 symbols (96.0% success rate)",
  "context": {
    "interval": "1d",
    "successful": 120,
    "failed": 5,
    "duration_seconds": 245
  }
}
```

### Métriques Celery

- **Worker status** : Santé des workers
- **Task success rate** : Taux de succès des tâches
- **Latency** : Temps d'exécution des tâches
- **Error tracking** : Suivi des erreurs

## ⚙️ Configuration

### Variables d'Environnement

```bash
# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# YFinance Rate Limiting
YFINANCE_RATE_LIMIT=10
YFINANCE_BATCH_SIZE=50
YFINANCE_TIMEOUT=30
YFINANCE_RETRY_ATTEMPTS=3

# Cache
MARKET_DATA_CACHE_TTL=300
REAL_TIME_DATA_CACHE_TTL=60
```

### Personnalisation des Indices

Pour ajouter de nouveaux indices, modifier `market_data_archiver.py` :

```python
def _load_financial_indices(self) -> Dict[str, List[str]]:
    return {
        "custom_index": [
            "SYMBOL1", "SYMBOL2", "SYMBOL3"
        ],
        # ... autres indices
    }
```

## 🔧 Maintenance

### Nettoyage des Données

```bash
# Nettoyer les données anciennes (> 365 jours)
poetry run celery -A src.infrastructure.background.celery_app call \
  src.infrastructure.background.tasks.cleanup_old_data_task \
  --args='[365]'
```

### Monitoring des Performances

```bash
# Statut des workers Celery
poetry run celery -A src.infrastructure.background.celery_app status

# Inspection des tâches actives
poetry run celery -A src.infrastructure.background.celery_app inspect active

# Statistiques des tâches
poetry run celery -A src.infrastructure.background.celery_app inspect stats
```

## 🚨 Gestion d'Erreurs

### Stratégies de Resilience

1. **Retry automatique** : 3 tentatives avec délai croissant
2. **Rate limiting** : Respect des limites YFinance (200ms entre requêtes)
3. **Circuit breaker** : Arrêt temporaire en cas d'erreurs répétées
4. **Graceful degradation** : Continuation même si certains symboles échouent

### Monitoring des Erreurs

- **Logs centralisés** : Tous les échecs sont loggés
- **Alertes** : Notifications en cas de taux d'échec > 20%
- **Métriques** : Suivi des performances via Celery

## 🧪 Tests

### Tests d'Intégration

```bash
# Test manuel d'archivage
poetry run python src/infrastructure/background/cli.py archive-symbols AAPL --interval 1d

# Test des connexions
poetry run python src/infrastructure/background/cli.py test-connection

# Vérification du statut
poetry run python src/infrastructure/background/cli.py status
```

### Tests de Performance

Le système est conçu pour traiter :
- **~200 symboles** en moins de 5 minutes
- **Taux de succès** > 95% en conditions normales
- **Latence** < 2 secondes par symbole

## 📚 Intégration

### Utilisation dans le Code

```python
from src.infrastructure.background.market_data_archiver import MarketDataArchiver

# Instance de l'archiveur
archiver = MarketDataArchiver()

# Archivage programmatique
report = await archiver.archive_all_symbols("1h")

# Statut du système
status = await archiver.get_archival_status()
```

### Événements Domaine

```python
from src.domain.events.market_events import MarketDataUpdatedEvent

# L'archivage génère automatiquement des événements
# pour notification des autres services
```

## 🔮 Évolutions Futures

### Fonctionnalités Prévues

1. **Sources multiples** : Alpha Vantage, IEX Cloud, Polygon
2. **Compression intelligente** : Optimisation du stockage
3. **API GraphQL** : Requêtes flexibles des données archivées
4. **Machine Learning** : Détection d'anomalies dans les données
5. **Webhooks** : Notifications en temps réel des événements

### Optimisations

1. **Parallélisation** : Traitement concurrent par indice
2. **Caching intelligent** : Éviter les requêtes redondantes
3. **Compression** : Réduction de l'espace disque
4. **Partitioning** : Amélioration des performances de requête

---

## 🆘 Support

En cas de problème :

1. **Vérifier les logs** : `docker-compose logs celery-worker`
2. **Statut système** : `poetry run python cli.py status`
3. **Test connexions** : `poetry run python cli.py test-connection`
4. **Restart services** : `docker-compose restart celery-worker celery-beat`

Le système d'archivage est conçu pour être robuste et auto-réparateur, mais en cas de problème persistant, consulter les logs détaillés.
