# BoursaVision — Instructions Copilot

## Contexte
- **Monorepo** : Application de trading/investissement avec architecture Clean Architecture
- **Backend** : Python 3.11, FastAPI, SQLAlchemy 2.0+, PostgreSQL + TimescaleDB, Redis, Celery
- **Frontend** : TypeScript 5.7, React 19, Vite 6, PWA avec Service Worker
- **Infrastructure** : Docker Compose, Nginx, Poetry (backend), npm (frontend)
- **Build/Test** : `make dev` (Docker), `poetry run pytest` (backend), `npm run build` (frontend)

## Architecture Clean Architecture (respecter strictement)
```
backend/src/boursa_vision/
├── domain/          # Entités, Value Objects, Services métier
│   ├── entities/    # Portfolio, Investment, User, MarketData
│   ├── services/    # RiskCalculator, PerformanceAnalyzer
│   └── repositories/ # Interfaces abstraites
├── application/     # Use Cases, Commands/Queries (CQRS)
│   ├── commands/    # Mutations (CreatePortfolio, etc.)
│   ├── queries/     # Lectures (GetPortfolios, etc.)
│   └── services/    # Services applicatifs
└── infrastructure/  # Adapters externes
    ├── persistence/ # SQLAlchemy, repositories concrets
    ├── web/         # FastAPI, routers, middleware
    └── background/  # Celery tasks, archivage
```

## Règles de code (à respecter strictement)
- **Python** : Type hints stricts (`mypy` configuré), pas de `Any` sans justification
- **TypeScript** : Mode strict activé (`"strict": true`), pas de `any` implicite
- **Domain First** : Commencer par le domaine, puis application, puis infrastructure
- **Dépendances** : Domain ne dépend de rien, Application dépend de Domain uniquement
- **Repositories** : Interfaces dans Domain, implémentations dans Infrastructure
- **Sécurité** : JWT auth, validation des entrées, secrets via environnement
- **Performance** : Cache Redis, requêtes SQL optimisées, pagination obligatoire

## Outillage & scripts
- **Backend** :
  - Lint/format : `black`, `isort`, `flake8`, `mypy` 
  - Tests : `poetry run pytest` + coverage (`pytest-cov`)
  - Dev : `make dev` (Docker Compose avec hot-reload)
- **Frontend** :
  - Lint/format : `npm run lint` (ESLint), Prettier intégré
  - Build : `npm run build` (TypeScript + Vite)
  - Dev : `npm run dev` (Vite dev server)
- **Global** : `make archive` (données de marché), `make backup` (BDD)

## Style commit & PR
- **Commits** : Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`)
- **Messages** : Courts, impératifs, en anglais ("Add portfolio validation")
- **PR** : Description détaillée, checklist tests, mention des risques, labels
- **Branches** : Feature branches (`feature/jwt-auth`, `fix/portfolio-bug`)

## Directives à Copilot

### Quand tu écris du code :
- **Tests d'abord** : Génère les tests unitaires **dans le même commit**
- **Domain-first** : Commence par les entités/value objects, puis use cases
- **Type Safety** : Utilise les types stricts (Python type hints, TS interfaces)
- **CQRS** : Sépare les commandes (mutations) des queries (lectures)
- **Dependency Injection** : Utilise les containers existants (`ApplicationContainer`)
- **Async/await** : Code asynchrone partout (FastAPI, SQLAlchemy async)

### Patterns à utiliser :
- **Repository Pattern** : Interfaces abstraites, implémentations concrètes
- **Unit of Work** : Pour les transactions complexes
- **Domain Events** : Pour la communication entre agrégats
- **Value Objects** : Pour Money, Price, Currency (immutables)
- **Factory Pattern** : Pour la création d'entités complexes

### Quand tu modifies :
- Exécute `poetry run pytest` et vérifie la coverage avant PR
- Met à jour la documentation inline si l'API change
- Respecte les alias de paths (`from ...domain import`)
- Vérifie les migrations Alembic si modèles changent

### Structure des tests :
```
tests/
├── unit/           # Tests unitaires (domaine + application)
├── integration/    # Tests d'intégration (BDD, API)
└── e2e/           # Tests end-to-end (scénarios complets)
```

## Pièges connus
- **Circular imports** : Utiliser des imports locaux dans les fonctions si nécessaire
- **SQLAlchemy async** : Utiliser `async with session` pour les transactions
- **Domain purity** : Les entités Domain ne doivent jamais importer Infrastructure
- **UTC everywhere** : Toutes les dates en UTC, conversion côté client uniquement
- **Cache Redis** : Attention aux TTL, préfixer les clés par service
- **Docker volumes** : Les logs persistent dans des volumes nommés
- **Market Data** : Utiliser TimescaleDB pour les données time-series
- **Rate Limiting** : API externe (YFinance) limitée, utiliser le cache intelligent

## APIs externes sensibles
- **YFinance** : Rate limiting strict, cache obligatoire (24h pour les données daily)
- **PostgreSQL** : Utiliser les index sur les colonnes de filtrage temporel
- **Redis** : TTL adapté par type de données (5min real-time, 24h daily)

## Environnements
- **Development** : Hot-reload activé, logs détaillés, DB en local
- **Production** : Optimisations activées, logs structurés, monitoring

---

*Dernière mise à jour : 21 août 2025*
