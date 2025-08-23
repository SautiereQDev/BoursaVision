"""
Modern Unified Mapper using Python 3.13
======================================

Eliminates duplication between Simple* and standard mappers
using Python 3.13 features and modern typing patterns.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from boursa_vision.application.dtos.portfolio import PortfolioCreateRequest, PortfolioResponse
from boursa_vision.application.dtos.user import UserCreateRequest, UserResponse
from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.entities.user import User as DomainUser

if TYPE_CHECKING:
    from boursa_vision.infrastructure.persistence.models.portfolio_model import PortfolioModel
    from boursa_vision.infrastructure.persistence.models.user_model import UserModel


# Generic type variables for mapping operations
TDomain = TypeVar('TDomain')
TModel = TypeVar('TModel')
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


# Python 3.13 type aliases using new 'type' keyword
type DomainEntity = DomainUser | DomainPortfolio
type PersistenceModel = UserModel | PortfolioModel
type RequestDTO = UserCreateRequest | PortfolioCreateRequest
type ResponseDTO = UserResponse | PortfolioResponse


class MapperProtocol(Protocol[TDomain, TModel, TRequest, TResponse]):
    """Protocol defining the mapping interface"""

    def to_domain(self, model: TModel) -> TDomain:
        """Convert persistence model to domain entity"""
        ...

    def to_model(self, domain: TDomain) -> TModel:
        """Convert domain entity to persistence model"""
        ...

    def from_create_request(self, request: TRequest) -> TDomain:
        """Convert create request DTO to domain entity"""
        ...

    def to_response(self, domain: TDomain) -> TResponse:
        """Convert domain entity to response DTO"""
        ...


class ModernUserMapper:
    """
    Modern unified user mapper with Python 3.13 optimizations
    Replaces both UserMapper and SimpleUserMapper
    """

    @staticmethod
    def to_domain(model: UserModel) -> DomainUser:
        """Convert UserModel to DomainUser using pattern matching"""
        return DomainUser(
            id=model.id,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash or "",  # Handle nullable field
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(domain: DomainUser) -> UserModel:
        """Convert DomainUser to UserModel"""
        from boursa_vision.infrastructure.persistence.models.user_model import UserModel

        return UserModel(
            id=domain.id,
            email=domain.email,
            username=domain.username,
            password_hash=domain.password_hash or None,  # Handle empty strings
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def from_create_request(request: UserCreateRequest) -> DomainUser:
        """Convert UserCreateRequest to DomainUser with Python 3.13 features"""
        from datetime import datetime
        from uuid import uuid4

        # Use pattern matching for request validation
        match request:
            case UserCreateRequest(email=email, username=username) if email and username:
                return DomainUser(
                    id=uuid4(),  # Generate new UUID instead of None
                    email=email,
                    username=username,
                    password_hash="",  # Will be set by authentication service
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            case _:
                raise ValueError("Invalid user creation request - missing email or username")

    @staticmethod
    def to_response(domain: DomainUser) -> UserResponse:
        """Convert DomainUser to UserResponse using dataclass optimization"""
        # Use asdict for efficient conversion with field filtering
        domain_dict = asdict(domain)
        
        # Remove sensitive/internal fields using pattern matching
        filtered_fields = {
            key: value 
            for key, value in domain_dict.items()
            if key not in {'password_hash'}  # Security: never expose password hash
        }
        
        return UserResponse(**filtered_fields)


class ModernPortfolioMapper:
    """
    Modern unified portfolio mapper with Python 3.13 optimizations
    Replaces both PortfolioMapper and SimplePortfolioMapper
    """

    @staticmethod
    def to_domain(model: PortfolioModel) -> DomainPortfolio:
        """Convert PortfolioModel to DomainPortfolio"""
        from decimal import Decimal
        from boursa_vision.domain.value_objects import Money, Currency
        
        # Convert database values to proper types
        base_currency_str = model.base_currency or "USD"
        base_currency = Currency(base_currency_str)
        cash_amount = Decimal(str(model.cash_balance or 0))
        
        return DomainPortfolio(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            base_currency=base_currency_str,  # Use string directly 
            cash_balance=Money(amount=cash_amount, currency=base_currency),
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(domain: DomainPortfolio) -> PortfolioModel:
        """Convert DomainPortfolio to PortfolioModel"""
        from boursa_vision.infrastructure.persistence.models.portfolio_model import PortfolioModel

        return PortfolioModel(
            id=domain.id,
            user_id=domain.user_id,
            name=domain.name,
            base_currency=domain.base_currency,
            cash_balance=float(domain.cash_balance.amount),  # Convert Decimal to float for DB
            created_at=domain.created_at,
        )

    @staticmethod
    def from_create_request(request: PortfolioCreateRequest) -> DomainPortfolio:
        """Convert PortfolioCreateRequest to DomainPortfolio with validation"""
        from datetime import datetime
        from decimal import Decimal
        from uuid import uuid4

        from boursa_vision.domain.value_objects import Currency, Money

        # Pattern matching for request validation
        match request:
            case PortfolioCreateRequest(user_id=user_id, name=name) if all([user_id, name]):
                base_currency_str = getattr(request, 'base_currency', 'USD') or 'USD'
                initial_balance_val = getattr(request, 'initial_balance', 0) or 0
                
                # Convert to proper types
                base_currency = Currency(base_currency_str)
                cash_amount = Decimal(str(initial_balance_val))
                
                return DomainPortfolio(
                    id=uuid4(),  # Generate new UUID
                    user_id=user_id,
                    name=name,
                    base_currency=base_currency_str,
                    cash_balance=Money(amount=cash_amount, currency=base_currency),
                    created_at=datetime.now(),
                )
            case _:
                raise ValueError("Invalid portfolio creation request - missing required fields")

    @staticmethod
    def to_response(domain: DomainPortfolio) -> PortfolioResponse:
        """Convert DomainPortfolio to PortfolioResponse"""
        # Create response dict from domain entity
        return PortfolioResponse(
            id=domain.id,
            user_id=domain.user_id,
            name=domain.name,
            base_currency=domain.base_currency,
            cash_balance=float(domain.cash_balance.amount),
            created_at=domain.created_at,
        )


# Unified mapper registry using Python 3.13 pattern matching
class MapperRegistry:
    """
    Registry for managing mappers with type-safe operations
    Uses Python 3.13 pattern matching for efficient dispatcher
    """

    @staticmethod
    def get_mapper(entity_type: type[DomainEntity]) -> Any:
        """
        Get appropriate mapper based on entity type
        Uses Python 3.13 enhanced pattern matching
        """
        match entity_type:
            case type() if issubclass(entity_type, DomainUser):
                return ModernUserMapper()
            case type() if issubclass(entity_type, DomainPortfolio):
                return ModernPortfolioMapper()
            case _:
                raise ValueError(f"No mapper registered for entity type: {entity_type}")

    @staticmethod
    def map_to_domain(model: PersistenceModel) -> DomainEntity:
        """Generic mapping to domain entity using pattern matching"""
        match model:
            case model if hasattr(model, 'email'):  # UserModel
                return ModernUserMapper.to_domain(model)
            case model if hasattr(model, 'currency'):  # PortfolioModel
                return ModernPortfolioMapper.to_domain(model)
            case _:
                raise ValueError(f"Unknown model type for domain mapping: {type(model)}")

    @staticmethod
    def map_to_response(domain: DomainEntity) -> ResponseDTO:
        """Generic mapping to response DTO using pattern matching"""
        match domain:
            case DomainUser():
                return ModernUserMapper.to_response(domain)
            case DomainPortfolio():
                return ModernPortfolioMapper.to_response(domain)
            case _:
                raise ValueError(f"Unknown domain type for response mapping: {type(domain)}")


# Example usage with Python 3.13 features
def example_mapper_usage():
    """Demonstrate modern mapper usage patterns"""
    from datetime import datetime
    from decimal import Decimal
    from uuid import uuid4

    from boursa_vision.domain.value_objects import Currency, Money

    # Create domain entities for demonstration
    user = DomainUser(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    portfolio = DomainPortfolio(
        id=uuid4(),
        user_id=uuid4(),
        name="My Portfolio",
        base_currency="USD",
        cash_balance=Money(amount=Decimal("1000.00"), currency=Currency.USD),
        created_at=datetime.now(),
    )

    # Registry-based mapping using pattern matching
    registry = MapperRegistry()

    # Map to responses
    user_response = registry.map_to_response(user)
    portfolio_response = registry.map_to_response(portfolio)

    # Demonstrate type safety
    _ = user_response
    _ = portfolio_response


# Migration helper for existing code
class LegacyMapperBridge:
    """
    Bridge to maintain compatibility with existing Simple* mapper usage
    Delegates to modern unified mappers
    """

    @staticmethod
    def get_simple_user_mapper():
        """Return modern user mapper for SimpleUserMapper compatibility"""
        return ModernUserMapper()

    @staticmethod
    def get_simple_portfolio_mapper():
        """Return modern portfolio mapper for SimplePortfolioMapper compatibility"""
        return ModernPortfolioMapper()

    @staticmethod
    def get_user_mapper():
        """Return modern user mapper for UserMapper compatibility"""
        return ModernUserMapper()

    @staticmethod
    def get_portfolio_mapper():
        """Return modern portfolio mapper for PortfolioMapper compatibility"""
        return ModernPortfolioMapper()


# Export aliases for easy migration
SimpleUserMapper = ModernUserMapper
SimplePortfolioMapper = ModernPortfolioMapper
UserMapper = ModernUserMapper
PortfolioMapper = ModernPortfolioMapper
