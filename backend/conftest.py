"""Configuration globale pour pytest."""

import os

# Force l'utilisation du mock Celery pour tous les tests
os.environ["USE_MOCK_CELERY"] = "true"
