"""
Script de migration pour centraliser la configuration.

Ce script aide à migrer depuis l'ancien système de configuration dispersé
vers le nouveau système de configuration globale centralisée.
"""

import os
import shutil
from pathlib import Path


def consolidate_env_files():
    """Consolide les fichiers .env dispersés vers la racine du projet."""

    project_root = find_project_root()

    # Fichiers .env à consolider
    env_sources = [
        project_root / "backend" / ".env.development",
        project_root / "backend" / ".env.production",
        project_root / "docker" / ".env",
    ]

    # Fichier .env principal
    main_env = project_root / ".env"

    print(f"📁 Racine du projet: {project_root}")
    print(f"📄 Fichier .env principal: {main_env}")

    # Backup de l'ancien .env s'il existe
    if main_env.exists():
        backup_path = project_root / ".env.backup"
        shutil.copy2(main_env, backup_path)
        print(f"💾 Sauvegarde: {backup_path}")

    # Analyse et fusion des configurations
    merged_config = {}
    comments = []

    for env_file in env_sources:
        if env_file.exists():
            print(f"📖 Lecture: {env_file}")
            config, file_comments = parse_env_file(env_file)
            merged_config.update(config)
            comments.extend(file_comments)

    # Génération du nouveau .env centralisé
    generate_consolidated_env(main_env, merged_config, comments)

    print("✅ Configuration centralisée générée avec succès!")
    print(f"🔧 Fichier principal: {main_env}")
    print("\n📋 Prochaines étapes:")
    print("1. Vérifiez le fichier .env généré")
    print("2. Supprimez les anciens fichiers .env dispersés")
    print("3. Mettez à jour vos scripts pour utiliser la configuration globale")


def find_project_root() -> Path:
    """Trouve la racine du projet."""
    current_path = Path(__file__).resolve()

    for parent in current_path.parents:
        if any(
            (parent / indicator).exists()
            for indicator in [
                "pyproject.toml",
                "Makefile",
                ".git",
                "docker-compose.yml",
            ]
        ):
            return parent

    return current_path.parent


def parse_env_file(env_file: Path):
    """Parse un fichier .env et retourne les variables et commentaires."""
    config = {}
    comments = []

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            current_section = None

            for line in f:
                line = line.strip()

                # Commentaires de section
                if line.startswith("# ==="):
                    current_section = line
                    comments.append(line)
                    continue

                # Autres commentaires
                if line.startswith("#"):
                    comments.append(line)
                    continue

                # Variables
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")

                    # Enrichissement avec section
                    if current_section:
                        config[key] = {
                            "value": value,
                            "section": current_section,
                            "file": env_file.name,
                        }
                    else:
                        config[key] = {"value": value, "file": env_file.name}

    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture de {env_file}: {e}")

    return config, comments


def generate_consolidated_env(output_path: Path, config: dict, comments: list):
    """Génère le fichier .env consolidé."""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Boursa Vision - Configuration Centralisée\n")
        f.write("# Générée automatiquement - Vérifiez et ajustez selon vos besoins\n\n")

        # Sections organisées
        sections = {
            "ENVIRONMENT": [
                "ENVIRONMENT",
                "DEBUG",
                "LOG_LEVEL",
                "APP_NAME",
                "APP_VERSION",
            ],
            "DATABASE": ["POSTGRES_", "DATABASE_URL", "DB_POOL"],
            "REDIS": ["REDIS_"],
            "SECURITY": ["SECRET_KEY", "JWT_", "ACCESS_TOKEN", "REFRESH_TOKEN"],
            "API": ["API_V1_STR", "ALLOWED_HOSTS", "CORS_ORIGINS"],
            "FRONTEND": ["FRONTEND_URL", "VITE_"],
            "EXTERNAL": ["YFINANCE_", "MARKET_DATA_"],
            "TASKS": ["CELERY_"],
            "TESTING": ["USE_MOCK_", "TESTING"],
        }

        for section_name, prefixes in sections.items():
            section_vars = {}

            for key, data in config.items():
                for prefix in prefixes:
                    if key.startswith(prefix):
                        section_vars[key] = data
                        break

            if section_vars:
                f.write(f"# ===================================\n")
                f.write(f"# {section_name} CONFIGURATION\n")
                f.write(f"# ===================================\n")

                for key, data in section_vars.items():
                    value = data["value"]
                    source = data.get("file", "unknown")
                    f.write(f"{key}={value}  # from {source}\n")

                f.write("\n")

        # Variables non catégorisées
        uncategorized = {}
        for key, data in config.items():
            found = False
            for prefixes in sections.values():
                for prefix in prefixes:
                    if key.startswith(prefix):
                        found = True
                        break
                if found:
                    break

            if not found:
                uncategorized[key] = data

        if uncategorized:
            f.write("# ===================================\n")
            f.write("# OTHER VARIABLES\n")
            f.write("# ===================================\n")

            for key, data in uncategorized.items():
                value = data["value"]
                source = data.get("file", "unknown")
                f.write(f"{key}={value}  # from {source}\n")


def cleanup_old_env_files():
    """Supprime les anciens fichiers .env après confirmation."""
    project_root = find_project_root()

    old_files = [
        project_root / "backend" / ".env.development",
        project_root / "backend" / ".env.production",
    ]

    print("\n🧹 Nettoyage des anciens fichiers .env:")

    for file_path in old_files:
        if file_path.exists():
            response = input(f"Supprimer {file_path}? (y/N): ")
            if response.lower() == "y":
                file_path.unlink()
                print(f"🗑️  Supprimé: {file_path}")
            else:
                print(f"🔒 Conservé: {file_path}")


if __name__ == "__main__":
    print("🔧 Migration vers la configuration centralisée")
    print("=" * 50)

    consolidate_env_files()

    response = input("\nSouhaitez-vous nettoyer les anciens fichiers .env? (y/N): ")
    if response.lower() == "y":
        cleanup_old_env_files()

    print("\n✅ Migration terminée!")
