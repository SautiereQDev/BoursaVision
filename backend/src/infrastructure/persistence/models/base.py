
"""
Base SQLAlchemy models for the trading platform.
Compatible with Clean Architecture + FastAPI.
"""
# ================================================================
# TRADING PLATFORM - BASE SQLALCHEMY
# Compatible with Clean Architecture + FastAPI
# ================================================================

from sqlalchemy.orm import declarative_base

# ================================================================
# DECLARATIVE BASE
# ================================================================

Base = declarative_base()


# ================================================================
# MIXIN FOR COMMON FUNCTIONALITIES
# ================================================================


class DatabaseMixin:
    """
    Mixin for common model functionalities

    Provides methods for creating, converting to dict, and updating models.
    Can be used with SQLAlchemy models to add these functionalities.

    Functions :

    create(**kwargs) -> 'DatabaseMixin':
        Factory method to create a new instance.

    to_dict() -> dict:
        Converts the model instance to a dictionary.

    update(**kwargs) -> None:
        Updates the model instance with new values.
    """

    @classmethod
    def create(cls, **kwargs):
        """Factory method to create an instance"""
        return cls(**kwargs)

    def to_dict(self):
        """Converts the object to a dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        """Updates the object's attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
