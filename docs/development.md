
# Guide de Développement Boursa Vision

Guide pour les développeurs travaillant sur la plateforme de trading Boursa Vision.

Pour une vue d'ensemble de l'architecture, voir : [Architecture Complète](architecture.md)

Pour la définition des termes techniques, voir : [Glossaire](glossaire.md)

## Architecture du Projet

### Structure des Dossiers

```txt
boursa-vision/
├── backend/                 # API FastAPI avec Clean Architecture
│   ├── src/
│   │   ├── domain/         # Entités métier et logique business
│   │   ├── application/    # Cas d'usage et services applicatifs
│   │   ├── infrastructure/ # Implémentations concrètes
│   │   └── interfaces/     # Adaptateurs et contrôleurs
│   ├── tests/             # Tests automatisés
│   └── pyproject.toml     # Configuration Python/Poetry
├── frontend/              # Application React PWA
│   ├── src/
│   │   ├── components/    # Composants React réutilisables
│   │   ├── routes/        # Pages et navigation
│   │   ├── hooks/         # Hooks personnalisés
│   │   └── integrations/  # Services tiers
│   └── package.json       # Configuration Node.js
├── docker/                # Configuration conteneurs
├── nginx/                 # Configuration proxy
├── scripts/               # Scripts de déploiement
└── docs/                  # Documentation
```

### Principes Architecturaux

1. **Clean Architecture**: Séparation claire des responsabilités
2. **Domain-Driven Design**: Modélisation métier centrée
3. **CQRS**: Séparation commandes/queries
4. **Event Sourcing**: Traçabilité des événements
5. **Microservices Ready**: Architecture évolutive

## Configuration de l'Environnement de Développement

### 1. Prérequis

```bash
# Node.js (version 18+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python (version 3.11+)
sudo apt install python3.11 python3.11-venv

# Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Docker & Docker Compose
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
```

### 2. Clone et Installation

```bash
# Clone du repository
git clone https://github.com/votre-repo/boursa-vision.git
cd boursa-vision

# Configuration de l'environnement
cp .env.template .env
# Éditez .env avec vos valeurs locales

# Backend
cd backend
poetry install
poetry shell

# Frontend
cd ../frontend
npm install
```

### 3. Base de Données de Développement

```bash
# Démarrage des services de développement
cd docker
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Attendre que PostgreSQL soit prêt
sleep 10

# Migrations
cd ../backend
poetry run alembic upgrade head

# (Optionnel) Données de test
poetry run python -c "from src.infrastructure.database.seed import seed_dev_data; seed_dev_data()"
```

## Workflow de Développement

### 1. Démarrage des Services

```bash
# Terminal 1 - Services de base
cd docker
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Terminal 2 - Backend
cd backend
poetry run uvicorn src.infrastructure.web.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 - Frontend
cd frontend
npm run dev

# Terminal 4 - Celery (si nécessaire)
cd backend
poetry run celery -A src.infrastructure.tasks.celery_app worker -l info
```

### 2. URLs de Développement

- **Frontend**: <http://localhost:5173>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **Adminer**: <http://localhost:8080>

### 3. Tests

```bash
# Backend - Tests unitaires
cd backend
poetry run pytest tests/unit/

# Backend - Tests d'intégration
poetry run pytest tests/integration/

# Backend - Coverage
poetry run pytest --cov=src tests/

# Frontend - Tests
cd frontend
npm run test

# Frontend - Tests E2E
npm run test:e2e
```

## Standards de Code

### 1. Backend (Python)

```python
# Exemple de structure d'une entité
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass(frozen=True)
class Portfolio:
    """Entité Portfolio représentant un portefeuille d'investissement."""
    
    id: str
    user_id: str
    name: str
    total_value: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    def calculate_return(self, initial_value: Decimal) -> Decimal:
        """Calcule le rendement du portefeuille."""
        if initial_value <= 0:
            raise ValueError("La valeur initiale doit être positive")
        
        return ((self.total_value - initial_value) / initial_value) * 100
```

**Standards**:

- Type hints obligatoires
- Docstrings pour toutes les classes/méthodes publiques
- Dataclasses immutables pour les entités
- Validation des entrées
- Tests unitaires avec 80%+ de couverture

### 2. Frontend (TypeScript/React)

```typescript
// Exemple de composant
import React from 'react'
import { useQuery } from '@tanstack/react-query'
import type { Portfolio } from '../types/portfolio'

interface PortfolioCardProps {
  portfolioId: string
  onEdit?: (portfolio: Portfolio) => void
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({
  portfolioId,
  onEdit
}) => {
  const { data: portfolio, isLoading, error } = useQuery({
    queryKey: ['portfolio', portfolioId],
    queryFn: () => fetchPortfolio(portfolioId)
  })

  if (isLoading) return <div>Chargement...</div>
  if (error) return <div>Erreur: {error.message}</div>
  if (!portfolio) return null

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold">{portfolio.name}</h3>
      <p className="text-2xl font-bold text-green-600">
        {portfolio.totalValue.toLocaleString('fr-FR', {
          style: 'currency',
          currency: 'EUR'
        })}
      </p>
      {onEdit && (
        <button
          onClick={() => onEdit(portfolio)}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Modifier
        </button>
      )}
    </div>
  )
}
```

**Standards**:

- TypeScript strict mode
- Props interfaces définies
- Hooks pour la gestion d'état
- Tailwind CSS pour le styling
- Composants réutilisables
- Tests avec Testing Library

### 3. Conventions de Nommage

```bash
# Fichiers
kebab-case.ts         # Frontend
snake_case.py         # Backend

# Variables/Fonctions
camelCase             # Frontend
snake_case            # Backend

# Classes
PascalCase            # Frontend & Backend

# Constants
UPPER_SNAKE_CASE      # Frontend & Backend

# Branches Git
feature/nom-feature
bugfix/nom-bug
hotfix/nom-hotfix
```

## Debugging

### 1. Backend Debugging

```python
# Ajout de logs
import logging

logger = logging.getLogger(__name__)

def create_portfolio(data: dict) -> Portfolio:
    logger.info(f"Création d'un portfolio: {data}")
    try:
        portfolio = Portfolio(**data)
        logger.debug(f"Portfolio créé: {portfolio.id}")
        return portfolio
    except Exception as e:
        logger.error(f"Erreur lors de la création: {e}")
        raise
```

```bash
# Debugging avec pdb
poetry run python -m pdb src/infrastructure/web/main.py

# Logs en développement
docker-compose -f docker-compose.dev.yml logs -f backend
```

### 2. Frontend Debugging

```typescript
// Console debugging
console.group('Portfolio Component')
console.log('Props:', { portfolioId, onEdit })
console.log('Portfolio data:', portfolio)
console.groupEnd()

// React DevTools
// Extension nécessaire pour Chrome/Firefox

// Network debugging
const fetchWithLogging = async (url: string) => {
  console.time(`API Call: ${url}`)
  try {
    const response = await fetch(url)
    console.log(`Response ${response.status}:`, response)
    return response
  } finally {
    console.timeEnd(`API Call: ${url}`)
  }
}
```

## Base de Données

### 1. Migrations

```bash
# Créer une nouvelle migration
cd backend
poetry run alembic revision --autogenerate -m "Description du changement"

# Appliquer les migrations
poetry run alembic upgrade head

# Revenir à une migration précédente
poetry run alembic downgrade -1

# Voir l'historique
poetry run alembic history
```

### 2. Modèles SQLAlchemy

```python
from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PortfolioModel(Base):
    __tablename__ = "portfolios"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    total_value = Column(Numeric(15, 2), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    def to_entity(self) -> Portfolio:
        """Convertit le modèle en entité domain."""
        return Portfolio(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            total_value=self.total_value,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
```

## API Documentation

### 1. Endpoints Standards

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])

@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> List[PortfolioResponse]:
    """
    Récupère la liste des portfolios de l'utilisateur.
    
    - **skip**: Nombre d'éléments à ignorer (pagination)
    - **limit**: Nombre maximum d'éléments à retourner
    """
    portfolios = await portfolio_service.get_user_portfolios(
        current_user.id, skip, limit
    )
    return [PortfolioResponse.from_entity(p) for p in portfolios]

@router.post("/", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    portfolio_data: CreatePortfolioRequest,
    current_user: User = Depends(get_current_user)
) -> PortfolioResponse:
    """Crée un nouveau portfolio."""
    portfolio = await portfolio_service.create_portfolio(
        current_user.id, portfolio_data.dict()
    )
    return PortfolioResponse.from_entity(portfolio)
```

### 2. Schémas Pydantic

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

class CreatePortfolioRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    initial_value: Decimal = Field(..., gt=0)

class PortfolioResponse(BaseModel):
    id: str
    name: str
    total_value: Decimal
    return_percentage: Decimal
    created_at: datetime
    
    @classmethod
    def from_entity(cls, portfolio: Portfolio) -> "PortfolioResponse":
        return cls(
            id=portfolio.id,
            name=portfolio.name,
            total_value=portfolio.total_value,
            return_percentage=portfolio.calculate_return(portfolio.initial_value),
            created_at=portfolio.created_at
        )
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
```

## Performance et Optimisation

### 1. Backend

```python
# Cache Redis
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

async def get_portfolio_cached(portfolio_id: str) -> Portfolio:
    # Vérifier le cache
    cached = redis_client.get(f"portfolio:{portfolio_id}")
    if cached:
        data = json.loads(cached)
        return Portfolio(**data)
    
    # Récupérer de la DB
    portfolio = await portfolio_repository.get_by_id(portfolio_id)
    
    # Mettre en cache
    redis_client.setex(
        f"portfolio:{portfolio_id}",
        300,  # 5 minutes
        json.dumps(portfolio.dict())
    )
    
    return portfolio

# Requêtes optimisées
async def get_portfolios_with_performance(user_id: str) -> List[Portfolio]:
    # Utiliser des requêtes bulk au lieu de N+1
    query = select(PortfolioModel).where(
        PortfolioModel.user_id == user_id
    ).options(
        selectinload(PortfolioModel.positions)
    )
    
    result = await session.execute(query)
    return [model.to_entity() for model in result.scalars().all()]
```

### 2. Frontend

```typescript
// Optimisation React Query
const usePortfolios = () => {
  return useQuery({
    queryKey: ['portfolios'],
    queryFn: fetchPortfolios,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false
  })
}

// Lazy loading
const LazyPortfolioChart = lazy(() => import('./PortfolioChart'))

// Memoization
const PortfolioList = memo(({ portfolios }: { portfolios: Portfolio[] }) => {
  const sortedPortfolios = useMemo(
    () => portfolios.sort((a, b) => b.totalValue - a.totalValue),
    [portfolios]
  )
  
  return (
    <div>
      {sortedPortfolios.map(portfolio => (
        <PortfolioCard key={portfolio.id} portfolio={portfolio} />
      ))}
    </div>
  )
})
```

## Déploiement et CI/CD

### 1. Tests Automatisés

```bash
# Pre-commit hooks
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml est déjà configuré
```

### 2. Workflow GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: |
        cd backend
        poetry install
    
    - name: Run tests
      run: |
        cd backend
        poetry run pytest --cov=src tests/
```

### 3. Environnements

- **Development**: Local avec Docker Compose
- **Staging**: Déploiement automatique sur merge vers `develop`
- **Production**: Déploiement manuel sur merge vers `main`

## Ressources Utiles

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)

### Outils de Développement

- **IDE**: VS Code avec extensions Python/TypeScript
- **API Testing**: Postman ou Thunder Client
- **Database**: Adminer ou pgAdmin
- **Monitoring**: Docker Desktop

### Support

- **Issues**: GitHub Issues pour les bugs
- **Discussions**: GitHub Discussions pour les questions
- **Documentation**: Ce dossier `docs/`
