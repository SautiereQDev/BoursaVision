"""
Infrastructure de tâches en arrière-plan avec Celery.
Fournit l'archivage continu des données de marché.
"""

from .celery_app import celery_app
from .market_data_archiver import MarketDataArchiver
from .tasks import archive_market_data_task, health_check_task

__all__ = [
    "MarketDataArchiver",
    "archive_market_data_task",
    "celery_app",
    "health_check_task",
]
