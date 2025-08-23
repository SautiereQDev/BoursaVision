"""
Configuration globale centralisée pour Boursa Vision.

Ce module fournit une configuration unifiée basée sur Pydantic Settings
qui charge automatiquement les variables d'environnement depuis les fichiers
.env de la racine du projet selon l'environnement spécifié.
"""

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_list_env(value: str) -> list[str]:
    """Parse une liste depuis une variable d'environnement."""
    if not value or value == "":
        return []
    # Essaye d'abord JSON
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    # Sinon, split par virgules
    return [item.strip() for item in value.split(",") if item.strip()]


class GlobalSettings(BaseSettings):
    """Configuration globale de l'application Boursa Vision."""

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_list_separator=",",
    )

    # =====================================
    # ENVIRONMENT & APPLICATION
    # =====================================
    environment: Literal["development", "staging", "production", "testing"] = Field(
        default="development", env="ENVIRONMENT"
    )
    debug: bool = Field(default=False, env="DEBUG")
    app_name: str = Field(default="Boursa Vision", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", env="LOG_LEVEL"
    )

    # =====================================
    # DATABASE CONFIGURATION
    # =====================================
    postgres_user: str = Field(env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    postgres_db: str = Field(env="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")

    # URL construite automatiquement
    database_url: str | None = Field(default=None, env="DATABASE_URL")
    test_database_url: str | None = Field(default=None, env="TEST_DATABASE_URL")

    # Pool settings
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_pool_overflow: int = Field(default=10, env="DB_POOL_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # =====================================
    # REDIS CONFIGURATION
    # =====================================
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str | None = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_url: str | None = Field(default=None, env="REDIS_URL")

    # =====================================
    # SECURITY & AUTH
    # =====================================
    secret_key: str = Field(env="SECRET_KEY")
    jwt_secret_key: str | None = Field(default=None, env="JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # =====================================
    # API CONFIGURATION
    # =====================================
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    allowed_hosts_env: str | None = Field(default=None, env="ALLOWED_HOSTS")
    cors_origins_env: str | None = Field(default=None, env="CORS_ORIGINS")

    @property
    def allowed_hosts(self) -> list[str]:
        """Liste des hôtes autorisés."""
        if self.allowed_hosts_env:
            return parse_list_env(self.allowed_hosts_env)
        return ["localhost", "127.0.0.1"]

    @property
    def cors_origins(self) -> list[str]:
        """Liste des origines CORS autorisées."""
        if self.cors_origins_env:
            return parse_list_env(self.cors_origins_env)
        return ["http://localhost:3000"]

    # =====================================
    # FRONTEND CONFIGURATION
    # =====================================
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    vite_api_base_url: str = Field(
        default="http://localhost:8000/api/v1", env="VITE_API_BASE_URL"
    )
    vite_ws_url: str = Field(default="ws://localhost:8000/ws", env="VITE_WS_URL")

    # =====================================
    # EXTERNAL SERVICES
    # =====================================
    # YFinance
    yfinance_rate_limit: int = Field(default=10, env="YFINANCE_RATE_LIMIT")
    yfinance_batch_size: int = Field(default=50, env="YFINANCE_BATCH_SIZE")
    yfinance_timeout: int = Field(default=30, env="YFINANCE_TIMEOUT")
    yfinance_retry_attempts: int = Field(default=3, env="YFINANCE_RETRY_ATTEMPTS")

    # Market Data Cache
    market_data_cache_ttl: int = Field(default=300, env="MARKET_DATA_CACHE_TTL")
    real_time_data_cache_ttl: int = Field(default=60, env="REAL_TIME_DATA_CACHE_TTL")

    # =====================================
    # MARKET DATA ARCHIVAL
    # =====================================
    enable_automatic_archival: bool = Field(
        default=True, env="ENABLE_AUTOMATIC_ARCHIVAL"
    )

    # Scheduling configuration
    archival_frequent_interval: int = Field(default=5, env="ARCHIVAL_FREQUENT_INTERVAL")
    archival_daily_hour: int = Field(default=18, env="ARCHIVAL_DAILY_HOUR")
    archival_weekly_day: int = Field(default=0, env="ARCHIVAL_WEEKLY_DAY")
    archival_weekly_hour: int = Field(default=20, env="ARCHIVAL_WEEKLY_HOUR")

    # Batch processing
    archival_batch_size: int = Field(default=25, env="ARCHIVAL_BATCH_SIZE")
    archival_concurrent_workers: int = Field(
        default=2, env="ARCHIVAL_CONCURRENT_WORKERS"
    )
    archival_request_delay: float = Field(default=0.2, env="ARCHIVAL_REQUEST_DELAY")

    # Data retention
    archival_retention_days: int = Field(default=1095, env="ARCHIVAL_RETENTION_DAYS")
    archival_cleanup_enabled: bool = Field(default=True, env="ARCHIVAL_CLEANUP_ENABLED")

    # Error handling
    archival_max_retries: int = Field(default=3, env="ARCHIVAL_MAX_RETRIES")
    archival_retry_delay: int = Field(default=60, env="ARCHIVAL_RETRY_DELAY")
    archival_error_threshold: int = Field(default=20, env="ARCHIVAL_ERROR_THRESHOLD")

    # =====================================
    # BACKGROUND TASKS
    # =====================================
    celery_broker_url: str | None = Field(default=None, env="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, env="CELERY_RESULT_BACKEND")

    # =====================================
    # TESTING & DEVELOPMENT
    # =====================================
    use_mock_repositories: bool = Field(default=False, env="USE_MOCK_REPOSITORIES")
    testing: bool = Field(default=False, env="TESTING")

    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_list_separator=",",
        env_parse_none_str="empty",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, v: str | None, info) -> str:
        """Construit l'URL de la base de données si elle n'est pas fournie."""
        if isinstance(v, str) and v:
            return v

        # Récupère les valeurs depuis les données du modèle
        values = info.data if hasattr(info, "data") else {}
        user = values.get("postgres_user")
        password = values.get("postgres_password")
        host = values.get("postgres_host", "localhost")
        port = values.get("postgres_port", 5432)
        db = values.get("postgres_db")

        if user and password and db:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return ""

    @field_validator("test_database_url", mode="before")
    @classmethod
    def assemble_test_database_url(cls, v: str | None, info) -> str:
        """Construit l'URL de la base de données de test si elle n'est pas fournie."""
        if isinstance(v, str) and v:
            return v

        # Récupère les valeurs depuis les données du modèle
        values = info.data if hasattr(info, "data") else {}
        # En développement et test, utilise SQLite en mémoire
        environment = values.get("environment", "development")
        if environment in ["development", "testing"]:
            return "sqlite:///:memory:"

        # En production, utilise une DB dédiée
        base_url = values.get("database_url", "")
        if base_url:
            return base_url.replace(
                values.get("postgres_db", ""), f"{values.get('postgres_db', '')}_test"
            )
        return "sqlite:///:memory:"

    @field_validator("redis_url", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str | None, info) -> str:
        """Construit l'URL Redis si elle n'est pas fournie."""
        if isinstance(v, str) and v:
            return v

        values = info.data if hasattr(info, "data") else {}
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        password = values.get("redis_password")
        db = values.get("redis_db", 0)

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def assemble_celery_broker_url(cls, v: str | None, info) -> str:
        """Construit l'URL du broker Celery si elle n'est pas fournie."""
        if isinstance(v, str) and v:
            return v
        values = info.data if hasattr(info, "data") else {}
        return values.get("redis_url", "redis://localhost:6379/0")

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def assemble_celery_result_backend(cls, v: str | None, info) -> str:
        """Construit l'URL du backend de résultats Celery si elle n'est pas fournie."""
        if isinstance(v, str) and v:
            return v
        values = info.data if hasattr(info, "data") else {}
        return values.get("redis_url", "redis://localhost:6379/0")

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def assemble_jwt_secret_key(cls, v: str | None, info) -> str:
        """Utilise secret_key comme JWT secret key si non fournie."""
        if isinstance(v, str) and v:
            return v
        values = info.data if hasattr(info, "data") else {}
        return values.get("secret_key", "")

    @field_validator(
        "archival_frequent_interval",
        "archival_daily_hour",
        "archival_weekly_day",
        "archival_weekly_hour",
        "archival_batch_size",
        "archival_concurrent_workers",
        "archival_retention_days",
        "archival_max_retries",
        "archival_retry_delay",
        "archival_error_threshold",
        mode="before",
    )
    @classmethod
    def clean_numeric_env_vars(cls, v: Any) -> Any:
        """Nettoie les commentaires des variables d'environnement numériques."""
        if isinstance(v, str):
            # Retire tout ce qui vient après un #
            cleaned = v.split("#")[0].strip()
            try:
                # Essaye de convertir en int si c'est possible
                if "." in cleaned:
                    return float(cleaned)
                else:
                    return int(cleaned)
            except ValueError:
                return cleaned
        return v

    @field_validator("archival_request_delay", mode="before")
    @classmethod
    def clean_float_env_vars(cls, v: Any) -> Any:
        """Nettoie les commentaires des variables d'environnement flottantes."""
        if isinstance(v, str):
            # Retire tout ce qui vient après un #
            cleaned = v.split("#")[0].strip()
            try:
                return float(cleaned)
            except ValueError:
                return cleaned
        return v

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
    """Trouve la racine du projet en remontant l'arborescence."""
    current_path = Path(__file__).resolve()

    # Cherche le fichier .env dans les répertoires parents
    for parent in current_path.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return parent

    # Fallback: cherche un dossier avec des indicateurs de racine de projet
    for parent in current_path.parents:
        if any(
            (parent / indicator).exists()
            for indicator in [
                "pyproject.toml",
                "setup.py",
                "Makefile",
                "docker-compose.yml",
                ".git",
            ]
        ):
            return parent

    # Dernière option: le répertoire actuel
    return current_path.parent


def load_env_variables() -> dict[str, Any]:
    """
    Charge les variables d'environnement depuis les fichiers .env appropriés.

    Ordre de priorité:
    1. Variables d'environnement système
    2. .env (racine du projet)
    3. .env.local (non versionné, spécifique à la machine)
    """
    project_root = find_project_root()
    env_vars: dict[str, Any] = {}

    # Fichiers .env à charger par ordre de priorité (le dernier écrase le premier)
    env_files = [
        project_root / ".env.template",  # Template par défaut
        project_root / ".env",  # Configuration principale
        project_root / ".env.local",  # Configuration locale (non versionnée)
    ]

    for env_file in env_files:
        if env_file.exists():
            env_vars.update(_parse_env_file(env_file, env_vars))

    return env_vars


def _parse_env_file(env_file: Path, existing_vars: dict[str, Any]) -> dict[str, Any]:
    """Parse un fichier .env et retourne les variables."""
    vars_dict: dict[str, Any] = {}

    try:
        with open(env_file, encoding="utf-8") as f:
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
                value = _remove_quotes(value)

                # Substitution de variables ${VAR}
                value = _substitute_variables(value, existing_vars)

                vars_dict[key] = value

    except Exception as e:
        logging.warning(f"Erreur lors du chargement de {env_file}: {e}")

    return vars_dict


def _remove_quotes(value: str) -> str:
    """Supprime les guillemets d'une valeur."""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _substitute_variables(value: str, existing_vars: dict[str, Any]) -> str:
    """Substitue les variables ${VAR} dans une valeur."""
    for match in re.finditer(r"\$\{([^}]+)\}", value):
        var_name = match.group(1)
        # Cherche d'abord dans les env vars système, puis dans celles déjà chargées
        var_value = os.getenv(var_name, existing_vars.get(var_name, ""))
        value = value.replace(match.group(0), var_value)
    return value


@lru_cache
def get_settings() -> GlobalSettings:
    """
    Retourne l'instance singleton des paramètres de configuration.

    Utilise lru_cache pour éviter de recharger les paramètres à chaque appel.
    """
    # Charge les variables d'environnement avant de créer les settings
    load_env_to_os()
    return GlobalSettings()


def load_env_to_os():
    """Charge les variables d'environnement dans os.environ."""
    env_vars = load_env_variables()
    for key, value in env_vars.items():
        if key not in os.environ:  # Ne surcharge pas les variables système existantes
            os.environ[key] = str(value)


# Instance globale pour l'import direct
settings = get_settings()
