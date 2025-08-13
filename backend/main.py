#!/usr/bin/env python3
"""
Boursa Vision Advanced API - Point d'entrée principal
API d'intelligence financière avec analyse massive de marché
"""

import logging
import os
import sys
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal de l'API"""

    print(
        """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎯 BOURSA VISION ADVANCED - API Intelligence Financière   ║
║                                                              ║
║   🚀 Analyse massive de marché avec IA                      ║
║   📊 Recommandations d'investissement automatisées          ║
║   💼 Optimisation de portefeuille intelligente              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    )

    try:
        # Import de l'application FastAPI
        import uvicorn

        from api import app

        # Configuration
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(
            os.getenv("API_PORT", "8006")
        )  # Port 8006 par défaut pour éviter les conflits
        reload = os.getenv("API_RELOAD", "true").lower() == "true"
        workers = int(os.getenv("API_WORKERS", "1"))

        logger.info(f"🌐 Démarrage sur {host}:{port}")
        logger.info(f"🔄 Reload: {reload}")
        logger.info(f"👥 Workers: {workers}")
        logger.info(f"📚 Documentation: http://{host}:{port}/docs")

        # Lancement de l'API
        if reload:
            # Mode reload : utiliser import string
            uvicorn.run(
                "api:app", host=host, port=port, reload=reload, log_level="info"
            )
        else:
            # Mode production : utiliser l'objet app directement
            uvicorn.run(app, host=host, port=port, workers=workers, log_level="info")

    except ImportError as e:
        logger.error(f"❌ Erreur d'import: {e}")
        logger.error("💡 Assurez-vous que toutes les dépendances sont installées")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
