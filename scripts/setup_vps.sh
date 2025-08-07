#!/bin/bash

# Boursa Vision - VPS Setup Script
# This script sets up a Ubuntu VPS for the trading platform

set -e

echo "🚀 Starting Boursa Vision VPS Setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    ufw \
    fail2ban \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
echo "📝 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/boursa-vision
sudo chown $USER:$USER /opt/boursa-vision

# Create environment file template
echo "⚙️ Creating environment template..."
cat > /opt/boursa-vision/.env.template << 'EOF'
# PostgreSQL Database
POSTGRES_USER=boursa_user
POSTGRES_PASSWORD=change_this_secure_password
POSTGRES_DB=boursa_vision

# Redis (optional password)
REDIS_PASSWORD=

# Backend API
SECRET_KEY=change_this_to_a_secure_random_string_at_least_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
VITE_API_BASE_URL=https://yourdomain.com/api/v1
VITE_WS_URL=wss://yourdomain.com/ws

# Email (optional for notifications)
SMTP_SERVER=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@yourdomain.com

# Monitoring (optional)
GRAFANA_PASSWORD=admin
EOF
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# 12. Création utilisateur application
adduser --system --group --home /opt/trading_platform trading

# 13. Configuration répertoires
mkdir -p /opt/trading_platform/{backend,frontend,data,logs}
chown -R trading:trading /opt/trading_platform

echo "✅ VPS setup completed!"