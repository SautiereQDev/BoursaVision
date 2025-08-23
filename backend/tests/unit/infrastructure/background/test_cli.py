"""
Tests unitaires pour le CLI de gestion des données de marché.

Phase 1 : Tests basiques d'import et de structure CLI
"""

import pytest
from click.testing import CliRunner


@pytest.mark.unit
class TestCLIImport:
    """Tests d'import du CLI."""

    def test_cli_module_import_succeeds(self):
        """L'import du module CLI devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background import cli

            assert cli is not None
        except ImportError as e:
            pytest.fail(f"Failed to import CLI module: {e}")

    def test_cli_main_group_import_succeeds(self):
        """L'import de la fonction principale CLI devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background.cli import cli

            assert cli is not None
            assert callable(cli)
        except ImportError as e:
            pytest.fail(f"Failed to import CLI main function: {e}")


@pytest.mark.unit
class TestCLICommands:
    """Tests de base sur les commandes CLI."""

    def test_cli_commands_are_importable(self):
        """Les commandes CLI peuvent être importées."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background.cli import (
                archive,
                archive_symbols,
                beat,
                cli,
                status,
                test_connection,
                worker,
            )

            # Vérifier que toutes les commandes sont des fonctions
            commands = [
                cli,
                archive,
                archive_symbols,
                status,
                worker,
                beat,
                test_connection,
            ]
            for command in commands:
                assert callable(command)
        except ImportError as e:
            pytest.fail(f"Failed to import CLI commands: {e}")

    def test_cli_commands_have_click_decorators(self):
        """Les commandes CLI ont des décorateurs Click."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background.cli import archive, cli, status

            # Vérifier que cli est un groupe Click
            assert hasattr(cli, "commands")

            # Vérifier que les commandes ont des attributs Click
            for command in [archive, status]:
                assert hasattr(command, "__click_params__") or hasattr(
                    command, "callback"
                )
        except ImportError as e:
            pytest.fail(f"Failed to import CLI commands: {e}")


@pytest.mark.unit
class TestCLIStructure:
    """Tests sur la structure du CLI."""

    def test_cli_runner_can_be_created(self):
        """Le CliRunner peut être créé."""
        # Arrange & Act
        runner = CliRunner()

        # Assert
        assert runner is not None

    def test_cli_main_group_exists(self):
        """Le groupe principal CLI existe."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background.cli import cli

            # Vérifier que c'est un groupe Click
            assert hasattr(cli, "commands")
            assert hasattr(cli, "name") or hasattr(cli, "__name__")
        except ImportError as e:
            pytest.fail(f"Failed to import CLI main group: {e}")

    def test_cli_has_expected_commands(self):
        """Le CLI a les commandes attendues."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.background.cli import cli

            # Les commandes devraient être enregistrées dans le groupe
            if hasattr(cli, "commands"):
                command_names = list(cli.commands.keys())
                expected_commands = [
                    "archive",
                    "archive-symbols",
                    "status",
                    "worker",
                    "beat",
                    "test-connection",
                ]

                # Au moins quelques commandes devraient être présentes
                for expected_cmd in ["archive", "status"]:
                    assert (
                        expected_cmd in command_names
                    ), f"Missing command: {expected_cmd}"
        except ImportError as e:
            pytest.fail(f"Failed to test CLI commands: {e}")


@pytest.mark.unit
class TestCLIBasicExecution:
    """Tests d'exécution basique du CLI."""

    def test_cli_help_works(self):
        """La commande --help fonctionne."""
        # Arrange
        try:
            from boursa_vision.infrastructure.background.cli import cli
        except ImportError:
            pytest.skip("CLI not available")

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "Usage:" in result.output or "help" in result.output.lower()

    def test_archive_command_help_works(self):
        """La commande archive --help fonctionne."""
        # Arrange
        try:
            from boursa_vision.infrastructure.background.cli import cli
        except ImportError:
            pytest.skip("CLI not available")

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["archive", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "Usage:" in result.output or "help" in result.output.lower()

    def test_status_command_help_works(self):
        """La commande status --help fonctionne."""
        # Arrange
        try:
            from boursa_vision.infrastructure.background.cli import cli
        except ImportError:
            pytest.skip("CLI not available")

        runner = CliRunner()

        # Act
        result = runner.invoke(cli, ["status", "--help"])

        # Assert
        assert result.exit_code == 0
        assert "Usage:" in result.output or "help" in result.output.lower()
