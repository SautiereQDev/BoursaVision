"""
Configuration for the API
"""
from enum import Enum
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class APISettings(BaseSettings):
    """API configuration settings."""

    # Application settings
    app_name: str = Field(default="Boursa Vision API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Investment portfolio management platform",
        description="Application description",
    )
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=True)

    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=True)

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins",
    )
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_calls: int = Field(default=100, description="Calls per minute")
    rate_limit_period: int = Field(default=60, description="Period in seconds")

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-please-change-in-production",
        description="Secret key for JWT tokens",
    )
    access_token_expire_minutes: int = Field(default=30)
    algorithm: str = Field(default="HS256")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/boursa_vision",
        description="Database URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and sessions",
    )

    # External APIs
    yfinance_timeout: int = Field(default=30)

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = APISettings()
