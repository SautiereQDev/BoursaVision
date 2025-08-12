#!/usr/bin/env python3
"""
Script de migration pour remplacer tous les usages d'os.getenv() par la nouvelle configuration globale.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Mapping des variables d'environnement vers les propriétés de settings
ENV_VAR_MAPPING = {
    "ENVIRONMENT": "settings.environment",
    "DEBUG": "settings.debug",
    "USE_MOCK_REPOSITORIES": "settings.use_mock_repositories",
    "DATABASE_URL": "settings.database_url",
    "POSTGRES_HOST": "settings.postgres_host",
    "POSTGRES_PORT": "settings.postgres_port",
    "POSTGRES_DB": "settings.postgres_db",
    "POSTGRES_USER": "settings.postgres_user",
    "POSTGRES_PASSWORD": "settings.postgres_password",
    "REDIS_URL": "settings.redis_url",
    "REDIS_HOST": "settings.redis_host",
    "REDIS_PORT": "settings.redis_port",
    "SECRET_KEY": "settings.secret_key",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "settings.access_token_expire_minutes",
    "LOG_LEVEL": "settings.log_level",
    "YFINANCE_RATE_LIMIT": "settings.yfinance_rate_limit",
    "MARKET_DATA_CACHE_TTL": "settings.market_data_cache_ttl",
}


def find_python_files(root_dir: Path) -> List[Path]:
    """Trouve tous les fichiers Python dans le répertoire."""
    python_files = []
    for path in root_dir.rglob("*.py"):
        # Ignore les fichiers de config et de migration
        if "config" in path.name or "migration" in path.name:
            continue
        python_files.append(path)
    return python_files


def find_os_getenv_usage(file_path: Path) -> List[Tuple[int, str, str]]:
    """Trouve tous les usages d'os.getenv() dans un fichier."""
    usages = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            # Pattern pour os.getenv("VAR", "default")
            match = re.search(
                r'os\.getenv\(\s*["\']([^"\']+)["\']\s*(?:,\s*["\']?([^"\']*)["\']?)?\)',
                line,
            )
            if match:
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ""
                usages.append((i, var_name, default_value))
    except Exception as e:
        print(f"Erreur lors de la lecture de {file_path}: {e}")

    return usages


def suggest_replacement(var_name: str, default_value: str) -> str:
    """Suggère un remplacement pour une variable d'environnement."""
    if var_name in ENV_VAR_MAPPING:
        return ENV_VAR_MAPPING[var_name]
    else:
        # Pour les variables non mappées, suggérer un ajout à la config
        return f"# TODO: Ajouter {var_name} à GlobalSettings"


def analyze_file(file_path: Path) -> Dict:
    """Analyse un fichier pour les usages d'os.getenv()."""
    usages = find_os_getenv_usage(file_path)

    if not usages:
        return None

    analysis = {"file": str(file_path), "usages": [], "needs_import": True}

    for line_num, var_name, default_value in usages:
        replacement = suggest_replacement(var_name, default_value)
        analysis["usages"].append(
            {
                "line": line_num,
                "variable": var_name,
                "default": default_value,
                "replacement": replacement,
            }
        )

    return analysis


def main():
    """Fonction principale."""
    project_root = Path(__file__).parent.parent
    print(f"🔍 Analyse du projet: {project_root}")
    print("=" * 60)

    python_files = find_python_files(project_root / "src")
    print(f"📁 Fichiers Python trouvés: {len(python_files)}")

    files_to_migrate = []

    for file_path in python_files:
        analysis = analyze_file(file_path)
        if analysis:
            files_to_migrate.append(analysis)

    if not files_to_migrate:
        print("✅ Aucun usage d'os.getenv() trouvé dans les fichiers src/")
        return

    print(f"\n📊 Fichiers nécessitant une migration: {len(files_to_migrate)}")
    print("=" * 60)

    for file_analysis in files_to_migrate:
        print(f"\n📄 {file_analysis['file']}")
        print("-" * 40)

        for usage in file_analysis["usages"]:
            print(f"  Ligne {usage['line']}: {usage['variable']}")
            if usage["default"]:
                print(f"    Valeur par défaut: {usage['default']}")
            print(f"    → Remplacer par: {usage['replacement']}")

        if file_analysis["needs_import"]:
            print("  ⚠️  Ajouter: from src.core.config_simple import settings")

    print("\n" + "=" * 60)
    print("🚀 Migration recommandée:")
    print("1. Ajouter l'import de settings dans chaque fichier")
    print("2. Remplacer os.getenv() par settings.propriété")
    print("3. Ajouter les variables manquantes à GlobalSettings si nécessaire")
    print("4. Tester que tout fonctionne correctement")


if __name__ == "__main__":
    main()
