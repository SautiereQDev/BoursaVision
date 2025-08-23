"""
Authentication Configuration
===========================

Configuration settings for JWT authentication system.
"""

import secrets
from datetime import timedelta

from pydantic import BaseSettings, Field


class AuthSettings(BaseSettings):
    """Authentication configuration settings."""

    # JWT Settings
    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(
        default="HS256", description="Algorithm for JWT token signing"
    )
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=30, description="Refresh token expiration time in days"
    )

    # Password Settings
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_uppercase: bool = Field(
        default=True, description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True, description="Require lowercase letters in password"
    )
    password_require_numbers: bool = Field(
        default=True, description="Require numbers in password"
    )
    password_require_special: bool = Field(
        default=True, description="Require special characters in password"
    )

    # Rate Limiting Settings
    login_rate_limit: str = Field(
        default="10/minute", description="Rate limit for login attempts"
    )
    register_rate_limit: str = Field(
        default="5/minute", description="Rate limit for registration attempts"
    )
    refresh_rate_limit: str = Field(
        default="20/minute", description="Rate limit for token refresh"
    )

    # Security Settings
    token_url: str = Field(
        default="/api/v1/auth/login", description="URL for token endpoint"
    )
    max_refresh_tokens_per_user: int = Field(
        default=5, description="Maximum number of active refresh tokens per user"
    )

    class Config:
        env_prefix = "AUTH_"
        case_sensitive = False


# Global auth settings instance
auth_settings = AuthSettings()


def get_auth_settings() -> AuthSettings:
    """Get authentication settings."""
    return auth_settings


# Derived settings
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=auth_settings.access_token_expire_minutes)
REFRESH_TOKEN_EXPIRE_DELTA = timedelta(days=auth_settings.refresh_token_expire_days)
