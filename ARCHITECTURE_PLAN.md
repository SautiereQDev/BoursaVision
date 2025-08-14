# 🏗️ Plan de Réorganisation - Boursa Vision Backend

## 📁 **Nouvelle Structure Proposée (Clean Architecture)**

```
backend/
├── src/
│   ├── boursa_vision/                    # Package principal
│   │   ├── __init__.py
│   │   ├── main.py                       # Point d'entrée FastAPI (depuis racine)
│   │   │
│   │   ├── core/                         # Configuration & Utilitaires centraux
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # Configuration globale
│   │   │   ├── logging.py                # Configuration des logs
│   │   │   └── exceptions.py             # Exceptions métier globales
│   │   │
│   │   ├── domain/                       # Logique métier pure (Domain Layer)
│   │   │   ├── __init__.py
│   │   │   ├── entities/                 # Entités métier
│   │   │   ├── value_objects/            # Objets valeur
│   │   │   ├── repositories/             # Interfaces des repositories
│   │   │   ├── services/                 # Services métier
│   │   │   └── events/                   # Événements métier
│   │   │
│   │   ├── application/                  # Logique applicative (Application Layer)
│   │   │   ├── __init__.py
│   │   │   ├── use_cases/                # Cas d'usage
│   │   │   │   ├── market_data/          # Gestion données marché
│   │   │   │   ├── recommendations/      # Recommandations
│   │   │   │   ├── portfolio/            # Portfolio management
│   │   │   │   └── analysis/             # Analyses avancées
│   │   │   ├── services/                 # Services applicatifs
│   │   │   │   ├── archiving/            # Services d'archivage
│   │   │   │   ├── recommendation/       # Services de recommandation
│   │   │   │   └── market_analysis/      # Services d'analyse
│   │   │   ├── commands/                 # Commandes (CQRS)
│   │   │   ├── queries/                  # Requêtes (CQRS)
│   │   │   └── handlers/                 # Gestionnaires
│   │   │
│   │   ├── infrastructure/               # Couche technique (Infrastructure Layer)
│   │   │   ├── __init__.py
│   │   │   ├── persistence/              # Persistance des données
│   │   │   │   ├── database/             # Configuration DB
│   │   │   │   ├── repositories/         # Implémentations repositories
│   │   │   │   └── models/               # Modèles SQLAlchemy
│   │   │   ├── external/                 # Services externes
│   │   │   │   ├── yfinance/             # Intégration YFinance
│   │   │   │   └── market_data/          # Autres sources de données
│   │   │   ├── web/                      # API REST
│   │   │   │   ├── fastapi/              # Configuration FastAPI
│   │   │   │   ├── routers/              # Routeurs API
│   │   │   │   ├── middleware/           # Middlewares
│   │   │   │   └── dependencies/         # Dépendances FastAPI
│   │   │   └── background/               # Tâches en arrière-plan
│   │   │       ├── celery/               # Configuration Celery
│   │   │       └── jobs/                 # Jobs d'archivage
│   │   │
│   │   └── presentation/                 # Interface utilisateur (Presentation Layer)
│   │       ├── __init__.py
│   │       ├── api/                      # API REST endpoints
│   │       │   ├── v1/                   # Version 1 de l'API
│   │       │   │   ├── market_data.py
│   │       │   │   ├── recommendations.py
│   │       │   │   ├── portfolio.py
│   │       │   │   └── analysis.py
│   │       │   └── v2/                   # Future version
│   │       ├── schemas/                  # Schémas Pydantic
│   │       │   ├── requests/
│   │       │   ├── responses/
│   │       │   └── common/
│   │       └── serializers/              # Sérialiseurs de données
│   │
│   └── tools/                            # Outils et scripts (ancien services/)
│       ├── __init__.py
│       ├── data_migration/               # Scripts de migration
│       ├── market_patterns/              # Patterns de données marché
│       └── cli/                          # Interface en ligne de commande
│           ├── archiver_cli.py           # CLI pour archivage
│           └── data_quality_cli.py       # CLI pour qualité données
│
├── tests/                                # Tests organisés par couche
│   ├── unit/                             # Tests unitaires
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/                      # Tests d'intégration
│   │   ├── database/
│   │   ├── external_services/
│   │   └── api/
│   ├── e2e/                             # Tests end-to-end
│   └── fixtures/                        # Données de test
│
├── scripts/                             # Scripts de déploiement et maintenance
│   ├── deployment/
│   ├── maintenance/
│   └── development/
│
├── migrations/                          # Migrations de base de données
│   └── alembic/
│
└── config/                              # Fichiers de configuration
    ├── development.yaml
    ├── testing.yaml
    └── production.yaml
```

## 🎯 **Objectifs de la Réorganisation**

### **1. Clean Architecture**
- **Séparation claire** des responsabilités par couche
- **Indépendance** entre les couches
- **Inversion des dépendances** (Domain -> Application -> Infrastructure)

### **2. Domain-Driven Design (DDD)**
- **Entités** et **Value Objects** bien définis
- **Services métier** dans le domain
- **Repositories** comme interfaces

### **3. CQRS (Command Query Responsibility Segregation)**
- **Commands** pour les modifications
- **Queries** pour les lectures
- **Handlers** pour traiter les commandes/requêtes