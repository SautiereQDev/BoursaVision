"""
Configuration et initialisation de l'application Celery.

Ce module configure Celery pour les tâches d'arrière-plan du système Boursa Vision,
incluant l'archivage automatique des données de marché.
"""

import logging
import os

try:
    from celery import Celery
    from celery.schedules import crontab as celery_crontab

    CELERY_AVAILABLE = True
    crontab = celery_crontab
except ImportError:
    CELERY_AVAILABLE = False
    crontab = None

# Force mock mode during testing
USE_MOCK_CELERY = os.getenv("USE_MOCK_CELERY", "false").lower() == "true"


if not CELERY_AVAILABLE or USE_MOCK_CELERY:
    # Mock pour développement
    class MockSignal:
        def connect(self, func):
            return func

    class MockSignals:
        def __init__(self):
            self.task_failure = MockSignal()
            self.task_success = MockSignal()

    class MockCelery:
        def __init__(self, *args, **kwargs):
            self.signals = MockSignals()

        def task(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        @property
        def conf(self):
            return self

        def update(self, *args, **kwargs):
            pass

        def start(self):
            """Mock start method for compatibility"""
            pass

    Celery = MockCelery

    def crontab(**kwargs):
        """Mock crontab function for development"""
        return kwargs


logger = logging.getLogger(__name__)

# Configuration de base depuis les variables d'environnement
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://redis:6379/0")
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://redis:6379/0")
)

# Configuration Celery
celery_app = Celery(
    "boursa_vision",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.infrastructure.background.tasks",
    ],
)

# Configuration optimisée pour la performance
celery_app.conf.update(
    # Sérialisation JSON pour la compatibilité
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Configuration des workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    # Gestion des résultats
    result_expires=3600,  # 1 heure
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
        "retry_policy": {"timeout": 5.0},
    },
    # Configuration des tâches
    task_routes={
        "src.infrastructure.background.tasks.archive_market_data_task": {
            "queue": "market_data"
        },
        "src.infrastructure.background.tasks.health_check_task": {"queue": "health"},
    },
    # Programmation des tâches
    beat_schedule={
        # Archive des données toutes les 5 minutes pendant les heures de marché
        "archive-market-data-frequent": {
            "task": "src.infrastructure.background.tasks.archive_market_data_task",
            "schedule": crontab(minute="*/5"),  # Toutes les 5 minutes
            "args": ("1m",),  # Intervalle 1 minute
            "options": {"queue": "market_data"},
        },
        # Archive des données horaires
        "archive-market-data-hourly": {
            "task": "src.infrastructure.background.tasks.archive_market_data_task",
            "schedule": crontab(minute=0),  # Toutes les heures
            "args": ("1h",),  # Intervalle 1 heure
            "options": {"queue": "market_data"},
        },
        # Archive des données quotidiennes
        "archive-market-data-daily": {
            "task": "src.infrastructure.background.tasks.archive_market_data_task",
            "schedule": crontab(
                hour=18, minute=0
            ),  # 18h00 UTC (après fermeture des marchés)
            "args": ("1d",),  # Intervalle 1 jour
            "options": {"queue": "market_data"},
        },
        # Archive des données hebdomadaires (le dimanche)
        "archive-market-data-weekly": {
            "task": "src.infrastructure.background.tasks.archive_market_data_task",
            "schedule": crontab(hour=20, minute=0, day_of_week=0),  # Dimanche 20h00
            "args": ("1w",),  # Intervalle 1 semaine
            "options": {"queue": "market_data"},
        },
        # Santé du système toutes les 30 minutes
        "health-check": {
            "task": "src.infrastructure.background.tasks.health_check_task",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "health"},
        },
    },
    # Surveillance et logs
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Gestion des erreurs
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
)


@celery_app.task(bind=True)
def debug_task(self):
    """Tâche de débogage pour tester Celery."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "debug_task_completed", "worker_id": self.request.id}


# Configuration du logger Celery
def setup_celery_logging():
    """Configure les logs pour Celery."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Configurer les logs spécifiques à Celery
    celery_logger = logging.getLogger("celery")
    celery_logger.setLevel(logging.INFO)

    # Logs pour les tâches
    task_logger = logging.getLogger("celery.task")
    task_logger.setLevel(logging.INFO)


# Initialisation des logs
setup_celery_logging()


# Event handlers pour le monitoring - ces tâches sont définies séparément
# pour éviter les conflits avec les gestionnaires de signaux


if CELERY_AVAILABLE and not USE_MOCK_CELERY:
    try:
        # Vérifier que l'objet signals est disponible sur l'instance Celery
        if hasattr(celery_app, "signals"):
            # Hooks pour le monitoring
            @celery_app.signals.task_failure.connect
            def task_failure_handler(
                sender=None, task_id=None, exception=None, einfo=None, **kwds
            ):
                """Handler pour les échecs de tâches."""
                logger.error(f"Task failure: {task_id} - {exception}")

            @celery_app.signals.task_success.connect
            def task_success_handler(sender=None, task_id=None, result=None, **kwds):
                """Handler pour les succès de tâches."""
                logger.info(f"Task success: {task_id}")

    except (AttributeError, ImportError) as e:
        logger.warning(f"Could not set up Celery signal handlers: {e}")
        logger.info("Running in mock mode - signal handlers disabled")


if __name__ == "__main__":
    celery_app.start()
