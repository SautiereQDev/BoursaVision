"""
Dependency Injection Containers Package
========================================

This package contains all dependency injection containers for the BoursaVision
application, implementing a modular architecture with proper separation of
concerns using the dependency-injector framework.

Architecture Overview:
- CoreContainer: Configuration, logging, and core services
- DatabaseContainer: Database connections and session management
- RepositoryContainer: Repository implementations with data access
- ServicesContainer: Domain services and business logic
- ApplicationContainer: CQRS commands and queries
- InfrastructureContainer: External services and integrations
- WebContainer: FastAPI web layer and HTTP concerns
- MainContainer: Root container orchestrating all other containers

Container Hierarchy:
    CoreContainer (foundation)
         ↓
    DatabaseContainer (data layer)
         ↓
    RepositoryContainer (data access)
         ↓
    ServicesContainer (domain logic)
         ↓
    ApplicationContainer (use cases)
         ↓
    InfrastructureContainer (external services)
         ↓
    WebContainer (presentation layer)
         ↓
    MainContainer (composition root)

Each container is responsible for a specific domain of dependencies,
ensuring clean separation and easy testing/mocking capabilities.
"""

from .application import ApplicationContainer
from .core import CoreContainer
from .database import DatabaseContainer
from .infrastructure import InfrastructureContainer
from .main_simple import ContainerManager, MainContainer
from .repositories import RepositoryContainer
from .services import ServicesContainer
from .web_simple import WebContainer

__all__ = [
    "ApplicationContainer",
    "ContainerManager",
    "CoreContainer",
    "DatabaseContainer",
    "InfrastructureContainer",
    "MainContainer",
    "RepositoryContainer",
    "ServicesContainer",
    "WebContainer",
]
