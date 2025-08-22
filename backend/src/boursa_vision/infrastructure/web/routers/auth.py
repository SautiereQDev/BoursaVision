"""
Simple Auth Router for E2E Tests
================================

Mock authentication endpoints for E2E testing.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Optional

# Router setup
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# Request/Response models
class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up new user",
    description="Mock signup endpoint for E2E tests",
)
async def signup(signup_data: SignupRequest) -> AuthResponse:
    """Mock signup endpoint for E2E tests."""
    return AuthResponse(
        user_id="mock-user-id",
        email=signup_data.email,
        first_name=signup_data.first_name,
        last_name=signup_data.last_name,
        access_token="mock-access-token",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    description="Mock login endpoint for E2E tests",
)
async def login(login_data: LoginRequest) -> AuthResponse:
    """Mock login endpoint for E2E tests."""
    return AuthResponse(
        user_id="mock-user-id",
        email=login_data.email,
        first_name="Mock",
        last_name="User",
        access_token="mock-access-token",
    )
