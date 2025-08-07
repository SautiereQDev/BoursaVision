# README - Boursa Vision

🚀 **Plateforme de Trading et Gestion de Portefeuille**

Boursa Vision est une plateforme moderne de trading et de gestion de portefeuille développée avec FastAPI et React, utilisant les principes de Clean Architecture et Domain-Driven Design.

## 🌟 Fonctionnalités

### 🔒 Authentification et Sécurité
- Authentification JWT sécurisée
- Gestion des rôles et permissions
- Authentification à deux facteurs (2FA)
- Chiffrement des données sensibles

### 📊 Gestion de Portefeuille
- Création et gestion de portefeuilles multiples
- Suivi en temps réel des performances
- Calcul automatique des rendements
- Historique détaillé des transactions

### 📈 Analyse et Reporting
- Tableaux de bord interactifs
- Graphiques de performance
- Rapports personnalisables
- Alertes et notifications

### 🔄 Trading
- Interface de trading intuitive
- Ordres automatisés
- Suivi des positions
- Gestion des risques

### 📱 PWA (Progressive Web App)
- Application installable
- Fonctionnement hors ligne
- Notifications push
- Interface responsive

## 🏗️ Architecture

### Stack Technologique

**Backend**:
- **FastAPI** - Framework web moderne et performant
- **PostgreSQL** - Base de données principale
- **TimescaleDB** - Extension pour données temporelles
- **Redis** - Cache et sessions
- **Celery** - Tâches asynchrones
- **Alembic** - Migrations de base de données

**Frontend**:
- **React 18** - Framework frontend
- **TypeScript** - Typage statique
- **TanStack Router** - Routing moderne
- **TanStack Query** - Gestion des données
- **Tailwind CSS** - Framework CSS
- **Vite** - Build tool rapide

**Infrastructure**:
- **Docker** - Conteneurisation
- **Nginx** - Proxy inverse et load balancer
- **Let's Encrypt** - Certificats SSL automatiques
- **GitHub Actions** - CI/CD

### Principes Architecturaux

```text
┌─────────────────────────────────────────────────────────┐
│                    CLEAN ARCHITECTURE                   │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Interfaces │  │ Application │  │   Domain    │     │
│  │             │  │             │  │  (Entities) │     │
│  │ Controllers │  │ Use Cases   │  │             │     │
│  │  Routers    │  │  Services   │  │ Value       │     │
│  │   DTOs      │  │             │  │ Objects     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│          │                │                │           │
│          └────────────────┼────────────────┘           │
│                           │                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │Infrastructure│ │  External   │  │   Tests     │     │
│  │             │  │  Services   │  │             │     │
│  │ Repository  │  │   APIs      │  │   Unit      │     │
│  │ Database    │  │  Message    │  │ Integration │     │
│  │   ORM       │  │   Queue     │  │    E2E      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Démarrage Rapide

### Prérequis

- **Docker** et **Docker Compose**
- **Git**
- **Node.js 18+** (pour le développement frontend)
- **Python 3.11+** (pour le développement backend)

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-repo/boursa-vision.git
cd boursa-vision

# 2. Configuration de l'environnement
cp .env.template .env
# Éditer .env avec vos paramètres

# 3. Démarrage avec Docker (Développement)
cd docker
docker-compose -f docker-compose.dev.yml up -d

# 4. Accéder à l'application
# Frontend: http://localhost:5173
# API: http://localhost:8000
# Docs API: http://localhost:8000/docs
```

### Installation pour le Développement

```bash
# Backend
cd backend
pip install poetry
poetry install
poetry shell

# Frontend
cd frontend
npm install

# Base de données
cd docker
docker-compose -f docker-compose.dev.yml up -d postgres redis
cd ../backend
poetry run alembic upgrade head
```

## 📖 Documentation

- **[Guide de Développement](docs/development.md)** - Configuration et standards de développement
- **[Guide de Déploiement](docs/deployment.md)** - Instructions de déploiement production
- **[Architecture](docs/architecture.md)** - Architecture détaillée du système
- **[API Documentation](http://localhost:8000/docs)** - Documentation interactive de l'API

## 🧪 Tests

```bash
# Backend
cd backend
poetry run pytest tests/ --cov=src

# Frontend
cd frontend
npm run test
npm run test:e2e

# Tests d'intégration complets
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🏗️ Structure du Projet

```text
boursa-vision/
├── 📁 backend/                 # API FastAPI
│   ├── src/
│   │   ├── domain/            # Logique métier
│   │   ├── application/       # Cas d'usage
│   │   ├── infrastructure/    # Implémentations
│   │   └── interfaces/        # API et adaptateurs
│   ├── tests/                # Tests automatisés
│   └── pyproject.toml        # Configuration Python
├── 📁 frontend/               # Application React
│   ├── src/
│   │   ├── components/       # Composants React
│   │   ├── routes/           # Pages et navigation
│   │   ├── hooks/            # Hooks personnalisés
│   │   └── integrations/     # Services tiers
│   └── package.json          # Configuration Node.js
├── 📁 docker/                # Configuration Docker
│   ├── docker-compose.dev.yml    # Développement
│   ├── docker-compose.prod.yml   # Production
│   ├── Dockerfile.backend         # Image backend
│   └── Dockerfile.frontend        # Image frontend
├── 📁 nginx/                 # Configuration Nginx
├── 📁 scripts/               # Scripts de déploiement
└── 📁 docs/                  # Documentation
```

## 🚀 Déploiement

### Développement

```bash
# Démarrage rapide avec Docker
docker-compose -f docker/docker-compose.dev.yml up -d

# Ou démarrage manuel des services
cd backend && poetry run uvicorn src.infrastructure.web.main:app --reload
cd frontend && npm run dev
```

### Production

```bash
# Installation automatique sur VPS
curl -fsSL https://raw.githubusercontent.com/votre-repo/boursa-vision/main/scripts/setup_vps.sh | bash

# Ou déploiement manuel
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

Voir le [Guide de Déploiement](docs/deployment.md) pour les instructions détaillées.

## 🔧 Configuration

### Variables d'Environnement

```bash
# Base de données
POSTGRES_USER=boursa_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=boursa_vision

# API
SECRET_KEY=your_secret_key_32_chars_minimum
JWT_SECRET_KEY=your_jwt_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
ALPHA_VANTAGE_API_KEY=your_api_key
IEX_CLOUD_API_KEY=your_api_key

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

Copiez `.env.template` vers `.env` et ajustez les valeurs selon votre environnement.

## 🤝 Contribution

Nous accueillons les contributions ! Voici comment contribuer :

1. **Fork** le project
2. Créez une **branche feature** (`git checkout -b feature/nouvelle-fonctionnalite`)
3. **Committez** vos changements (`git commit -m 'Ajout d'une nouvelle fonctionnalité'`)
4. **Push** vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une **Pull Request**

### Standards de Code

- **Backend**: Suivre PEP 8, type hints obligatoires, tests unitaires
- **Frontend**: ESLint + Prettier, TypeScript strict, composants testés
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Documentation**: Mise à jour obligatoire pour les nouvelles fonctionnalités

## 📊 Monitoring et Performance

### Métriques Disponibles

- **Performance API**: Temps de réponse, throughput
- **Base de Données**: Requêtes lentes, connexions actives
- **Frontend**: Core Web Vitals, erreurs JavaScript
- **Infrastructure**: CPU, mémoire, stockage

### Logs

```bash
# Logs en temps réel
docker-compose -f docker/docker-compose.prod.yml logs -f

# Logs spécifiques
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

## 🔒 Sécurité

- **Authentification**: JWT avec refresh tokens
- **Autorisation**: RBAC (Role-Based Access Control)
- **Chiffrement**: HTTPS/TLS en production
- **Validation**: Sanitization et validation stricte des inputs
- **Audit**: Logging complet des actions utilisateurs
- **Rate Limiting**: Protection contre les abus
- **CORS**: Configuration restrictive

## 🆘 Dépannage

### Problèmes Courants

**Erreur de connexion à la base de données**:
```bash
# Vérifier que PostgreSQL est démarré
docker-compose ps postgres

# Vérifier les logs
docker-compose logs postgres
```

**Erreur de build frontend**:
```bash
# Nettoyer le cache
rm -rf node_modules package-lock.json
npm install

# Vérifier la version Node.js
node --version  # Doit être 18+
```

**Problème de permissions Docker**:
```bash
# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker
```

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/votre-repo/boursa-vision/issues)
- **Discussions**: [GitHub Discussions](https://github.com/votre-repo/boursa-vision/discussions)
- **Email**: <support@votre-domaine.com>

## 🎯 Roadmap

### Version 1.0 (Q1 2024)
- [x] Architecture de base
- [x] Authentification et autorisation
- [x] Gestion de portefeuilles
- [ ] Interface de trading basique
- [ ] Rapports de performance

### Version 1.1 (Q2 2024)
- [ ] Trading automatisé
- [ ] Notifications push
- [ ] API mobile
- [ ] Intégrations brokers

### Version 2.0 (Q3 2024)
- [ ] Machine Learning pour prédictions
- [ ] Social trading
- [ ] API publique
- [ ] Marketplace de stratégies

---

**Développé avec ❤️ par l'équipe Boursa Vision**
