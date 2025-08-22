"""Authentication DTOs for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Request DTO for user login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response DTO for successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: str


class RegisterRequest(BaseModel):
    """Request DTO for user registration."""
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class RegisterResponse(BaseModel):
    """Response DTO for successful registration."""
    user_id: str
    email: str
    message: str = "User registered successfully"


class RefreshTokenRequest(BaseModel):
    """Request DTO for token refresh."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Response DTO for token refresh."""
    access_token: str
    expires_at: datetime
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Request DTO for password reset initiation."""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Request DTO for password reset confirmation."""
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Request DTO for password change."""
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    """Response DTO for user data."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    is_active: bool


class TokenResponse(BaseModel):
    """Response DTO for token operations."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserProfileResponse(BaseModel):
    """Response DTO for user profile."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    is_active: bool
