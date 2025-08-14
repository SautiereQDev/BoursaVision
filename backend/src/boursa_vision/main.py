#!/usr/bin/env python3
"""
🚀 Point d'entrée unifié pour Boursa Vision FastAPI - Architecture Clean

✨ ARCHITECTURE CLEAN ✨
• Clean Architecture avec séparation des couches
• Domain-Driven Design (DDD)
• Configuration unifiée pour tous les environnements
• API versionnée et modulaire

🐳 Docker:    Mode production, stable, port 8000
💻 Local:     Mode développement, hot-reload, port 8001

🌟 Usage:
  make api        # Docker
  make api-local  # Local
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path for proper imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core imports
from pathlib import Path

import uvicorn


def setup_paths():
    """Configure les chemins Python pour les imports"""
    current_dir = Path(__file__).parent.absolute()
    src_dir = current_dir / "src"

    # Ajouter src au PYTHONPATH
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    # Ajouter le répertoire backend aussi
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))


def detect_environment() -> dict:
    """Détecte l'environnement d'exécution et retourne la configuration appropriée"""

    # Détection Docker
    is_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"

    # Configuration de base
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("API_PORT", "8000")),
        "reload": True,
    }

    if is_docker:
        print("🐳 Détection environnement Docker")
        # En mode développement Docker, on active le reload si demandé
        config["reload"] = os.getenv("API_RELOAD", "false").lower() == "true"
    else:
        print("💻 Détection environnement local")
        config["reload"] = True  # Pratique pour le développement local

    print(f"📡 Serveur configuré sur {config['host']}:{config['port']}")
    print(f"🔄 Rechargement automatique: {config['reload']}")

    return config


def create_app():
    """Crée et configure l'application FastAPI"""
    try:
        # Configuration des chemins
        setup_paths()

        # Import de l'application
        from fastapi_yfinance import app

        print("✅ Application FastAPI chargée avec succès")
        return app

    except ImportError as e:
        print(f"❌ Erreur d'import FastAPI: {e}")
        print("💡 Vérifiez que le fichier src/fastapi_yfinance.py existe")
        sys.exit(1)


def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage Boursa Vision FastAPI")

    try:
        # Configuration automatique
        config = detect_environment()

        # Démarrage du serveur
        print("🌟 Lancement du serveur FastAPI...")
        print(
            f"📖 Documentation disponible sur: http://{config['host']}:{config['port']}/docs"
        )

        if config["reload"]:
            # Mode reload nécessite une chaîne d'import
            print("🔄 Mode développement avec rechargement automatique")

            # Détecter si on est dans Docker pour ajuster le chemin de reload
            is_docker = (
                os.path.exists("/.dockerenv") or os.getenv("DOCKER_ENV") == "true"
            )

            if is_docker:
                # Dans Docker, on surveille /app/src
                uvicorn.run(
                    "src.fastapi_yfinance:app",
                    host=config["host"],
                    port=config["port"],
                    reload=True,
                    reload_dirs=["/app/src"],
                    log_level="debug",
                )
            else:
                # Localement, on surveille src/
                uvicorn.run(
                    "src.fastapi_yfinance:app",
                    host=config["host"],
                    port=config["port"],
                    reload=True,
                    reload_dirs=["src/"],
                    log_level="debug",
                )
        else:
            # Mode production avec l'objet app directement
            print("🏭 Mode production sans rechargement")
            app = create_app()
            uvicorn.run(app, host=config["host"], port=config["port"], reload=False)

    except Exception as e:
        print(f"❌ Erreur de démarrage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
