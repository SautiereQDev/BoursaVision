"""
Tests unitaires pour les tâches Celery d'archivage.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur les signatures de tâches et la structure.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone


@pytest.mark.unit
class TestTasksModuleStructure:
    """Tests de structure et disponibilité du module tasks."""
    
    def test_tasks_module_file_exists(self):
        """Vérifie que le fichier tasks existe."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        assert tasks_path.exists()
        assert tasks_path.is_file()
    
    def test_tasks_module_has_docstring(self):
        """Vérifie que le module tasks a une docstring."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'Tâches Celery pour l\'archivage automatique' in content
        assert 'tâches d\'arrière-plan pour maintenir' in content


@pytest.mark.unit
class TestTasksImports:
    """Tests d'imports et gestion des dépendances."""
    
    def test_tasks_required_imports_exist(self):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = [
            'logging',
            'datetime',
            'typing'
        ]
        
        for import_name in required_imports:
            try:
                __import__(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")
    
    def test_tasks_has_celery_import_handling(self):
        """Vérifie la gestion des imports Celery avec fallback."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content
        assert 'from celery import Task' in content
        assert 'CELERY_AVAILABLE = True' in content
        assert 'except ImportError:' in content
        assert 'CELERY_AVAILABLE = False' in content
    
    def test_tasks_imports_archiver_components(self):
        """Vérifie que les composants d'archivage sont importés."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'from .celery_app import celery_app' in content
        assert 'from .market_data_archiver import market_data_archiver' in content


@pytest.mark.unit
class TestTaskConstants:
    """Tests des constantes de tâches."""
    
    def test_task_names_are_defined(self):
        """Vérifie que les noms de tâches sont définis comme constantes."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'ARCHIVE_TASK_NAME = ' in content
        assert 'HEALTH_TASK_NAME = ' in content
        assert 'archive_market_data_task' in content
        assert 'health_check_task' in content
    
    def test_task_names_follow_convention(self):
        """Vérifie que les noms de tâches suivent la convention."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'src.infrastructure.background.tasks' in content


@pytest.mark.unit
class TestCallbackTaskClass:
    """Tests de la classe CallbackTask."""
    
    def test_callback_task_class_defined(self):
        """Vérifie que la classe CallbackTask est définie."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'class CallbackTask(Task):' in content
        assert 'Classe de base pour les tâches avec callbacks.' in content
    
    def test_callback_task_has_required_methods(self):
        """Vérifie que CallbackTask a les méthodes de callback."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'def on_success(self, retval, task_id, args, kwargs):' in content
        assert 'def on_failure(self, exc, task_id, args, kwargs, einfo):' in content
    
    def test_callback_task_logs_events(self):
        """Vérifie que CallbackTask log les événements."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'logger.info(' in content
        assert 'logger.error(' in content
        assert 'succeeded with result' in content
        assert 'failed:' in content


@pytest.mark.unit
class TestArchiveMarketDataTask:
    """Tests de la tâche archive_market_data_task."""
    
    def test_archive_task_decorator_configuration(self):
        """Vérifie la configuration du décorateur de tâche d'archivage."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert '@celery_app.task(' in content
        assert 'bind=True' in content
        assert 'base=CallbackTask' in content
        assert 'max_retries=3' in content
        assert 'default_retry_delay=60' in content
        assert 'autoretry_for=(Exception,)' in content
    
    def test_archive_task_function_signature(self):
        """Vérifie la signature de la fonction archive_market_data_task."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'def archive_market_data_task(self, interval: str = "1d")' in content
        assert '-> Dict[str, Any]:' in content
    
    def test_archive_task_has_docstring(self):
        """Vérifie que la tâche d'archivage a une docstring."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'Tâche d\'archivage des données de marché.' in content
        assert 'Args:' in content
        assert 'Returns:' in content
        assert 'Rapport d\'archivage avec statistiques' in content
    
    def test_archive_task_handles_asyncio(self):
        """Vérifie que la tâche d'archivage gère asyncio."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'import asyncio' in content
        assert 'asyncio.get_event_loop()' in content
        assert 'new_loop = asyncio.new_event_loop()' in content
    
    def test_archive_task_has_retry_logic(self):
        """Vérifie que la tâche d'archivage a la logique de retry."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'if self.request.retries < self.max_retries:' in content
        assert 'raise self.retry(exc=exc)' in content
        assert 'Maximum de retries atteint' in content


@pytest.mark.unit
class TestHealthCheckTask:
    """Tests de la tâche health_check_task."""
    
    def test_health_check_task_decorator_configuration(self):
        """Vérifie la configuration du décorateur de santé."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'bind=True, base=CallbackTask, name=HEALTH_TASK_NAME, max_retries=2' in content
    
    def test_health_check_task_function_signature(self):
        """Vérifie la signature de la fonction health_check_task."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'def health_check_task(self) -> Dict[str, Any]:' in content
    
    def test_health_check_task_has_docstring(self):
        """Vérifie que la tâche de santé a une docstring."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'Tâche de vérification de santé du système' in content
        assert 'Statut de santé du système' in content


@pytest.mark.unit
class TestTasksLogging:
    """Tests de logging des tâches."""
    
    def test_tasks_configures_logger(self):
        """Vérifie que les tâches configurent le logger."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'logger = logging.getLogger(__name__)' in content
    
    def test_tasks_log_important_events(self):
        """Vérifie que les tâches loggent les événements importants."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'Starting market data archival task' in content
        assert 'Archival completed:' in content
        assert 'Archive task failed:' in content
        assert 'Running health check' in content


@pytest.mark.unit
class TestTasksErrorHandling:
    """Tests de gestion d'erreurs des tâches."""
    
    def test_tasks_have_exception_handling(self):
        """Vérifie que les tâches gèrent les exceptions."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'try:' in content
        assert 'except Exception as exc:' in content
    
    def test_tasks_return_error_status(self):
        """Vérifie que les tâches retournent un statut d'erreur."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert '"status": "failed"' in content
        assert '"error": str(exc)' in content
        assert '"timestamp":' in content


@pytest.mark.unit
class TestTasksPerformanceFeatures:
    """Tests des fonctionnalités de performance des tâches."""
    
    def test_archive_task_has_timeout_protection(self):
        """Vérifie que la tâche d'archivage a une protection timeout."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'timeout=1800' in content  # 30 minutes
        assert 'concurrent.futures.ThreadPoolExecutor' in content
    
    def test_archive_task_monitors_success_rate(self):
        """Vérifie que la tâche d'archivage surveille le taux de succès."""
        tasks_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'background' / 'tasks.py'
        with open(tasks_path, 'r') as f:
            content = f.read()
        
        assert 'success_rate = report.get("success_rate", 0)' in content
        assert 'if success_rate < 80:' in content
        assert 'Low success rate' in content
