#!/bin/bash

# Guide de démarrage pour Boursa Vision API
# Utilise l'environnement Poetry

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║   🎯 BOURSA VISION - Guide de Démarrage                     ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "📁 Répertoire de travail: $(pwd)"
echo ""

echo "🚀 Options de démarrage disponibles:"
echo ""
echo "1. 📦 Démarrage avec Poetry (recommandé):"
echo "   cd backend && poetry run python api.py"
echo ""
echo "2. 🎛️  Démarrage via main.py:"
echo "   cd backend && poetry run python main.py"
echo ""
echo "3. 🧪 Utilisation du script de lancement:"
echo "   cd backend && ./launch_api.sh"
echo ""

echo "📚 Une fois démarré, l'API sera accessible sur:"
echo "   🌐 Interface: http://localhost:8005"
echo "   📖 Documentation: http://localhost:8005/docs"
echo "   ❤️  Santé: http://localhost:8005/health"
echo ""

echo "🧪 Tester les recommandations:"
echo "   ./test_recommendations.sh"
echo ""

echo "🛑 Pour arrêter l'API, utilisez Ctrl+C dans le terminal"
