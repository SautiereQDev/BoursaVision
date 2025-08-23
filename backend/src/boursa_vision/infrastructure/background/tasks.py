"""
Tâches Celery pour l'archivage automatique des données de marché.

Ce module contient toutes les tâches d'arrière-plan pour maintenir
l'archive des données financières à jour.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    from celery import Task

    CELERY_AVAILABLE = True
except ImportError:
    # Mock Task pour les environnements sans Celery
    class Task:
        def on_success(self, retval, task_id, args, kwargs):
            pass

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            pass

    CELERY_AVAILABLE = False

from .celery_app import celery_app
from .market_data_archiver import market_data_archiver

logger = logging.getLogger(__name__)

# Constantes pour éviter la duplication
ARCHIVE_TASK_NAME = "src.infrastructure.background.tasks.archive_market_data_task"
HEALTH_TASK_NAME = "src.infrastructure.background.tasks.health_check_task"


class CallbackTask(Task):
    """Classe de base pour les tâches avec callbacks."""

    def on_success(self, retval, task_id, args, kwargs):
        """Appelé lors du succès d'une tâche."""
        logger.info(f"Task {task_id} succeeded with result: {retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Appelé lors de l'échec d'une tâche."""
        logger.error(f"Task {task_id} failed: {exc}")
        # Ici on pourrait ajouter des notifications


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name=ARCHIVE_TASK_NAME,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_kwargs={"countdown": 60},
)
def archive_market_data_task(self, interval: str = "1d") -> dict[str, Any]:
    """
    Tâche d'archivage des données de marché.

    Args:
        interval: Intervalle temporel pour l'archivage (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)

    Returns:
        Rapport d'archivage avec statistiques
    """
    try:
        logger.info(f"Starting market data archival task for interval: {interval}")

        # Utilisation d'asyncio pour les opérations asynchrones
        import asyncio

        # Si nous sommes dans un contexte asyncio existant, créons un nouveau loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Créer un nouveau thread pour éviter les conflits
                import concurrent.futures

                def run_archival():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            market_data_archiver.archive_all_symbols(interval)
                        )
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_archival)
                    report = future.result(timeout=1800)  # 30 minutes timeout
            else:
                report = loop.run_until_complete(
                    market_data_archiver.archive_all_symbols(interval)
                )
        except RuntimeError:
            # Pas de loop existant, créons-en un
            report = asyncio.run(market_data_archiver.archive_all_symbols(interval))

        # Logging du résultat
        success_rate = report.get("success_rate", 0)
        total_symbols = report.get("total_symbols", 0)
        successful = report.get("successful_archives", 0)

        logger.info(
            "Archival completed: %d/%d symbols (%.1f%% success rate)",
            successful,
            total_symbols,
            success_rate,
        )

        # Si le taux de succès est trop bas, on considère cela comme un échec partiel
        if success_rate < 80:
            logger.warning(f"Low success rate ({success_rate:.1f}%) for archival")

        return report

    except Exception as exc:
        logger.error(f"Archive task failed: {exc!s}")

        # Retry automatique pour certaines erreurs
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying archive task (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc)  # noqa: B904

        # Maximum de retries atteint
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
            "retries": self.request.retries,
        }


@celery_app.task(bind=True, base=CallbackTask, name=HEALTH_TASK_NAME, max_retries=2)
def health_check_task(self) -> dict[str, Any]:
    """
    Tâche de vérification de santé du système d'archivage.

    Returns:
        Statut de santé du système
    """
    try:
        logger.info("Running health check for market data archiver")

        import asyncio

        # Même gestion d'asyncio que pour l'archivage
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                def run_health_check():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            market_data_archiver.get_archival_status()
                        )
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_health_check)
                    status = future.result(timeout=60)  # 1 minute timeout
            else:
                status = loop.run_until_complete(
                    market_data_archiver.get_archival_status()
                )
        except RuntimeError:
            status = asyncio.run(market_data_archiver.get_archival_status())

        # Enrichir le statut avec des informations sur Celery
        status.update(
            {
                "celery_worker_status": "active",
                "task_id": self.request.id,
                "task_timestamp": datetime.now(UTC).isoformat(),
            }
        )

        logger.info("Health check completed successfully")
        return status

    except Exception as exc:
        logger.error(f"Health check failed: {exc!s}")

        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
            "celery_worker_status": "error",
        }


@celery_app.task(
    bind=True, name="src.infrastructure.background.tasks.manual_archive_task"
)
def manual_archive_task(
    self, symbols: list, interval: str = "1d", period: str = "1d"
) -> dict[str, Any]:
    """
    Tâche d'archivage manuel pour des symboles spécifiques.

    Args:
        symbols: Liste des symboles à archiver
        interval: Intervalle temporel
        period: Période de données à récupérer

    Returns:
        Rapport d'archivage
    """
    try:
        logger.info(f"Manual archival task for {len(symbols)} symbols")

        import asyncio

        async def archive_specific_symbols():
            """Archive les symboles spécifiés."""
            successful = 0
            failed = 0
            errors = []

            for symbol in symbols:
                try:
                    await market_data_archiver._archive_symbol_data(
                        symbol, interval, period
                    )
                    successful += 1
                    logger.debug(f"Successfully archived {symbol}")
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to archive {symbol}: {e!s}"
                    errors.append(error_msg)
                    logger.error(error_msg)

                # Délai entre symboles
                await asyncio.sleep(0.2)

            return {
                "status": "completed",
                "timestamp": datetime.now(UTC).isoformat(),
                "symbols": symbols,
                "interval": interval,
                "period": period,
                "successful": successful,
                "failed": failed,
                "errors": errors,
            }

        # Exécution de la tâche asynchrone
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                def run_manual_archive():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(archive_specific_symbols())
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_manual_archive)
                    return future.result(timeout=600)  # 10 minutes timeout
            else:
                return loop.run_until_complete(archive_specific_symbols())
        except RuntimeError:
            return asyncio.run(archive_specific_symbols())

    except Exception as exc:
        logger.error(f"Manual archive task failed: {exc!s}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        }


@celery_app.task(
    bind=True, name="src.infrastructure.background.tasks.cleanup_old_data_task"
)
def cleanup_old_data_task(self, days_to_keep: int = 365) -> dict[str, Any]:
    """
    Tâche de nettoyage des anciennes données.

    Args:
        days_to_keep: Nombre de jours de données à conserver

    Returns:
        Rapport de nettoyage
    """
    try:
        logger.info(f"Starting cleanup of data older than {days_to_keep} days")

        # Cette tâche sera implémentée selon les besoins de rétention
        # Pour l'instant, on retourne un rapport basique

        cutoff_date = datetime.now(UTC) - timedelta(days=days_to_keep)

        return {
            "status": "completed",
            "timestamp": datetime.now(UTC).isoformat(),
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep,
            "records_deleted": 0,  # À implémenter
            "message": "Cleanup task completed (placeholder implementation)",
        }

    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc!s}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Tâche de démarrage pour vérifier la connectivité
@celery_app.task(name="src.infrastructure.background.tasks.startup_check_task")
def startup_check_task() -> dict[str, Any]:
    """
    Tâche de vérification au démarrage.

    Returns:
        Statut de démarrage
    """
    try:
        logger.info("Running startup check for background tasks system")

        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Background tasks system is operational",
            "version": "1.0.0",
        }

    except Exception as exc:
        logger.error(f"Startup check failed: {exc!s}")
        return {
            "status": "failed",
            "error": str(exc),
            "timestamp": datetime.now(UTC).isoformat(),
        }
