
# Architecture Complète PWA + Backend - Plateforme Trading

Pour les standards de développement, voir : [Guide de développement](development.md)

Pour la définition des termes techniques, voir : [Glossaire](glossaire.md)

## Vue d'ensemble de l'architecture

Cette architecture suit les principes de **Clean Architecture**, **Domain-Driven Design**, et **CQRS** pour créer une application de trading moderne, scalable et entièrement gratuite.

## 1. Dogmes architecturaux et principes fondamentaux

### Principe de Clean Architecture (Uncle Bob)

```text
┌─────────────────────────────────────────────────────────┐
│                    FRAMEWORKS & DRIVERS                 │
│  ┌─────────────────────────────────────────────────────┐│
│  │              INTERFACE ADAPTERS                     ││
│  │  ┌─────────────────────────────────────────────────┐││
│  │  │            APPLICATION BUSINESS RULES           │││
│  │  │  ┌─────────────────────────────────────────────┐│││
│  │  │  │         ENTERPRISE BUSINESS RULES          ││││
│  │  │  │                                             ││││
│  │  │  │  ┌─────────────────────────────────────┐    ││││
│  │  │  │  │            ENTITIES             │    ││││
│  │  │  │  │  Portfolio, Investment,        │    ││││
│  │  │  │  │  Signal, MarketData           │    ││││
│  │  │  │  └─────────────────────────────────────┘    ││││
│  │  │  │                                             ││││
│  │  │  │         USE CASES                           ││││
│  │  │  │  FindBestInvestments                        ││││
│  │  │  │  AnalyzePortfolio                          ││││
│  │  │  │  GenerateSignals                           ││││
│  │  │  └─────────────────────────────────────────────┘│││
│  │  │                                                 │││
│  │  │              CONTROLLERS & PRESENTERS           │││
│  │  │  FastAPI Routes, GraphQL Resolvers              │││
│  │  └─────────────────────────────────────────────────┘││
│  │                                                     ││
│  │                    GATEWAYS                         ││
│  │  YFinance Adapter, Database Repository             ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│                  EXTERNAL INTERFACES                    │
│  Web UI, Database, APIs, File System                   │
└─────────────────────────────────────────────────────────┘

      ▲                    ▲                    ▲
      │                    │                    │
   STABLE              POLICIES              DETAILS
   (Business)          (Abstract)           (Concrete)
```

### Règles de dépendance

1. **Règle d'inversion** : Les dépendances pointent toujours vers l'intérieur
2. **Isolation métier** : La logique business ne dépend d'aucune technologie
3. **Ports et adapters** : Interfaces abstraites pour tous les accès externes

## 2. Architecture globale du système

```text
┌─────────────────────────────────────────────────────────────────────┐
│                              PWA CLIENT                             │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   PRESENTATION   │  │      DOMAIN      │  │   INFRASTRUCTURE │   │
│  │                  │  │                  │  │                  │   │
│  │ ┌──────────────┐ │  │ ┌──────────────┐ │  │ ┌──────────────┐ │   │
│  │ │ Components   │ │  │ │ Models       │ │  │ │ HTTP Client  │ │   │
│  │ │ Views        │ │  │ │ Validators   │ │  │ │ Cache        │ │   │
│  │ │ Hooks        │ │  │ │ Business     │ │  │ │ Storage      │ │   │
│  │ └──────────────┘ │  │ │ Logic        │ │  │ │ PWA Service  │ │   │
│  └──────────────────┘  │ └──────────────┘ │  │ └──────────────┘ │   │
│                        └──────────────────┘  └──────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    SERVICE WORKER                               │ │
│  │  Caching Strategy • Background Sync • Push Notifications       │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ REST API + WebSocket
                          │
┌─────────────────────────┼───────────────────────────────────────────┐
│                         │           BACKEND API                     │
│                         │                                           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    PRESENTATION LAYER                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │ │
│  │  │FastAPI REST │ │ WebSocket   │ │ GraphQL     │ │ Background│ │ │
│  │  │Controllers  │ │ Handlers    │ │ Schema      │ │ Tasks     │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                   APPLICATION LAYER                             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │ │
│  │  │ Use Cases   │ │ Commands    │ │ Queries     │ │ Events    │ │ │
│  │  │ Services    │ │ (CQRS)      │ │ (CQRS)      │ │ Handlers  │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      DOMAIN LAYER                               │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │ │
│  │  │ Entities    │ │ Aggregates  │ │ Value       │ │ Domain    │ │ │
│  │  │ (Pure)      │ │ (Business)  │ │ Objects     │ │ Services  │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                  INFRASTRUCTURE LAYER                           │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │ │
│  │  │ Database    │ │ YFinance    │ │ Cache       │ │ External  │ │ │
│  │  │ Repository  │ │ Adapter     │ │ Redis       │ │ APIs      │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Design Patterns utilisés avec schémas

.. tabs::
   
  .. tab:: Diagramme UML (PlantUML)
      
    .. uml::
      :caption: Repository Pattern (PlantUML)

      @startuml
      interface IRepository {
        +add(entity)
        +remove(entity)
        +find_by_id(id)
      }
      class PortfolioRepository implements IRepository
      class UnitOfWork {
        +commit()
        +rollback()
      }
      PortfolioRepository --> IRepository
      PortfolioRepository --> UnitOfWork
      @enduml

  .. tab:: Diagramme Mermaid
      
    .. mermaid::
      :caption: Repository Pattern (Mermaid)

      classDiagram
        class IRepository {
         +add(entity)
         +remove(entity)
         +find_by_id(id)
        }
        class PortfolioRepository {
         +commit()
         +rollback()
        }
        IRepository <|-- PortfolioRepository

  .. tab:: Vidéo explicative
      
    .. video:: https://www.youtube.com/watch?v=Pb3opFOnp2g
      :width: 600
      :height: 340
      :align: center

.. grid:: 2
  :gutter: 2

  .. card:: :emoji:`rocket` Performance
    :shadow: md
    :link: https://fastapi.tiangolo.com/
    :link-type: url

    FastAPI propulse l'API backend avec une latence < 100ms.

  .. card:: :emoji:`bar_chart` Monitoring
    :shadow: md

    Logs structurés, alertes Prometheus, dashboards Grafana.

.. bibliography::
  :filter: docname in docnames

```text
┌─────────────────────────────────────────────────────────┐
│                    REPOSITORY PATTERN                   │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   DOMAIN LAYER                      │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │          IPortfolioRepository              │    │ │
│  │  │  ┌─────────────────────────────────────┐   │    │ │
│  │  │  │  + find_by_id(id)                  │   │    │ │
│  │  │  │  + find_by_user(user_id)           │   │    │ │
│  │  │  │  + save(portfolio)                 │   │    │ │
│  │  │  │  + delete(id)                      │   │    │ │
│  │  │  └─────────────────────────────────────┘   │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                            │                             │
│                            │ implements                  │
│                            ▼                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                INFRASTRUCTURE                       │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │       PostgreSQLPortfolioRepository        │    │ │
│  │  │  ┌─────────────────────────────────────┐   │    │ │
│  │  │  │  + __init__(session)               │   │    │ │
│  │  │  │  + find_by_id(id)                  │   │    │ │
│  │  │  │  + save(portfolio)                 │   │    │ │
│  │  │  │  - _map_to_entity()                │   │    │ │
│  │  │  │  - _map_to_model()                 │   │    │ │
│  │  │  └─────────────────────────────────────┘   │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                         │
│           ┌─────────────────────────────────────────┐   │
│           │           UNIT OF WORK                  │   │
│           │  ┌─────────────────────────────────┐    │   │
│           │  │  + begin_transaction()         │    │   │
│           │  │  + commit()                    │    │   │
│           │  │  + rollback()                  │    │   │
│           │  │  + portfolios: IPortfolioRepo  │    │   │
│           │  │  + market_data: IMarketDataRepo│    │   │
│           │  └─────────────────────────────────┘    │   │
│           └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Strategy Pattern pour indicateurs techniques

```text
┌─────────────────────────────────────────────────────────┐
│                    STRATEGY PATTERN                     │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    CONTEXT                          │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │           TechnicalAnalyzer             │    │ │
│  │  │  ┌─────────────────────────────────┐   │    │ │
│  │  │  │  - strategies: List[Strategy]   │   │    │ │
│  │  │  │  + analyze(data, symbol)        │   │    │ │
│  │  │  │  + add_strategy(strategy)       │   │    │ │
│  │  │  │  + remove_strategy(name)        │   │    │ │
│  │  │  └─────────────────────────────────┘   │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                            │                             │
│                            │ uses                        │
│                            ▼                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   STRATEGY                          │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │            IIndicatorStrategy              │    │ │
│  │  │  ┌─────────────────────────────────────┐   │    │ │
│  │  │  │  + calculate(data): Signal         │   │    │ │
│  │  │  │  + name: str                       │   │    │ │
│  │  │  │  + parameters: Dict                │   │    │ │
│  │  │  └─────────────────────────────────────┘   │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                            ▲                             │
│           ┌────────────────┼────────────────┐            │
│           │                │                │            │
│           ▼                ▼                ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ RSIStrategy │  │MACDStrategy │  │ SMAStrategy │       │
│  │             │  │             │  │             │       │
│  │ + calculate │  │ + calculate │  │ + calculate │       │
│  │ + name="RSI"│  │ + name="MACD│  │ + name="SMA"│       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Observer Pattern pour notifications temps réel

```text
┌─────────────────────────────────────────────────────────┐
│                    OBSERVER PATTERN                     │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    SUBJECT                          │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │             MarketDataSubject              │    │ │
│  │  │  ┌─────────────────────────────────────┐   │    │ │
│  │  │  │  - observers: List[Observer]       │   │    │ │
│  │  │  │  + attach(observer)                │   │    │ │
│  │  │  │  + detach(observer)                │   │    │ │
│  │  │  │  + notify(data)                    │   │    │ │
│  │  │  │  + update_price(symbol, price)     │   │    │ │
│  │  │  └─────────────────────────────────────┘   │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                            │                             │
│                            │ notifies                    │
│                            ▼                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   OBSERVERS                         │ │
│  │                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│ │
│  │  │ AlertObserver│  │ ChartObserver│  │ PushObserver ││ │
│  │  │              │  │              │  │              ││ │
│  │  │ + update()   │  │ + update()   │  │ + update()   ││ │
│  │  │ - check_     │  │ - update_    │  │ - send_      ││ │
│  │  │   alerts()   │  │   chart()    │  │   notification()│ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘│ │
│  └─────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                   WEBSOCKET                         │ │
│  │  Client 1 ←→ Client 2 ←→ Client 3 ←→ Client N       │ │
│  │    (PWA)       (PWA)       (PWA)       (PWA)        │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.4 CQRS (Command Query Responsibility Segregation)

```text
┌─────────────────────────────────────────────────────────┐
│                      CQRS PATTERN                       │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    API LAYER                        │ │
│  │  ┌──────────────────┐    ┌──────────────────────┐   │ │
│  │  │   COMMANDS       │    │       QUERIES        │   │ │
│  │  │                  │    │                      │   │ │
│  │  │ POST /portfolio  │    │  GET /portfolio/:id  │   │ │
│  │  │ PUT /investments │    │  GET /investments    │   │ │
│  │  │ DELETE /alerts   │    │  GET /market-data    │   │ │
│  │  └──────────────────┘    └──────────────────────┘   │ │
│  └─────────────────────────────────────────────────────┘ │
│                   │                    │                 │
│                   ▼                    ▼                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                APPLICATION LAYER                    │ │
│  │                                                     │ │
│  │  ┌──────────────────┐    ┌──────────────────────┐   │ │
│  │  │ COMMAND HANDLERS │    │   QUERY HANDLERS     │   │ │
│  │  │                  │    │                      │   │ │
│  │  │ + handle_create_ │    │ + handle_get_        │   │ │
│  │  │   portfolio()    │    │   portfolio()        │   │ │
│  │  │ + handle_add_    │    │ + handle_search_     │   │ │
│  │  │   investment()   │    │   investments()      │   │ │
│  │  └──────────────────┘    └──────────────────────┘   │ │
│  └─────────────────────────────────────────────────────┘ │
│                   │                    │                 │
│                   ▼                    ▼                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │               STORAGE LAYER                         │ │
│  │                                                     │ │
│  │  ┌──────────────────┐    ┌──────────────────────┐   │ │
│  │  │   WRITE MODEL    │    │     READ MODEL       │   │ │
│  │  │                  │    │                      │   │ │
│  │  │ PostgreSQL       │    │ Materialized Views   │   │ │
│  │  │ Transactional    │    │ Read-Optimized       │   │ │
│  │  │ Normalized       │    │ Denormalized         │   │ │
│  │  └──────────────────┘    └──────────────────────┘   │ │
│  └─────────────────────────────────────────────────────┘ │
│                   │                                      │
│                   ▼                                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                EVENT STORE                          │ │
│  │  Portfolio Created • Investment Added • Alert Set   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 4. Structure complète du projet

```text
trading_platform/
├── 📁 frontend/                     # PWA React Application
│   ├── public/
│   │   ├── manifest.json            # PWA manifest
│   │   ├── sw.js                    # Service Worker
│   │   └── icons/                   # PWA icons
│   ├── src/
│   │   ├── 📁 components/           # UI Components
│   │   │   ├── common/
│   │   │   │   ├── Chart.tsx
│   │   │   │   ├── DataTable.tsx
│   │   │   │   └── LoadingSpinner.tsx
│   │   │   ├── portfolio/
│   │   │   │   ├── PortfolioSummary.tsx
│   │   │   │   ├── PositionsList.tsx
│   │   │   │   └── PerformanceChart.tsx
│   │   │   └── trading/
│   │   │       ├── Watchlist.tsx
│   │   │       ├── Screener.tsx
│   │   │       └── SignalsList.tsx
│   │   ├── 📁 pages/                # Route Components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Portfolio.tsx
│   │   │   ├── Analysis.tsx
│   │   │   └── Settings.tsx
│   │   ├── 📁 hooks/                # Custom Hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── usePortfolio.ts
│   │   │   └── useMarketData.ts
│   │   ├── 📁 stores/               # State Management (Zustand)
│   │   │   ├── portfolioStore.ts
│   │   │   ├── marketDataStore.ts
│   │   │   └── authStore.ts
│   │   ├── 📁 services/             # API Layer
│   │   │   ├── api.ts               # HTTP Client
│   │   │   ├── websocket.ts         # WebSocket Client
│   │   │   └── cache.ts             # Client-side Cache
│   │   ├── 📁 utils/                # Utilities
│   │   │   ├── formatters.ts
│   │   │   ├── calculations.ts
│   │   │   └── constants.ts
│   │   └── 📁 types/                # TypeScript Types
│   │       ├── portfolio.ts
│   │       ├── market-data.ts
│   │       └── api.ts
│   ├── package.json
│   ├── vite.config.ts               # Vite Configuration
│   ├── tailwind.config.js           # Tailwind CSS
│   └── tsconfig.json
│
├── 📁 backend/                      # Python FastAPI Backend
│   ├── 📁 src/
│   │   ├── 📁 domain/               # 🎯 DOMAIN LAYER
│   │   │   ├── 📁 entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── portfolio.py
│   │   │   │   ├── investment.py
│   │   │   │   ├── market_data.py
│   │   │   │   └── user.py
│   │   │   ├── 📁 value_objects/
│   │   │   │   ├── money.py
│   │   │   │   ├── price.py
│   │   │   │   ├── signal.py
│   │   │   │   └── timeframe.py
│   │   │   ├── 📁 services/
│   │   │   │   ├── portfolio_service.py
│   │   │   │   ├── risk_calculator.py
│   │   │   │   └── performance_analyzer.py
│   │   │   ├── 📁 repositories/     # Interfaces (Ports)
│   │   │   │   ├── portfolio_repository.py
│   │   │   │   ├── market_data_repository.py
│   │   │   │   └── user_repository.py
│   │   │   └── 📁 events/
│   │   │       ├── portfolio_events.py
│   │   │       └── market_events.py
│   │   │
│   │   ├── 📁 application/          # 🎯 APPLICATION LAYER
│   │   │   ├── 📁 use_cases/
│   │   │   │   ├── find_investments.py
│   │   │   │   ├── analyze_portfolio.py
│   │   │   │   ├── create_alert.py
│   │   │   │   └── generate_report.py
│   │   │   ├── 📁 commands/         # CQRS Commands
│   │   │   │   ├── portfolio_commands.py
│   │   │   │   └── investment_commands.py
│   │   │   ├── 📁 queries/          # CQRS Queries
│   │   │   │   ├── portfolio_queries.py
│   │   │   │   └── market_data_queries.py
│   │   │   ├── 📁 services/
│   │   │   │   ├── technical_analyzer.py
│   │   │   │   ├── fundamental_analyzer.py
│   │   │   │   └── signal_generator.py
│   │   │   └── 📁 dto/
│   │   │       ├── portfolio_dto.py
│   │   │       └── investment_dto.py
│   │   │
│   │   ├── 📁 infrastructure/       # 🎯 INFRASTRUCTURE LAYER
│   │   │   ├── 📁 web/              # API Layer
│   │   │   │   ├── main.py          # FastAPI App
│   │   │   │   ├── 📁 routers/
│   │   │   │   │   ├── portfolio.py
│   │   │   │   │   ├── market_data.py
│   │   │   │   │   ├── analysis.py
│   │   │   │   │   └── websocket.py
│   │   │   │   ├── 📁 middleware/
│   │   │   │   │   ├── cors.py
│   │   │   │   │   ├── auth.py
│   │   │   │   │   └── rate_limiting.py
│   │   │   │   └── dependencies.py
│   │   │   ├── 📁 persistence/      # Database Layer
│   │   │   │   ├── 📁 sqlalchemy/
│   │   │   │   │   ├── models.py
│   │   │   │   │   ├── repositories.py
│   │   │   │   │   └── session.py
│   │   │   │   └── 📁 migrations/   # Alembic
│   │   │   │       └── versions/
│   │   │   ├── 📁 external/         # External APIs
│   │   │   │   ├── yfinance_client.py
│   │   │   │   └── market_data_adapter.py
│   │   │   ├── 📁 cache/            # Redis Cache
│   │   │   │   └── redis_client.py
│   │   │   └── 📁 background/       # Background Tasks
│   │   │       ├── celery_app.py
│   │   │       └── tasks.py
│   │   │
│   │   ├── 📁 indicators/           # Technical Indicators
│   │   │   ├── 📁 technical/
│   │   │   │   ├── trend.py         # SMA, EMA, MACD
│   │   │   │   ├── momentum.py      # RSI, Stochastic
│   │   │   │   ├── volatility.py    # Bollinger, ATR
│   │   │   │   └── volume.py        # OBV, VWAP
│   │   │   └── 📁 fundamental/
│   │   │       ├── ratios.py        # P/E, P/B, ROE
│   │   │       └── growth.py        # Revenue growth
│   │   │
│   │   └── 📁 shared/               # Shared Utilities
│   │       ├── 📁 config/
│   │       │   └── settings.py
│   │       ├── 📁 exceptions/
│   │       │   └── business_exceptions.py
│   │       └── 📁 utils/
│   │           ├── datetime_utils.py
│   │           └── financial_math.py
│   │
│   ├── tests/                       # Tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── 📁 docker/                       # Docker Configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── 📁 scripts/                      # Deployment Scripts
│   ├── setup_vps.sh
│   ├── deploy.sh
│   └── backup.sh
│
└── 📁 docs/                         # Documentation
    ├── api.md
    ├── architecture.md
    └── deployment.md
```

## 5. Implémentation détaillée des composants clés

### 5.1 Domain Layer - Entités métier pures

```python
# src/domain/entities/portfolio.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from .base import AggregateRoot
from ..value_objects.money import Money
from ..value_objects.signal import Signal
from ..events.portfolio_events import PortfolioCreatedEvent, InvestmentAddedEvent

@dataclass
class Portfolio(AggregateRoot):
    """
    Aggregate racine pour la gestion de portefeuille
    Encapsule toute la logique métier liée au portfolio
    """
    id: 'PortfolioId'
    user_id: 'UserId'
    name: str
    base_currency: str
    cash_balance: Money
    created_at: datetime
    _positions: Dict[str, 'Position'] = field(default_factory=dict)
    _risk_limits: 'RiskLimits' = field(default_factory=lambda: RiskLimits())
    
    def __post_init__(self):
        """Initialisation post-création"""
        super().__post_init__()
        if not hasattr(self, '_domain_events'):
            self._domain_events = []
    
    def add_investment(self, symbol: str, quantity: int, 
                      price: Money, transaction_date: datetime) -> 'Investment':
        """
        Business logic : Ajout d'investissement avec validation métier
        
        Rules:
        - Vérification liquidités suffisantes
        - Respect limites de position (max 10% par actif)
        - Calcul impact diversification
        """
        # Règle métier : Liquidités suffisantes
        total_cost = Money(price.amount * Decimal(quantity), price.currency)
        if total_cost > self.cash_balance:
            raise InsufficientFundsException(
                f"Insufficient funds. Required: {total_cost}, Available: {self.cash_balance}"
            )
        
        # Règle métier : Limite de position (10% max)
        portfolio_value = self.calculate_total_value()
        position_percentage = (total_cost.amount / portfolio_value.amount) * 100
        if position_percentage > self._risk_limits.max_position_percentage:
            raise PositionLimitExceededException(
                f"Position would exceed {self._risk_limits.max_position_percentage}% limit"
            )
        
        # Création investment et mise à jour positions
        investment = Investment.create(
            symbol=symbol,
            quantity=quantity,
            price=price,
            transaction_date=transaction_date,
            transaction_type=TransactionType.BUY
        )
        
        # Mise à jour état portfolio
        self._update_position(investment)
        self._update_cash_balance(-total_cost.amount)
        
        # Event pour CQRS
        self._add_domain_event(InvestmentAddedEvent(
            portfolio_id=self.id,
            investment_id=investment.id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            timestamp=transaction_date
        ))
        
        return investment
    
    def calculate_performance_metrics(self, market_prices: Dict[str, Money]) -> 'PerformanceMetrics':
        """
        Calcul métriques de performance avancées
        
        Retourne:
        - Valeur totale portfolio
        - Return journalier/mensuel/annuel
        - Volatilité (écart-type returns)
        - Sharpe ratio
        - Maximum drawdown
        - Beta (vs marché)
        """
        current_value = self.calculate_current_value(market_prices)
        
        # Calculs de performance
        daily_return = self._calculate_daily_return(market_prices)
        monthly_return = self._calculate_monthly_return(market_prices)
        annual_return = self._calculate_annual_return(market_prices)
        
        # Calculs de risque
        volatility = self._calculate_volatility()
        sharpe_ratio = self._calculate_sharpe_ratio(annual_return, volatility)
        max_drawdown = self._calculate_max_drawdown()
        beta = self._calculate_beta()
        
        return PerformanceMetrics(
            total_value=current_value,
            daily_return=daily_return,
            monthly_return=monthly_return,
            annual_return=annual_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            beta=beta,
            last_updated=datetime.utcnow()
        )
    
    def generate_rebalancing_signals(self, target_allocation: Dict[str, float],
                                   current_prices: Dict[str, Money]) -> List[Signal]:
        """
        Génère signaux de rééquilibrage basés sur allocation cible
        
        Args:
            target_allocation: Dict[symbol, percentage] - Allocation souhaitée
            current_prices: Prix actuels pour valorisation
            
        Returns:
            Liste de signaux BUY/SELL pour rééquilibrage
        """
        signals = []
        current_allocation = self._calculate_current_allocation(current_prices)
        total_value = self.calculate_current_value(current_prices)
        
        for symbol, target_pct in target_allocation.items():
            current_pct = current_allocation.get(symbol, 0.0)
            deviation = target_pct - current_pct
            
            # Seuil de rééquilibrage (éviter micro-ajustements)
            if abs(deviation) > 0.05:  # 5% de déviation minimum
                target_value = total_value.amount * Decimal(target_pct / 100)
                current_position = self._positions.get(symbol)
                
                if current_position:
                    current_value = current_position.calculate_market_value(current_prices[symbol])
                    amount_difference = target_value - current_value.amount
                else:
                    amount_difference = target_value
                
                action = SignalAction.BUY if amount_difference > 0 else SignalAction.SELL
                confidence_score = min(abs(deviation) / 0.1, 1.0)  # Max confidence à 10% déviation
                
                signals.append(Signal(
                    symbol=symbol,
                    action=action,
                    confidence_score=confidence_score,
                    price_target=current_prices[symbol],
                    amount=Money(abs(amount_difference), self.base_currency),
                    rationale=f"Rebalancing: current {current_pct:.1f}% vs target {target_pct:.1f}%",
                    generated_at=datetime.utcnow()
                ))
        
        return signals
    
    def _calculate_sharpe_ratio(self, annual_return: float, volatility: float, 
                               risk_free_rate: float = 0.02) -> float:
        """Calcul Sharpe ratio (rendement ajusté du risque)"""
        if volatility == 0:
            return 0.0
        return (annual_return - risk_free_rate) / volatility
    
    def _calculate_max_drawdown(self) -> float:
        """Calcul maximum drawdown (perte maximale depuis un pic)"""
        # Implémentation simplifiée - nécessiterait historique valorisations
        return 0.0  # À implémenter avec données historiques
    
    def _update_position(self, investment: 'Investment'):
        """Mise à jour position suite à transaction"""
        symbol = investment.symbol
        
        if symbol in self._positions:
            self._positions[symbol].add_transaction(investment)
        else:
            self._positions[symbol] = Position.from_investment(investment)
    
    def _update_cash_balance(self, amount: Decimal):
        """Mise à jour solde cash"""
        new_amount = self.cash_balance.amount + amount
        if new_amount < 0:
            raise InsufficientFundsException("Insufficient cash balance")
        
        self.cash_balance = Money(new_amount, self.cash_balance.currency)

@dataclass(frozen=True)
class Position:
    """Value object représentant une position dans un actif"""
    symbol: str
    quantity: int
    average_price: Money
    first_purchase_date: datetime
    last_update: datetime
    
    def calculate_market_value(self, current_price: Money) -> Money:
        """Valeur de marché actuelle"""
        return Money(
            current_price.amount * Decimal(self.quantity),
            current_price.currency
        )
    
    def calculate_unrealized_pnl(self, current_price: Money) -> Money:
        """Plus/moins-value latente"""
        market_value = self.calculate_market_value(current_price)
        book_value = Money(
            self.average_price.amount * Decimal(self.quantity),
            self.average_price.currency
        )
        return Money(
            market_value.amount - book_value.amount,
            market_value.currency
        )
    
    def calculate_return_percentage(self, current_price: Money) -> float:
        """Rendement en pourcentage"""
        if self.average_price.amount == 0:
            return 0.0
        return float((current_price.amount - self.average_price.amount) / self.average_price.amount * 100)
```

### 5.2 Application Layer - Use Cases métier

```python
# src/application/use_cases/find_investments.py
from typing import List, Dict
from ..dto.investment_dto import FindInvestmentsRequest, InvestmentRecommendations
from ...domain.repositories.portfolio_repository import IPortfolioRepository
from ...domain.repositories.market_data_repository import IMarketDataRepository
from ..services.technical_analyzer import TechnicalAnalyzer
from ..services.fundamental_analyzer import FundamentalAnalyzer
from ..services.signal_generator import SignalGenerator

class FindBestInvestmentsUseCase:
    """
    Use Case principal : Trouver les meilleurs investissements
    
    Orchestration complète :
    1. Récupération données marché (yfinance)
    2. Analyse technique multi-indicateurs
    3. Analyse fondamentale 
    4. Scoring et ranking des opportunités
    5. Filtrage par contraintes portfolio
    """
    
    def __init__(self, 
                 portfolio_repo: IPortfolioRepository,
                 market_data_repo: IMarketDataRepository,
                 technical_analyzer: TechnicalAnalyzer,
                 fundamental_analyzer: FundamentalAnalyzer,
                 signal_generator: SignalGenerator):
        self._portfolio_repo = portfolio_repo
        self._market_data_repo = market_data_repo
        self._technical_analyzer = technical_analyzer
        self._fundamental_analyzer = fundamental_analyzer
        self._signal_generator = signal_generator
    
    async def execute(self, request: FindInvestmentsRequest) -> InvestmentRecommendations:
        """Exécution du cas d'usage complet"""
        
        # 1. Validation et récupération portfolio
        portfolio = await self._portfolio_repo.find_by_id(request.portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundException(f"Portfolio {request.portfolio_id} not found")
        
        # 2. Récupération données de marché (parallèle)
        symbols = request.symbols or self._get_default_universe()
        market_data_tasks = [
            self._market_data_repo.get_price_data(symbol, request.timeframe)
            for symbol in symbols
        ]
        market_data_list = await asyncio.gather(*market_data_tasks, return_exceptions=True)
        
        # Filtrage erreurs de récupération
        valid_market_data = {}
        for symbol, data in zip(symbols, market_data_list):
            if not isinstance(data, Exception) and data is not None:
                valid_market_data[symbol] = data
        
        if not valid_market_data:
            raise MarketDataException("No market data available for analysis")
        
        # 3. Analyse technique parallèle
        technical_analysis_tasks = [
            self._technical_analyzer.analyze(symbol, data)
            for symbol, data in valid_market_data.items()
        ]
        technical_signals = await asyncio.gather(*technical_analysis_tasks)
        
        # 4. Analyse fondamentale parallèle  
        fundamental_analysis_tasks = [
            self._fundamental_analyzer.analyze(symbol)
            for symbol in valid_market_data.keys()
        ]
        fundamental_signals = await asyncio.gather(*fundamental_analysis_tasks)
        
        # 5. Combinaison et scoring des signaux
        combined_signals = self._signal_generator.combine_signals(
            technical_signals=dict(zip(valid_market_data.keys(), technical_signals)),
            fundamental_signals=dict(zip(valid_market_data.keys(), fundamental_signals)),
            market_context=self._get_market_context()
        )
        
        # 6. Filtrage par contraintes portfolio
        filtered_signals = self._apply_portfolio_constraints(
            signals=combined_signals,
            portfolio=portfolio,
            current_prices={s: d.latest_price for s, d in valid_market_data.items()}
        )
        
        # 7. Ranking final et sélection top N
        ranked_signals = self._rank_and_select(
            signals=filtered_signals,
            max_results=request.max_recommendations
        )
        
        # 8. Calcul métriques complémentaires
        portfolio_impact = self._calculate_portfolio_impact(
            portfolio=portfolio,
            signals=ranked_signals,
            current_prices={s: d.latest_price for s, d in valid_market_data.items()}
        )
        
        risk_assessment = self._assess_combined_risk(ranked_signals)
        
        return InvestmentRecommendations(
            signals=ranked_signals,
            portfolio_impact=portfolio_impact,
            risk_assessment=risk_assessment,
            market_context=self._get_market_context(),
            generated_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(hours=4)  # Validité 4h
        )
    
    def _apply_portfolio_constraints(self, signals: List[Signal], 
                                   portfolio: Portfolio,
                                   current_prices: Dict[str, Money]) -> List[Signal]:
        """
        Filtrage des signaux selon contraintes portfolio
        
        Contraintes :
        - Diversification maximum (10% par position)
        - Liquidités disponibles
        - Corrélation avec positions existantes
        - Exposition sectorielle
        """
        filtered_signals = []
        portfolio_value = portfolio.calculate_current_value(current_prices)
        
        for signal in signals:
            # Contrainte : Liquidités
            if signal.action == SignalAction.BUY:
                required_amount = signal.amount or Money(
                    portfolio_value.amount * Decimal('0.05'),  # 5% par défaut
                    portfolio.base_currency
                )
                
                if required_amount > portfolio.cash_balance:
                    continue  # Skip si pas assez de liquidités
                
                # Contrainte : Limite position (10% max)
                position_percentage = (required_amount.amount / portfolio_value.amount) * 100
                if position_percentage > 10.0:
                    continue
            
            # Contrainte : Pas de doublon avec positions existantes (si signal faible)
            if signal.symbol in portfolio._positions and signal.confidence_score < 0.7:
                continue
            
            filtered_signals.append(signal)
        
        return filtered_signals
    
    def _rank_and_select(self, signals: List[Signal], max_results: int) -> List[Signal]:
        """Ranking final basé sur score composite"""
        
        # Score composite : Technical (40%) + Fundamental (40%) + Market Context (20%)
        for signal in signals:
            technical_weight = 0.4
            fundamental_weight = 0.4
            context_weight = 0.2
            
            # Score technique déjà dans confidence_score
            technical_score = signal.confidence_score
            
            # Score fondamental (à récupérer depuis metadata)
            fundamental_score = signal.metadata.get('fundamental_score', 0.5)
            
            # Score contexte marché
            market_context_score = self._calculate_market_context_score(signal.symbol)
            
            # Score composite final
            signal.composite_score = (
                technical_score * technical_weight +
                fundamental_score * fundamental_weight +
                market_context_score * context_weight
            )
        
        # Tri par score composite décroissant
        ranked_signals = sorted(signals, key=lambda s: s.composite_score, reverse=True)
        
        return ranked_signals[:max_results]
    
    def _calculate_portfolio_impact(self, portfolio: Portfolio, 
                                  signals: List[Signal],
                                  current_prices: Dict[str, Money]) -> Dict:
        """Calcul impact des signaux sur le portfolio"""
        
        current_metrics = portfolio.calculate_performance_metrics(current_prices)
        
        # Simulation ajout des investissements recommandés
        simulated_portfolio = self._simulate_investments(portfolio, signals, current_prices)
        simulated_metrics = simulated_portfolio.calculate_performance_metrics(current_prices)
        
        return {
            'expected_return_change': simulated_metrics.annual_return - current_metrics.annual_return,
            'volatility_change': simulated_metrics.volatility - current_metrics.volatility,
            'sharpe_improvement': simulated_metrics.sharpe_ratio - current_metrics.sharpe_ratio,
            'diversification_effect': self._calculate_diversification_effect(portfolio, signals),
            'total_investment_amount': sum(s.amount.amount for s in signals if s.amount),
        }
    
    def _get_default_universe(self) -> List[str]:
        """Univers d'investissement par défaut (actions liquides)"""
        return [
            # Tech US
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS',
            # Indices ETFs
            'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO',
            # Secteurs
            'XLF', 'XLK', 'XLE', 'XLV', 'XLI',
            # International
            'EWZ', 'EWJ', 'FXI', 'EWG'
        ]
```

### 5.3 Infrastructure Layer - Optimisation yfinance

```python
# src/infrastructure/external/yfinance_client.py
import yfinance as yf
import asyncio
import aiohttp
from typing import Dict, List, Optional
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class YFinanceOptimizedClient:
    """
    Client yfinance optimisé avec :
    - Rate limiting intelligent
    - Retry avec backoff exponentiel  
    - Cache Redis intégré
    - Requêtes batch
    - Gestion erreurs robuste
    """
    
    def __init__(self, redis_client, max_requests_per_minute: int = 2000):
        self.redis_client = redis_client
        self.max_requests_per_minute = max_requests_per_minute
        self._request_timestamps = []
        self._session = None
    
    async def __aenter__(self):
        """Context manager pour session HTTP réutilisable"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def get_stock_data(self, symbol: str, period: str = "1y", 
                           interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Récupération données stock avec retry et cache
        
        Args:
            symbol: Ticker symbol (ex: 'AAPL')
            period: Période ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Intervalle ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        """
        
        # 1. Check cache Redis first
        cache_key = f"yfinance:stock:{symbol}:{period}:{interval}"
        cached_data = await self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {symbol}")
            return cached_data
        
        # 2. Rate limiting check
        await self._check_rate_limit()
        
        # 3. Fetch from yfinance
        try:
            logger.info(f"Fetching {symbol} data from yfinance")
            
            # Utilisation thread pool pour éviter blocking
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                self._fetch_yfinance_data, 
                symbol, period, interval
            )
            
            if data is not None and not data.empty:
                # Cache pour éviter re-fetch (TTL selon période)
                cache_ttl = self._get_cache_ttl(interval)
                await self._store_in_cache(cache_key, data, cache_ttl)
                
                logger.info(f"Successfully fetched {len(data)} records for {symbol}")
                return data
            else:
                logger.warning(f"No data returned for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {str(e)}")
            raise
    
    async def get_multiple_stocks_batch(self, symbols: List[str], 
                                      period: str = "1y", 
                                      interval: str = "1d",
                                      max_concurrent: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Récupération batch de plusieurs stocks avec limite concurrence
        
        Optimisations :
        - Limite requêtes concurrentes
        - Cache partagé entre symboles  
        - Gestion erreurs par symbole
        - Progress tracking
        """
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_single(symbol: str) -> tuple[str, Optional[pd.DataFrame]]:
            async with semaphore:
                try:
                    data = await self.get_stock_data(symbol, period, interval)
                    return symbol, data
                except Exception as e:
                    logger.error(f"Failed to fetch {symbol}: {str(e)}")
                    return symbol, None
        
        # Lancement requêtes parallèles
        tasks = [fetch_single(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrage résultats valides
        stock_data = {}
        successful_fetches = 0
        
        for result in results:
            if isinstance(result, tuple):
                symbol, data = result
                if data is not None:
                    stock_data[symbol] = data
                    successful_fetches += 1
        
        logger.info(f"Batch fetch completed: {successful_fetches}/{len(symbols)} successful")
        return stock_data
    
    async def get_real_time_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Prix temps réel avec cache très court (30 secondes)
        Utilise l'API yfinance.download pour plus d'efficacité
        """
        
        # Check cache en masse
        cache_keys = [f"quote:{symbol}" for symbol in symbols]
        cached_quotes = await self.redis_client.mget(cache_keys)
        
        fresh_symbols = []
        quotes = {}
        
        # Séparer données cachées vs à récupérer
        for i, (symbol, cached) in enumerate(zip(symbols, cached_quotes)):
            if cached:
                quotes[symbol] = json.loads(cached)
            else:
                fresh_symbols.append(symbol)
        
        # Fetch données manquantes
        if fresh_symbols:
            try:
                # yfinance batch download (plus efficace)
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: yf.download(
                        tickers=' '.join(fresh_symbols),
                        period='1d',
                        interval='1m',
                        progress=False
                    )
                )
                
                # Extraction derniers prix
                for symbol in fresh_symbols:
                    if symbol in data.columns.levels[1]:
                        latest = data.xs(symbol, axis=1, level=1).iloc[-1]
                        quote = {
                            'symbol': symbol,
                            'price': float(latest['Close']),
                            'change': float(latest['Close'] - data.xs(symbol, axis=1, level=1)['Close'].iloc[-2]),
                            'change_percent': float((latest['Close'] / data.xs(symbol, axis=1, level=1)['Close'].iloc[-2] - 1) * 100),
                            'volume': int(latest['Volume']),
                            'timestamp': datetime.now().isoformat()
                        }
                        quotes[symbol] = quote
                        
                        # Cache 30 secondes
                        await self.redis_client.setex(
                            f"quote:{symbol}", 30, json.dumps(quote)
                        )
                
            except Exception as e:
                logger.error(f"Real-time quotes fetch failed: {str(e)}")
        
        return quotes
    
    async def get_company_info_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Informations fondamentales batch (mise en cache longue)
        
        Données récupérées :
        - Infos générales (secteur, industrie, employees)
        - Ratios financiers (P/E, P/B, ROE, etc.)
        - Données bilancières
        """
        
        company_info = {}
        
        for symbol in symbols:
            cache_key = f"company_info:{symbol}"
            cached_info = await self._get_from_cache(cache_key)
            
            if cached_info is not None:
                company_info[symbol] = cached_info
                continue
            
            try:
                await self._check_rate_limit()
                
                # Fetch company info
                loop = asyncio.get_event_loop()
                ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
                info = await loop.run_in_executor(None, lambda: ticker.info)
                
                if info:
                    # Filtrer données utiles uniquement
                    filtered_info = {
                        'symbol': symbol,
                        'sector': info.get('sector'),
                        'industry': info.get('industry'),
                        'marketCap': info.get('marketCap'),
                        'enterpriseValue': info.get('enterpriseValue'),
                        'peRatio': info.get('trailingPE'),
                        'forwardPE': info.get('forwardPE'),
                        'pbRatio': info.get('priceToBook'),
                        'pegRatio': info.get('pegRatio'),
                        'roe': info.get('returnOnEquity'),
                        'roa': info.get('returnOnAssets'),
                        'profitMargins': info.get('profitMargins'),
                        'revenueGrowth': info.get('revenueGrowth'),
                        'earningsGrowth': info.get('earningsGrowth'),
                        'debtToEquity': info.get('debtToEquity'),
                        'beta': info.get('beta'),
                        'dividendYield': info.get('dividendYield'),
                        'payoutRatio': info.get('payoutRatio'),
                        'lastUpdate': datetime.now().isoformat()
                    }
                    
                    company_info[symbol] = filtered_info
                    
                    # Cache 24h (données fondamentales changent lentement)
                    await self._store_in_cache(cache_key, filtered_info, 86400)
                
            except Exception as e:
                logger.error(f"Company info fetch failed for {symbol}: {str(e)}")
                continue
        
        return company_info
    
    def _fetch_yfinance_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Fetch synchrone yfinance (utilisée dans thread pool)"""
        ticker = yf.Ticker(symbol)
        return ticker.history(
            period=period, 
            interval=interval,
            auto_adjust=True,
            prepost=True,
            repair=True  # Fix données manquantes
        )
    
    async def _check_rate_limit(self):
        """Rate limiting intelligent basé sur fenêtre glissante"""
        now = datetime.now()
        
        # Nettoyer timestamps anciens (> 1 minute)
        cutoff = now - timedelta(minutes=1)
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts > cutoff
        ]
        
        # Vérifier limite
        if len(self._request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self._request_timestamps[0]).seconds
            logger.warning(f"Rate limit reached, waiting {sleep_time}s")
            await asyncio.sleep(sleep_time)
        
        # Enregistrer nouvelle requête
        self._request_timestamps.append(now)
    
    async def _get_from_cache(self, key: str):
        """Récupération cache avec désérialisation"""
        try:
            cached = await self.redis_client.get(key)
            if cached:
                # Désérialisation DataFrame pandas depuis JSON
                return pd.read_json(cached, orient='index')
        except Exception as e:
            logger.error(f"Cache read error for {key}: {str(e)}")
        return None
    
    async def _store_in_cache(self, key: str, data: pd.DataFrame, ttl: int):
        """Stockage cache avec sérialisation"""
        try:
            # Sérialisation DataFrame -> JSON
            json_data = data.to_json(orient='index')
            await self.redis_client.setex(key, ttl, json_data)
        except Exception as e:
            logger.error(f"Cache write error for {key}: {str(e)}")
    
    def _get_cache_ttl(self, interval: str) -> int:
        """TTL cache selon intervalle de données"""
        ttl_mapping = {
            '1m': 60,      # 1 minute
            '5m': 300,     # 5 minutes  
            '15m': 900,    # 15 minutes
            '1h': 1800,    # 30 minutes
            '1d': 3600,    # 1 heure
            '1wk': 7200,   # 2 heures
            '1mo': 14400   # 4 heures
        }
        return ttl_mapping.get(interval, 3600)

# Utilisation optimisée
async def example_usage():
    """Exemple d'utilisation optimisée du client"""
    
    async with YFinanceOptimizedClient(redis_client) as client:
        
        # 1. Fetch batch de stocks
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        stock_data = await client.get_multiple_stocks_batch(
            symbols=symbols,
            period='6mo',
            interval='1d',
            max_concurrent=5
        )
        
        # 2. Prix temps réel
        quotes = await client.get_real_time_quotes(symbols)
        
        # 3. Données fondamentales
        company_info = await client.get_company_info_batch(symbols)
        
        logger.info(f"Fetched {len(stock_data)} stocks, {len(quotes)} quotes, {len(company_info)} company infos")
```

### 5.4 Frontend PWA - Architecture React

```typescript
// src/stores/portfolioStore.ts (Zustand)
import { create } from 'zustand'
import { persist, subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

interface PortfolioState {
  // État
  portfolios: Portfolio[]
  currentPortfolioId: string | null
  positions: Position[]
  performance: PerformanceMetrics | null
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchPortfolios: () => Promise<void>
  selectPortfolio: (id: string) => void
  addInvestment: (investment: InvestmentRequest) => Promise<void>
  removePosition: (symbol: string) => Promise<void>
  refreshPerformance: () => Promise<void>
  
  // Computed
  getCurrentPortfolio: () => Portfolio | null
  getTotalValue: () => number
  getDailyPnL: () => number
}

const usePortfolioStore = create<PortfolioState>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        // État initial
        portfolios: [],
        currentPortfolioId: null,
        positions: [],
        performance: null,
        isLoading: false,
        error: null,
        
        // Actions
        fetchPortfolios: async () => {
          set((state) => {
            state.isLoading = true
            state.error = null
          })
          
          try {
            const response = await api.get('/portfolios')
            set((state) => {
              state.portfolios = response.data
              state.isLoading = false
              // Auto-select premier portfolio si aucun sélectionné
              if (!state.currentPortfolioId && state.portfolios.length > 0) {
                state.currentPortfolioId = state.portfolios[0].id
              }
            })
          } catch (error) {
            set((state) => {
              state.error = error.message
              state.isLoading = false
            })
          }
        },
        
        selectPortfolio: (id: string) => {
          set((state) => {
            state.currentPortfolioId = id
          })
          // Trigger refresh des positions
          get().refreshPositions()
        },
        
        addInvestment: async (investment: InvestmentRequest) => {
          set((state) => { state.isLoading = true })
          
          try {
            const response = await api.post('/investments', investment)
            set((state) => {
              state.positions.push(response.data)
              state.isLoading = false
            })
            // Refresh performance
            await get().refreshPerformance()
          } catch (error) {
            set((state) => {
              state.error = error.message
              state.isLoading = false
            })
            throw error
          }
        },
        
        refreshPerformance: async () => {
          const currentPortfolio = get().getCurrentPortfolio()
          if (!currentPortfolio) return
          
          try {
            const response = await api.get(`/portfolios/${currentPortfolio.id}/performance`)
            set((state) => {
              state.performance = response.data
            })
          } catch (error) {
            console.error('Performance refresh failed:', error)
          }
        },
        
        // Computed values
        getCurrentPortfolio: () => {
          const { portfolios, currentPortfolioId } = get()
          return portfolios.find(p => p.id === currentPortfolioId) || null
        },
        
        getTotalValue: () => {
          const { performance } = get()
          return performance?.totalValue || 0
        },
        
        getDailyPnL: () => {
          const { performance } = get()
          return performance?.dailyPnL || 0
        }
      })),
      {
        name: 'portfolio-store',
        partialize: (state) => ({
          currentPortfolioId: state.currentPortfolioId,
          // Ne pas persister les données qui peuvent être stale
        })
      }
    )
  )
)

// Auto-refresh performance toutes les 5 minutes
usePortfolioStore.subscribe(
  (state) => state.currentPortfolioId,
  (portfolioId) => {
    if (portfolioId) {
      // Setup interval pour refresh
      const interval = setInterval(() => {
        usePortfolioStore.getState().refreshPerformance()
      }, 5 * 60 * 1000) // 5 minutes
      
      return () => clearInterval(interval)
    }
  }
)

export default usePortfolioStore
```

```typescript
// src/components/portfolio/PortfolioDashboard.tsx
import React, { useEffect, useMemo } from 'react'
import { usePortfolioStore } from '../../stores/portfolioStore'
import { useMarketDataStore } from '../../stores/marketDataStore'
import { formatCurrency, formatPercentage } from '../../utils/formatters'
import { PerformanceChart } from './PerformanceChart'
import { PositionsList } from './PositionsList'
import { RecommendationsList } from './RecommendationsList'

const PortfolioDashboard: React.FC = () => {
  const {
    currentPortfolio,
    performance,
    isLoading,
    fetchPortfolios,
    refreshPerformance,
    getTotalValue,
    getDailyPnL
  } = usePortfolioStore()
  
  const { recommendations, fetchRecommendations } = useMarketDataStore()
  
  // Chargement initial
  useEffect(() => {
    fetchPortfolios()
  }, [])
  
  // Refresh recommendations quand portfolio change
  useEffect(() => {
    if (currentPortfolio?.id) {
      fetchRecommendations(currentPortfolio.id)
    }
  }, [currentPortfolio?.id])
  
  // Métriques calculées
  const metrics = useMemo(() => {
    if (!performance) return null
    
    const totalValue = getTotalValue()
    const dailyPnL = getDailyPnL()
    const dailyReturn = totalValue > 0 ? (dailyPnL / totalValue) * 100 : 0
    
    return {
      totalValue,
      dailyPnL,
      dailyReturn,
      monthlyReturn: performance.monthlyReturn,
      yearlyReturn: performance.yearlyReturn,
      sharpeRatio: performance.sharpeRatio,
      maxDrawdown: performance.maxDrawdown,
      beta: performance.beta
    }
  }, [performance, getTotalValue, getDailyPnL])
  
  if (isLoading || !currentPortfolio) {
    return <div className="flex justify-center items-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  }
  
  return (
    <div className="space-y-6">
      {/* En-tête Portfolio */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">{currentPortfolio.name}</h1>
          <button
            onClick={refreshPerformance}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>
        
        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Valeur Totale"
              value={formatCurrency(metrics.totalValue)}
              className="col-span-2 md:col-span-1"
            />
            <MetricCard
              title="P&L Journalier"
              value={formatCurrency(metrics.dailyPnL)}
              subtitle={formatPercentage(metrics.dailyReturn)}
              trend={metrics.dailyPnL >= 0 ? 'up' : 'down'}
            />
            <MetricCard
              title="Performance Annuelle"
              value={formatPercentage(metrics.yearlyReturn)}
              subtitle="vs benchmark"
            />
            <MetricCard
              title="Sharpe Ratio"
              value={metrics.sharpeRatio?.toFixed(2) || 'N/A'}
              subtitle="Risk-adjusted return"
            />
          </div>
        )}
      </div>
      
      {/* Performance Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Performance</h2>
        <PerformanceChart 
          portfolioId={currentPortfolio.id}
          timeframe="6M"
        />
      </div>
      
      {/* Layout 2 colonnes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Positions actuelles */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Positions</h2>
          <PositionsList portfolioId={currentPortfolio.id} />
        </div>
        
        {/* Recommandations */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Recommandations</h2>
          <RecommendationsList 
            recommendations={recommendations}
            onInvest={(symbol, amount) => {
              // Handle investment action
            }}
          />
        </div>
      </div>
      
      {/* Alerts et News (si espace) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Alertes</h2>
          {/* Alerts component */}
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Market News</h2>
          {/* News component */}
        </div>
      </div>
    </div>
  )
}

const MetricCard: React.FC<{
  title: string
  value: string
  subtitle?: string
  trend?: 'up' | 'down'
  className?: string
}> = ({ title, value, subtitle, trend, className = '' }) => {
  return (
    <div className={`bg-gray-50 rounded-lg p-4 ${className}`}>
      <p className="text-sm text-gray-600 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${
        trend === 'up' ? 'text-green-600' : 
        trend === 'down' ? 'text-red-600' : 'text-gray-900'
      }`}>
        {value}
      </p>
      {subtitle && (
        <p className={`text-sm ${
          trend === 'up' ? 'text-green-600' : 
          trend === 'down' ? 'text-red-600' : 'text-gray-500'
        }`}>
          {subtitle}
        </p>
      )}
    </div>
  )
}

export default PortfolioDashboard
```

## 6. Configuration déploiement VPS

```bash
#!/bin/bash
# scripts/setup_vps.sh - Setup VPS complet

set -e

echo "🚀 Setup Trading Platform VPS"

# 1. Mise à jour système
apt update && apt upgrade -y

# 2. Installation Docker + Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $USER

# 3. Installation Node.js (pour frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 4. Installation Python 3.11
apt install -y python3.11 python3.11-venv python3-pip

# 5. Installation PostgreSQL
apt install -y postgresql postgresql-contrib
systemctl start postgresql
systemctl enable postgresql

# 6. Installation Redis
apt install -y redis-server
systemctl start redis
systemctl enable redis

# 7. Installation TimescaleDB
echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -
apt update
apt install -y timescaledb-2-postgresql-14

# 8. Configuration PostgreSQL pour TimescaleDB
sudo -u postgres psql -c "CREATE DATABASE trading_platform;"
sudo -u postgres psql -d trading_platform -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# 9. Installation Nginx (reverse proxy)
apt install -y nginx
systemctl start nginx
systemctl enable nginx

# 10. Installation Certbot (SSL gratuit)
apt install -y certbot python3-certbot-nginx

# 11. Configuration firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# 12. Création utilisateur application
adduser --system --group --home /opt/trading_platform trading

# 13. Configuration répertoires
mkdir -p /opt/trading_platform/{backend,frontend,data,logs}
chown -R trading:trading /opt/trading_platform

echo "✅ VPS setup completed!"
```

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://trading_user:${DB_PASSWORD}@postgres:5432/trading_platform
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./backend/logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - trading_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend PWA
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=https://api.yourdomain.com
    restart: unless-stopped
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
    networks:
      - trading_network

  # Base de données PostgreSQL + TimescaleDB
  postgres:
    image: timescale/timescaledb:latest-pg14
    restart: unless-stopped
    environment:
      - POSTGRES_DB=trading_platform
      - POSTGRES_USER=trading_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - trading_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user -d trading_platform"]
      interval: 30s
      timeout: 5s
      retries: 5

  # Cache Redis
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - trading_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 5s
      retries: 5

  # Reverse proxy Nginx
  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - /var/log/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - trading_network

  # Worker Celery (background tasks)
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A src.infrastructure.background.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://trading_user:${DB_PASSWORD}@postgres:5432/trading_platform
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend/logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - trading_network

  # Scheduler Celery Beat
  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A src.infrastructure.background.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://trading_user:${DB_PASSWORD}@postgres:5432/trading_platform
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend/logs:/app/logs
    depends_on:
      - postgres
      - redis
    networks:
      - trading_network

volumes:
  postgres_data:
  redis_data:

networks:
  trading_network:
    driver: bridge
```

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=1r/s;

    server {
        listen 80;
        server_name yourdomain.com api.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # Frontend PWA
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        root /usr/share/nginx/html;
        index index.html;
        
        # PWA configuration
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
            
            # Service Worker pas de cache
            location = /sw.js {
                expires off;
                add_header Cache-Control "no-cache, no-store, must-revalidate";
            }
        }
    }

    # Backend API
    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Health check
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

Cette architecture complète vous fournit :

1. **Clean Architecture** avec séparation stricte des responsabilités
2. **Patterns robustes** : Repository, Strategy, Observer, CQRS
3. **Optimisation yfinance** maximale avec cache et batch requests  
4. **PWA moderne** avec React, TypeScript et Tailwind CSS
5. **Backend scalable** FastAPI + PostgreSQL + TimescaleDB + Redis
6. **Déploiement VPS** avec Docker, Nginx, SSL gratuit
7. **Monitoring** et observabilité intégrée
8. **Solutions 100% gratuites** (hors VPS)

Voulez-vous que je développe une partie spécifique ou que j'ajoute des fonctionnalités particulières ?
