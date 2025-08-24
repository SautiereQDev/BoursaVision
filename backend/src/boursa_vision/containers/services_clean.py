"""
Services Container - Domain Business Logic Services (Clean)
==========================================================

ServicesContainer manages pure domain services that encapsulate business
logic without external dependencies. This aligns with existing domain
services in the codebase following Clean Architecture principles.

Features:
- Risk calculation and portfolio analysis
- Performance metrics and analytics
- Business validation services  
- Pure domain logic (no infrastructure dependencies)
- Integration with existing domain services

Dependencies: RepositoryContainer (minimal, for data when needed)
"""

from dependency_injector import containers, providers


# =============================================================================
# DOMAIN SERVICE FACTORY FUNCTIONS
# =============================================================================

def _create_risk_calculator_service():
    """Create risk calculator service aligned with existing domain service."""
    from boursa_vision.domain.services.risk_calculator_service import RiskCalculatorService
    return RiskCalculatorService()


def _create_performance_analyzer_service(risk_calculator):
    """Create performance analyzer service aligned with existing domain service."""  
    from boursa_vision.domain.services.performance_analyzer_service import PerformanceAnalyzerService
    return PerformanceAnalyzerService()


# =============================================================================
# SERVICES CONTAINER CLASS
# =============================================================================

class ServicesContainer(containers.DeclarativeContainer):
    """
    Services container for pure domain business logic.
    
    Contains:
        - Risk calculation and assessment services
        - Performance analysis and metrics
        - Business rule validation services
        - Domain service orchestration
    
    All services in this container are pure domain services that encapsulate
    business logic following the existing codebase patterns.
    """
    
    # Dependencies from RepositoryContainer (when data access is needed)
    repositories = providers.DependenciesContainer()
    
    # =============================================================================
    # CORE DOMAIN SERVICES - Pure business logic
    # =============================================================================
    
    risk_calculator = providers.Factory(
        _create_risk_calculator_service,
    )
    
    performance_analyzer = providers.Factory(
        _create_performance_analyzer_service,
        risk_calculator=risk_calculator,
    )
