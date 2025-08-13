#!/bin/bash

# Script de lancement pour Boursa Vision Advanced API
# Utilise l'environnement virtuel Poetry

cd /home/quentin-sautiere/Documents/workspace/python/boursa-vision/backend

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║   🎯 BOURSA VISION ADVANCED - API Intelligence Financière   ║"
echo "║                                                              ║"
echo "║   🚀 Démarrage avec Poetry...                                ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Vérification de l'environnement
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erreur: pyproject.toml non trouvé dans $(pwd)"
    exit 1
fi

echo "📁 Répertoire de travail: $(pwd)"
echo "🐍 Lancement de l'API avec Poetry..."

# Lancement avec Poetry
poetry run python api.py
