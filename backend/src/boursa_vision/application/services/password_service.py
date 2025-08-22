"""
Password Service - Application Layer
====================================

Service for password hashing and verification using bcrypt.
"""

import re
from passlib.context import CryptContext
from passlib.exc import InvalidTokenError, UnknownHashError


class PasswordService:
    """Service for password operations using bcrypt"""
    
    def __init__(self):
        """Initialize password context with bcrypt"""
        self._pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12,  # Strong security level
        )
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Raises:
            ValueError: If password is empty or invalid
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        return self._pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password
            
        Returns:
            True if password is correct, False otherwise
        """
        if not password or not hashed_password:
            return False
        
        try:
            return self._pwd_context.verify(password, hashed_password)
        except (InvalidTokenError, UnknownHashError):
            return False
    
    def needs_update(self, hashed_password: str) -> bool:
        """
        Check if a hashed password needs to be updated.
        
        This can happen when the hashing algorithm is upgraded
        or security parameters change.
        
        Args:
            hashed_password: Previously hashed password
            
        Returns:
            True if password needs rehashing
        """
        if not hashed_password:
            return True
        
        try:
            return self._pwd_context.needs_update(hashed_password)
        except (InvalidTokenError, UnknownHashError):
            return True

    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets all requirements, False otherwise
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not re.search(r'\d', password):
            raise ValueError("Password must contain at least one number")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            raise ValueError("Password must contain at least one special character")
            
        return True

    def generate_random_password(self, length: int = 12) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Length of password to generate (minimum 8)
            
        Returns:
            Randomly generated password string
        """
        import secrets
        import string
        
        if length < 8:
            length = 8
            
        # Ensure we have at least one of each required character type
        chars = []
        chars.append(secrets.choice(string.ascii_uppercase))  # Uppercase
        chars.append(secrets.choice(string.ascii_lowercase))  # Lowercase
        chars.append(secrets.choice(string.digits))          # Digit
        chars.append(secrets.choice('!@#$%^&*()_+-=[]{}|;:,.<>?'))  # Special
        
        # Fill the rest with random characters from all categories
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?'
        for _ in range(length - 4):
            chars.append(secrets.choice(all_chars))
        
        # Shuffle the characters to avoid predictable patterns
        secrets.SystemRandom().shuffle(chars)
        
        return ''.join(chars)
