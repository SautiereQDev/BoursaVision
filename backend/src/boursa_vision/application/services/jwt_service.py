"""
JWT Service - Application Layer
===============================

Service for JWT token generation, validation, and management.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from ...domain.entities.user import UserRole
from ...domain.value_objects.auth import AccessToken, RefreshToken, TokenPair


class JWTService:
    """Service for JWT token operations"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 30,
    ):
        """
        Initialize JWT service.
        
        Args:
            secret_key: Secret key for token signing
            algorithm: JWT algorithm to use
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        if not secret_key:
            raise ValueError("Secret key cannot be empty")
    
    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        permissions: List[str],
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> AccessToken:
        """
        Create a new access token.
        
        Args:
            user_id: User identifier
            email: User email
            role: User role
            permissions: User permissions
            extra_claims: Additional claims to include
            expires_delta: Optional custom expiration duration
            
        Returns:
            AccessToken value object
        """
        # Validate required parameters
        if not user_id:
            raise ValueError("User ID is required")
        if not email:
            raise ValueError("Email is required")
        if not role:
            raise ValueError("Role is required")
        
        now = datetime.now(timezone.utc)
        if expires_delta:
            expires_at = now + expires_delta
        else:
            expires_at = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "role": role,  # UserRole is a string enum, no need for .value
            "permissions": permissions,
            "token_type": "access",
            "iat": now,  # Issued at
            "exp": expires_at,  # Expiration time
            "jti": secrets.token_urlsafe(16),  # JWT ID for tracking
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return AccessToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            issued_at=now,
        )
    
    def create_refresh_token(self, user_id: UUID) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            RefreshToken value object
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.refresh_token_expire_days)
        
        # Refresh tokens are longer and more random
        token = secrets.token_urlsafe(64)
        
        return RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            created_at=now,
        )
    
    def create_token_pair(
        self,
        user_id: UUID,
        email: str,
        role: UserRole,
        permissions: List[str],
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> TokenPair:
        """
        Create a pair of access and refresh tokens.
        
        Args:
            user_id: User identifier
            email: User email
            role: User role
            permissions: User permissions
            extra_claims: Additional claims for access token
            
        Returns:
            TokenPair value object
        """
        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            permissions=permissions,
            extra_claims=extra_claims,
        )
        
        refresh_token = self.create_refresh_token(user_id=user_id)
        
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode an access token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("token_type") != "access":
                return None
            
            # Check expiration is handled by jwt.decode automatically
            return payload
        
        except InvalidTokenError:
            return None
    
    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """
        Decode an access token (throws exception if invalid).
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload
            
        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("token_type") != "access":
                raise ValueError("Invalid token type")
            
            return payload
        
        except InvalidTokenError as e:
            raise ValueError("Invalid token") from e
    
    def validate_access_token(self, token: str) -> bool:
        """
        Validate an access token (returns boolean).
        
        Args:
            token: JWT token string
            
        Returns:
            True if valid, False otherwise
        """
        return self.verify_access_token(token) is not None
