
# Points clés de l'architecture

Pour une vue d'ensemble détaillée, voir : [Architecture Complète](architecture.md)

Pour les standards de développement, voir : [Guide de développement](development.md)

Pour la définition des termes techniques, voir : [Glossaire](glossaire.md)

## 🎯 **Base de données : PostgreSQL + TimescaleDB**

- **PostgreSQL** : Robuste, gratuit, parfait pour les transactions financières
- **TimescaleDB** : Extension gratuite, 20x plus rapide pour les time-series
- **Alternative légère** : SQLite avec optimisations WAL si VPS < 2GB RAM

## 🚀 **Optimisation yfinance maximale**

- **Rate limiting intelligent** : 2000 req/min avec fenêtre glissante
- **Cache Redis** : TTL adaptatif selon fréquence des données
- **Batch requests** : Récupération parallèle avec limite concurrence
- **Retry exponential backoff** : Résilience aux erreurs réseau
- **Session HTTP réutilisable** : Performance optimale

## 🏛️ **Dogmes architecturaux appliqués**

- **Clean Architecture** : Indépendance technologique totale
- **Domain-Driven Design** : Logique métier pure dans le domaine
- **CQRS** : Séparation lecture/écriture pour performance
- **Event Sourcing** : Traçabilité complète des opérations

## 🎨 **Design Patterns utilisés**

- **Repository Pattern** : Abstraction accès données
- **Strategy Pattern** : Indicateurs techniques modulaires  
- **Observer Pattern** : Notifications temps réel WebSocket
- **Unit of Work** : Gestion transactions complexes

## 🔧 **Stack 100% gratuit**

```text
Frontend : React PWA + TypeScript + Tailwind CSS
Backend  : FastAPI + Python + Pydantic
Database : PostgreSQL + TimescaleDB  
Cache    : Redis
Deploy   : Docker + Nginx + Let's Encrypt SSL
VPS      : Ubuntu + systemd services
```

## 📊 **Fonctionnalités implémentées**

- **Dashboard temps réel** avec métriques performance
- **Analyse technique** : 15+ indicateurs (RSI, MACD, Bollinger, etc.)
- **Signaux d'investissement** avec scoring composite
- **Gestion portfolio** : positions, P&L, rééquilibrage
- **Cache intelligent** : Données market en < 50ms
- **PWA native** : Notifications push, mode offline

## 🚀 **Performance attendue**

- **API** : < 100ms response time (p95)
- **yfinance** : 10-50 stocks/seconde selon VPS
- **Cache hit rate** : > 90% pour données récurrentes
- **Concurrent users** : 100-500 selon ressources VPS

L'architecture est **production-ready** avec monitoring, logs structurés, CI/CD Docker et déploiement automatisé.
