# Déploiement Boursa Vision

Guide complet pour déployer la plateforme de trading Boursa Vision en production.

## Architecture de Déploiement

```
┌─────────────────────────────────────────────────────────┐
│                    PRODUCTION STACK                     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Nginx     │  │   Backend   │  │  Frontend   │     │
│  │   (Proxy)   │  │  (FastAPI)  │  │  (React)    │     │
│  │   Port 80   │  │   Port 8000 │  │   Static    │     │
│  │   Port 443  │  │             │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│          │                │                │           │
│          └────────────────┼────────────────┘           │
│                           │                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ PostgreSQL  │  │    Redis    │  │   Celery    │     │
│  │ TimescaleDB │  │   (Cache)   │  │  (Workers)  │     │
│  │   Port 5432 │  │   Port 6379 │  │             │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Prérequis

### Serveur VPS
- **OS**: Ubuntu 20.04+ LTS
- **RAM**: Minimum 2GB (recommandé 4GB+)
- **Stockage**: Minimum 20GB SSD (recommandé 50GB+)
- **CPU**: 2 cores minimum
- **Réseau**: IPv4 publique

### Domaine
- Nom de domaine configuré (ex: votre-domaine.com)
- Accès aux DNS pour configuration

## Installation Automatique

### 1. Setup VPS Initial

```bash
# Connectez-vous à votre VPS
ssh root@votre-serveur-ip

# Téléchargez et exécutez le script de setup
curl -fsSL https://raw.githubusercontent.com/votre-repo/boursa-vision/main/scripts/setup_vps.sh | bash

# Ou clonez le repo et exécutez
git clone https://github.com/votre-repo/boursa-vision.git
cd boursa-vision
chmod +x scripts/setup_vps.sh
sudo ./scripts/setup_vps.sh
```

### 2. Configuration de l'Environnement

```bash
# Allez dans le répertoire du projet
cd /opt/boursa-vision

# Copiez et configurez l'environnement
cp .env.template .env

# Éditez la configuration
nano .env
```

**Configuration minimale requise** dans `.env`:

```bash
# Base de données
POSTGRES_USER=boursa_user
POSTGRES_PASSWORD=votre_mot_de_passe_securise
POSTGRES_DB=boursa_vision

# API
SECRET_KEY=votre_cle_secrete_32_caracteres_minimum
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
CORS_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com

# Frontend
VITE_API_BASE_URL=https://votre-domaine.com/api/v1
VITE_WS_URL=wss://votre-domaine.com/ws
```

### 3. Configuration SSL

```bash
# Générez un certificat SSL gratuit avec Let's Encrypt
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Le certificat sera automatiquement configuré dans Nginx
```

### 4. Déploiement

```bash
# Déployez l'application
cd /opt/boursa-vision
chmod +x scripts/deploy.sh
./scripts/deploy.sh --production --backup
```

## Installation Manuelle

### 1. Préparation du Serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx ufw fail2ban git

# Configuration du firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw --force enable

# Démarrage des services
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### 2. Clonage du Projet

```bash
# Création du répertoire
sudo mkdir -p /opt/boursa-vision
sudo chown $USER:$USER /opt/boursa-vision

# Clone du repository
git clone https://github.com/votre-repo/boursa-vision.git /opt/boursa-vision
cd /opt/boursa-vision
```

### 3. Configuration Docker

```bash
# Construction des images
cd docker
docker-compose -f docker-compose.prod.yml build

# Lancement des services
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Configuration Nginx

```bash
# Copiez la configuration Nginx
sudo cp nginx/nginx.prod.conf /etc/nginx/sites-available/boursa-vision
sudo ln -s /etc/nginx/sites-available/boursa-vision /etc/nginx/sites-enabled/

# Supprimez la configuration par défaut
sudo rm /etc/nginx/sites-enabled/default

# Testez la configuration
sudo nginx -t

# Redémarrez Nginx
sudo systemctl restart nginx
```

## Vérification du Déploiement

### 1. Health Checks

```bash
# Vérifiez que tous les containers sont en cours d'exécution
docker ps

# Vérifiez les logs
docker-compose -f docker/docker-compose.prod.yml logs

# Testez les endpoints
curl http://localhost:8000/health
curl http://localhost:80
```

### 2. Tests Fonctionnels

```bash
# API Health
curl https://votre-domaine.com/api/v1/health

# Frontend
curl https://votre-domaine.com

# WebSocket (nécessite wscat: npm install -g wscat)
wscat -c wss://votre-domaine.com/ws
```

## Maintenance et Monitoring

### 1. Logs

```bash
# Logs en temps réel
docker-compose -f docker/docker-compose.prod.yml logs -f

# Logs spécifiques
docker-compose -f docker/docker-compose.prod.yml logs backend
docker-compose -f docker/docker-compose.prod.yml logs frontend
docker-compose -f docker/docker-compose.prod.yml logs postgres
```

### 2. Sauvegarde

```bash
# Sauvegarde manuelle
./scripts/backup.sh

# Configuration de sauvegardes automatiques (déjà configuré par setup_vps.sh)
crontab -l
```

### 3. Mise à jour

```bash
# Mise à jour avec sauvegarde
./scripts/deploy.sh --production --backup

# Rollback en cas de problème
./scripts/deploy.sh --rollback
```

### 4. Surveillance des ressources

```bash
# Utilisation Docker
docker stats

# Utilisation système
htop
df -h
free -h

# Logs de monitoring (configuré automatiquement)
tail -f /var/log/boursa-monitor.log
```

## Dépannage

### 1. Problèmes Courants

**Container ne démarre pas**:
```bash
docker-compose -f docker/docker-compose.prod.yml logs [service-name]
docker inspect [container-id]
```

**Problème de base de données**:
```bash
# Vérifiez la connectivité
docker exec boursa-postgres-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# Vérifiez les migrations
docker-compose -f docker/docker-compose.prod.yml exec backend poetry run alembic current
```

**Problème SSL**:
```bash
# Renouvelez le certificat
sudo certbot renew
sudo systemctl reload nginx
```

### 2. Performance

**Optimisation mémoire**:
```bash
# Limitez la mémoire Redis
echo 'maxmemory 512mb' | docker exec -i boursa-redis-prod redis-cli

# Surveillez l'utilisation
docker stats --no-stream
```

**Optimisation base de données**:
```bash
# Analysez les performances
docker exec boursa-postgres-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM pg_stat_activity;"
```

## Sécurité

### 1. Checklist Sécurité

- [ ] Certificats SSL configurés et renouvelés automatiquement
- [ ] Firewall configuré (UFW)
- [ ] Fail2ban actif
- [ ] Mots de passe forts dans .env
- [ ] Sauvegardes automatiques
- [ ] Monitoring actif
- [ ] Logs configurés

### 2. Durcissement

```bash
# Désactivez l'accès SSH par mot de passe
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no

# Configurez des clés SSH
ssh-keygen -t rsa -b 4096
ssh-copy-id user@votre-serveur
```

## Support et Déploiement Avancé

### 1. Scaling Horizontal

```bash
# Augmentez le nombre de workers Celery
docker-compose -f docker/docker-compose.prod.yml up -d --scale celery-worker=3

# Load balancing avec plusieurs backends
# Modifiez nginx/nginx.prod.conf pour ajouter plusieurs upstream
```

### 2. Monitoring Avancé

```bash
# Installation de Prometheus + Grafana (optionnel)
# Voir docker/monitoring/docker-compose.monitoring.yml
```

### 3. CI/CD

```bash
# GitHub Actions workflow
# Voir .github/workflows/deploy.yml
```

---

## Contacts et Support

- **Documentation**: [docs/](../docs/)
- **Issues**: GitHub Issues
- **Email**: support@votre-domaine.com

**Note**: Remplacez `votre-domaine.com` et `votre-repo` par vos valeurs réelles.
