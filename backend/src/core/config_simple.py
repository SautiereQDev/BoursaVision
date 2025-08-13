"""
Configuration globale simplifiée pour Boursa Vision.

Version simplifiée et compatible avec Pydantic v2.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class GlobalSettings(BaseSettings):
    """Configuration globale de l'application Boursa Vision."""

    # =====================================
    # ENVIRONMENT & APPLICATION
    # =====================================
    environment: Literal["development", "staging", "production", "testing"] = Field(
        default="development", description="Environnement d'exécution"
    )
    debug: bool = Field(default=False, description="Mode debug")
    app_name: str = Field(default="Boursa Vision", description="Nom de l'application")
    app_version: str = Field(default="1.0.0", description="Version de l'application")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Niveau de log"
    )

    # =====================================
    # DATABASE CONFIGURATION
    # =====================================
    postgres_user: str = Field(
        default="boursa_user", description="Utilisateur PostgreSQL"
    )
    postgres_password: str = Field(
        default="boursa_dev_password_2024", description="Mot de passe PostgreSQL"
    )
    postgres_db: str = Field(default="boursa_vision", description="Base de données")
    postgres_host: str = Field(default="localhost", description="Hôte PostgreSQL")
    postgres_port: int = Field(default=5432, description="Port PostgreSQL")

    # Pool settings
    db_pool_size: int = Field(default=5, description="Taille du pool de connexions")
    db_pool_overflow: int = Field(default=10, description="Connexions supplémentaires")
    db_pool_timeout: int = Field(default=30, description="Timeout du pool")

    # =====================================
    # REDIS CONFIGURATION
    # =====================================
    redis_host: str = Field(default="localhost", description="Hôte Redis")
    redis_port: int = Field(default=6379, description="Port Redis")
    redis_password: Optional[str] = Field(
        default=None, description="Mot de passe Redis"
    )
    redis_db: int = Field(default=0, description="Base de données Redis")

    # =====================================
    # SECURITY & AUTH
    # =====================================
    secret_key: str = Field(
        default="boursa_dev_secret_key_for_development_only_2024_not_for_production_use",
        description="Clé secrète pour l'application",
    )
    access_token_expire_minutes: int = Field(
        default=1440, description="Expiration token d'accès (minutes)"
    )
    refresh_token_expire_days: int = Field(
        default=30, description="Expiration refresh token (jours)"
    )

    # =====================================
    # API CONFIGURATION
    # =====================================
    api_v1_str: str = Field(default="/api/v1", description="Préfixe API v1")

    # =====================================
    # EXTERNAL SERVICES
    # =====================================
    yfinance_rate_limit: int = Field(default=10, description="Limite de taux YFinance")
    yfinance_batch_size: int = Field(default=50, description="Taille des lots YFinance")
    yfinance_timeout: int = Field(default=30, description="Timeout YFinance")
    yfinance_retry_attempts: int = Field(
        default=3, description="Tentatives de retry YFinance"
    )

    # Market Data Cache
    market_data_cache_ttl: int = Field(
        default=300, description="TTL cache données marché"
    )
    real_time_data_cache_ttl: int = Field(
        default=60, description="TTL cache temps réel"
    )

    # =====================================
    # TESTING & DEVELOPMENT
    # =====================================
    use_mock_repositories: bool = Field(
        default=False, description="Utiliser des repositories mock"
    )
    testing: bool = Field(default=False, description="Mode test")

    class Config:
        """Configuration Pydantic."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """Construit l'URL de la base de données."""
        if self.environment in ("development", "testing") or self.testing:
            return "sqlite:///:memory:"
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def test_database_url(self) -> str:
        """URL de la base de données de test."""
        return "sqlite:///:memory:"

    @property
    def redis_url(self) -> str:
        """Construit l'URL Redis."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker_url(self) -> str:
        """URL du broker Celery."""
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        """URL du backend de résultats Celery."""
        return self.redis_url

    @property
    def jwt_secret_key(self) -> str:
        """Clé secrète JWT."""
        return self.secret_key

    @property
    def is_development(self) -> bool:
        """Retourne True si l'environnement est development."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Retourne True si l'environnement est production."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Retourne True si l'environnement est testing."""
        return self.testing or self.environment == "testing"


def find_project_root() -> Path:
    """
    Trouve la racine du projet (répertoire parent du backend).
    Cherche les fichiers .env à la racine du projet, pas dans backend/.
    """
    current_path = Path(__file__).resolve()

    # Remonter jusqu'au répertoire backend
    while current_path.name != "backend" and current_path.parent != current_path:
        current_path = current_path.parent

    if current_path.name == "backend":
        # Remonter d'un niveau pour aller à la racine du projet
        project_root = current_path.parent
        print(f"🏠 Racine du projet trouvée: {project_root}")
        return project_root

    # Fallback: cherche les indicateurs de racine de projet
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if any(
            (parent / indicator).exists()
            for indicator in [
                "pyproject.toml",
                "setup.py",
                "Makefile",
                "docker-compose.yml",
                "docker-compose.dev.yml",
                ".git",
                "README.md",
            ]
        ):
            print(f"🏠 Racine du projet trouvée (fallback): {parent}")
            return parent

    # Dernière option: le répertoire du fichier config
    fallback = current_path.parent
    print(f"⚠️  Racine du projet non trouvée, utilisation de: {fallback}")
    return fallback


def load_env_file():
    """
    Charge les fichiers .env depuis la racine du projet dans les variables d'environnement.
    Ordre de priorité:
    1. Variables d'environnement système (les plus prioritaires)
    2. .env.local (ignoré par git)
    3. .env.{environment} (ex: .env.development, .env.production)
    4. .env (base commune)
    """
    project_root = find_project_root()
    print(f"🔍 Configuration project root: {project_root}")

    # Détermine l'environnement actuel pour charger le bon fichier
    environment = os.getenv("ENVIRONMENT", "development")

    # Liste des fichiers .env à charger (du moins prioritaire au plus prioritaire)
    env_files = [
        project_root / ".env",  # Base commune
        project_root / f".env.{environment}",  # Spécifique à l'environnement
        project_root / ".env.local",  # Local (ignore par git)
    ]

    for env_file in env_files:
        if env_file.exists():
            print(f"📄 Chargement: {env_file}")
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()

                        # Ignore les commentaires et lignes vides
                        if not line or line.startswith("#"):
                            continue

                        # Parse key=value
                        if "=" not in line:
                            continue

                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Supprime les guillemets
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        # Pour certains environnements, on veut surcharger même si déjà défini
                        # (ex: variables de base de données en testing)
                        override_vars = (
                            {
                                "DATABASE_URL",
                                "LOG_LEVEL",
                                "SECRET_KEY",
                                "POSTGRES_HOST",
                                "POSTGRES_PORT",
                                "POSTGRES_DB",
                                "POSTGRES_USER",
                                "POSTGRES_PASSWORD",
                            }
                            if environment == "testing"
                            else set()
                        )

                        # Ne surcharge que si la variable n'existe pas déjà ou si c'est autorisé
                        if key not in os.environ or key in override_vars:
                            os.environ[key] = value

            except Exception as e:
                print(f"Warning: Could not load .env file {env_file}: {e}")


@lru_cache()
def get_settings() -> GlobalSettings:
    """
    Retourne l'instance singleton des paramètres de configuration.

    Utilise lru_cache pour éviter de recharger les paramètres à chaque appel.
    """
    # Charge le fichier .env avant de créer les settings
    load_env_file()
    return GlobalSettings()


# Instance globale pour l'import direct
settings = get_settings()
