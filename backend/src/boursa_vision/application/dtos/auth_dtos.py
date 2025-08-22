"""
Authentication DTOs (Data Transfer Objects)
==========================================

Pydantic models for authentication API requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request model for user login"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Request model for user registration"""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    
    refresh_token: str = Field(..., description="Refresh token")


class TokenResponse(BaseModel):
    """Response model for authentication tokens"""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class UserResponse(BaseModel):
    """Response model for user information"""
    
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    email_verified: bool = Field(..., description="Whether email is verified")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login date")


class LoginResponse(BaseModel):
    """Response model for successful login"""
    
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="Authentication tokens")


class RegisterResponse(BaseModel):
    """Response model for successful registration"""
    
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    role: str = Field(..., description="User role")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    
    user: UserResponse = Field(..., description="User information")
    permissions: List[str] = Field(..., description="User permissions")


class ChangePasswordRequest(BaseModel):
    """Request model for password change"""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class LogoutRequest(BaseModel):
    """Request model for logout"""
    
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")
    logout_all_sessions: bool = Field(default=False, description="Logout from all sessions")


class AuthErrorResponse(BaseModel):
    """Response model for authentication errors"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class UserPermissionsResponse(BaseModel):
    """Response model for user permissions"""
    
    permissions: List[str] = Field(..., description="List of user permissions")
    role: str = Field(..., description="User role")


class ActiveSessionsResponse(BaseModel):
    """Response model for active user sessions"""
    
    active_sessions: int = Field(..., description="Number of active sessions")
    sessions: List[dict] = Field(..., description="Session details")


class AuthStatusResponse(BaseModel):
    """Response model for authentication status check"""
    
    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[UserResponse] = Field(None, description="User information if authenticated")
    permissions: Optional[List[str]] = Field(None, description="User permissions if authenticated")
