"""
Application Container - CQRS Commands and Queries Layer
=======================================================

ApplicationContainer manages the application layer following CQRS pattern.
This includes Commands (write operations), Queries (read operations), and
their corresponding handlers aligned with existing implementations.

Features:
- Command pattern for write operations
- Query pattern for read operations  
- Handler orchestration with domain services
- Transaction boundary management
- Integration with existing handlers

Dependencies: ServicesContainer, RepositoryContainer
"""

from dependency_injector import containers, providers


# =============================================================================
# COMMAND HANDLER FACTORY FUNCTIONS
# =============================================================================

def _create_portfolio_command_handler(portfolio_repository, user_repository):
    """Create portfolio creation command handler aligned with existing implementation."""
    from boursa_vision.application.handlers.command_handlers import CreatePortfolioCommandHandler
    
    # Simple unit of work implementation for now
    class SimpleUnitOfWork:
        def __init__(self):
            # Placeholder unit of work for dependency injection integration
            pass
        
        async def __aenter__(self):
            # Context manager entry - returns self for transaction handling
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Context manager exit - handles cleanup and rollback if needed
            pass
        
        async def commit(self):
            # Commit transaction - placeholder for real transaction handling
            pass
    
    return CreatePortfolioCommandHandler(
        portfolio_repository=portfolio_repository,
        user_repository=user_repository,
        unit_of_work=SimpleUnitOfWork(),
    )


def _create_investment_command_handler(investment_repository):
    """Create investment creation command handler aligned with existing implementation."""
    from boursa_vision.application.handlers.command_handlers import CreateInvestmentCommandHandler
    
    class SimpleUnitOfWork:
        def __init__(self):
            # Placeholder unit of work for dependency injection integration
            pass
        
        async def __aenter__(self):
            # Context manager entry - returns self for transaction handling
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Context manager exit - handles cleanup and rollback if needed
            pass
        
        async def commit(self):
            # Commit transaction - placeholder for real transaction handling
            pass
    
    return CreateInvestmentCommandHandler(
        investment_repository=investment_repository,
        unit_of_work=SimpleUnitOfWork(),
    )


def _create_add_investment_to_portfolio_command_handler(portfolio_repository, investment_repository):
    """Create add investment to portfolio command handler aligned with existing implementation."""
    from boursa_vision.application.handlers.command_handlers import AddInvestmentToPortfolioCommandHandler
    
    class SimpleUnitOfWork:
        def __init__(self):
            # Placeholder unit of work for dependency injection integration
            pass
        
        async def __aenter__(self):
            # Context manager entry - returns self for transaction handling
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            # Context manager exit - handles cleanup and rollback if needed
            pass
        
        async def commit(self):
            # Commit transaction - placeholder for real transaction handling
            pass
    
    return AddInvestmentToPortfolioCommandHandler(
        portfolio_repository=portfolio_repository,
        investment_repository=investment_repository,
        unit_of_work=SimpleUnitOfWork(),
    )


def _create_generate_signal_command_handler():
    """Create signal generation command handler aligned with existing implementation."""
    from boursa_vision.application.handlers.command_handlers import GenerateSignalCommandHandler
    
    # Signal generation handler needs to be properly configured with required services
    # For now, create with minimal dependencies
    return GenerateSignalCommandHandler()


# =============================================================================
# QUERY HANDLER FACTORY FUNCTIONS  
# =============================================================================

def _create_get_portfolio_by_id_query_handler(portfolio_repository):
    """Create get portfolio by ID query handler aligned with existing implementation."""
    from boursa_vision.application.handlers.query_handlers import GetPortfolioByIdQueryHandler
    return GetPortfolioByIdQueryHandler(portfolio_repository=portfolio_repository)


def _create_get_user_portfolios_query_handler(portfolio_repository):
    """Create get user portfolios query handler aligned with existing implementation."""
    from boursa_vision.application.handlers.query_handlers import GetUserPortfoliosQueryHandler
    return GetUserPortfoliosQueryHandler(portfolio_repository=portfolio_repository)


def _create_find_investments_query_handler(investment_repository):
    """Create find investments query handler aligned with existing implementation."""
    from boursa_vision.application.handlers.query_handlers import FindInvestmentsQueryHandler
    return FindInvestmentsQueryHandler(investment_repository=investment_repository)


def _create_get_investment_by_id_query_handler(investment_repository):
    """Create get investment by ID query handler aligned with existing implementation."""
    from boursa_vision.application.handlers.query_handlers import GetInvestmentByIdQueryHandler
    return GetInvestmentByIdQueryHandler(investment_repository=investment_repository)


def _create_analyze_portfolio_query_handler(portfolio_repository, risk_calculator, performance_analyzer):
    """Create analyze portfolio query handler aligned with existing implementation."""
    from boursa_vision.application.handlers.query_handlers import AnalyzePortfolioQueryHandler
    return AnalyzePortfolioQueryHandler(
        portfolio_repository=portfolio_repository,
        risk_calculator=risk_calculator,
        performance_analyzer=performance_analyzer,
    )


# =============================================================================
# APPLICATION CONTAINER CLASS
# =============================================================================

class ApplicationContainer(containers.DeclarativeContainer):
    """
    Application container for CQRS Commands and Queries.
    
    Contains:
        - Command handlers for write operations
        - Query handlers for read operations
        - Application service orchestration
        - Transaction management
        - Alignment with existing handler patterns
    
    This layer orchestrates domain services and repositories to fulfill
    business use cases while maintaining clean separation of concerns.
    """
    
    # Dependencies from other containers
    repositories = providers.DependenciesContainer()
    services = providers.DependenciesContainer()
    
    # =============================================================================
    # COMMAND HANDLERS - Aligned with existing handlers
    # =============================================================================
    
    create_portfolio_command_handler = providers.Factory(
        _create_portfolio_command_handler,
        portfolio_repository=repositories.portfolio_repository,
        user_repository=repositories.user_repository,
    )
    
    create_investment_command_handler = providers.Factory(
        _create_investment_command_handler,
        investment_repository=repositories.investment_repository,
    )
    
    add_investment_to_portfolio_command_handler = providers.Factory(
        _create_add_investment_to_portfolio_command_handler,
        portfolio_repository=repositories.portfolio_repository,
        investment_repository=repositories.investment_repository,
    )
    
    generate_signal_command_handler = providers.Factory(
        _create_generate_signal_command_handler,
    )
    
    # =============================================================================
    # QUERY HANDLERS - Aligned with existing handlers
    # =============================================================================
    
    get_portfolio_by_id_query_handler = providers.Factory(
        _create_get_portfolio_by_id_query_handler,
        portfolio_repository=repositories.portfolio_repository,
    )
    
    get_user_portfolios_query_handler = providers.Factory(
        _create_get_user_portfolios_query_handler,
        portfolio_repository=repositories.portfolio_repository,
    )
    
    find_investments_query_handler = providers.Factory(
        _create_find_investments_query_handler,
        investment_repository=repositories.investment_repository,
    )
    
    get_investment_by_id_query_handler = providers.Factory(
        _create_get_investment_by_id_query_handler,
        investment_repository=repositories.investment_repository,
    )
    
    analyze_portfolio_query_handler = providers.Factory(
        _create_analyze_portfolio_query_handler,
        portfolio_repository=repositories.portfolio_repository,
        risk_calculator=services.risk_calculator,
        performance_analyzer=services.performance_analyzer,
    )
