"""
Tests unitaires pour le CLI d'archivage des données de marché.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur les imports, instanciations et validations de base.
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


@pytest.mark.unit
class TestCLIModuleStructure:
    """Tests de structure et disponibilité du module CLI."""

    def test_cli_module_file_exists(self):
        """Vérifie que le fichier CLI existe."""
        # Chemin depuis le répertoire backend
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        assert cli_path.exists()
        assert cli_path.is_file()

    def test_cli_module_has_shebang(self):
        """Vérifie que le module CLI a le shebang correct."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            first_line = f.readline().strip()
        assert first_line == "#!/usr/bin/env python3"

    def test_cli_module_has_docstring(self):
        """Vérifie que le module CLI a une docstring."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()
        assert "CLI pour la gestion des tâches" in content
        assert "archivage des données de marché" in content


@pytest.mark.unit
class TestCLIImports:
    """Tests d'imports avec gestion des dépendances externes."""

    @patch("sys.modules")
    def test_cli_required_imports_exist(self, mock_modules):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = ["asyncio", "logging", "sys", "pathlib", "typing", "click"]

        for import_name in required_imports:
            try:
                importlib.import_module(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")


@pytest.mark.unit
class TestCLIConfiguration:
    """Tests de configuration du CLI."""

    def test_cli_logging_setup_exists(self):
        """Vérifie que la configuration logging est présente."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "logging.basicConfig" in content
        assert "logging.getLogger(__name__)" in content

    def test_cli_click_decorators_present(self):
        """Vérifie que les décorateurs Click sont présents."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "@click.group()" in content
        assert "@cli.command()" in content
        assert "@click.option(" in content


@pytest.mark.unit
class TestCLIFunctionSignatures:
    """Tests des signatures de fonctions CLI."""

    def test_cli_main_group_signature(self):
        """Vérifie la signature du groupe CLI principal."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "def cli(debug: bool):" in content
        assert "Boursa Vision - Market Data Archiver CLI" in content

    def test_archive_command_signature(self):
        """Vérifie la signature de la commande archive."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "def archive(interval: str, period: str):" in content
        assert "Archive market data for all configured symbols." in content

    def test_archive_symbols_command_signature(self):
        """Vérifie la signature de la commande archive-symbols."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "def archive_symbols(symbols: tuple, interval: str):" in content
        assert "Archive specific symbols manually." in content


@pytest.mark.unit
class TestCLICommandOptions:
    """Tests des options de commande CLI."""

    def test_archive_command_has_interval_option(self):
        """Vérifie que la commande archive a l'option interval."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "--interval" in content
        assert "Time interval for data archival" in content
        assert "type=click.Choice([" in content

    def test_archive_command_has_period_option(self):
        """Vérifie que la commande archive a l'option period."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "--period" in content
        assert "Period of data to retrieve" in content


@pytest.mark.unit
class TestCLIErrorHandling:
    """Tests de gestion d'erreurs du CLI."""

    def test_cli_has_exception_handling(self):
        """Vérifie que le CLI gère les exceptions."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "try:" in content
        assert "except Exception as e:" in content
        assert "sys.exit(1)" in content

    def test_cli_has_logging_statements(self):
        """Vérifie que le CLI a des statements de logging."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        assert "logger.info(" in content
        assert "logger.error(" in content


@pytest.mark.unit
class TestCLIConstants:
    """Tests des constantes et configurations du CLI."""

    def test_cli_has_valid_intervals(self):
        """Vérifie que les intervalles valides sont définis."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        expected_intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]
        for interval in expected_intervals:
            assert f'"{interval}"' in content

    def test_cli_has_valid_periods(self):
        """Vérifie que les périodes valides sont définies."""
        cli_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "background"
            / "cli.py"
        )
        with open(cli_path, "r") as f:
            content = f.read()

        expected_periods = [
            "1d",
            "5d",
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y",
            "10y",
            "ytd",
            "max",
        ]
        for period in expected_periods:
            assert f'"{period}"' in content
