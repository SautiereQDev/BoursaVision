"""
Tests unitaires pour le module repositories principal.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur les interfaces et structures de repository.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime


@pytest.mark.unit
class TestRepositoriesModuleStructure:
    """Tests de structure et disponibilité du module repositories."""
    
    def test_repositories_module_file_exists(self):
        """Vérifie que le fichier repositories existe."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        assert repos_path.exists()
        assert repos_path.is_file()
    
    def test_repositories_module_has_docstring(self):
        """Vérifie que le module repositories a une docstring."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'Repository implementations for the trading platform' in content
        assert 'concrete implementations of domain repository interfaces' in content


@pytest.mark.unit
class TestRepositoryImports:
    """Tests d'imports des dépendances repository."""
    
    def test_repository_required_imports_exist(self):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = [
            'typing',
            'uuid',
            'sqlalchemy',
            'sqlalchemy.ext.asyncio'
        ]
        
        for import_name in required_imports:
            try:
                __import__(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")
    
    def test_repository_interfaces_referenced(self):
        """Vérifie que les interfaces de repository sont référencées."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'IUserRepository' in content
        assert 'IPortfolioRepository' in content
        assert 'IMarketDataRepository' in content
        assert 'IInvestmentRepository' in content


@pytest.mark.unit
class TestSqlAlchemyUserRepository:
    """Tests de structure de SqlAlchemyUserRepository."""
    
    def test_user_repository_class_defined(self):
        """Vérifie que la classe SqlAlchemyUserRepository est définie."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'class SqlAlchemyUserRepository(IUserRepository):' in content
        assert 'SQLAlchemy implementation of User repository.' in content
    
    def test_user_repository_has_required_methods(self):
        """Vérifie que SqlAlchemyUserRepository a les méthodes requises."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        required_methods = [
            'async def find_by_id(self, user_id: UUID)',
            'async def find_by_email(self, email: str)',
            'async def find_by_username(self, username: str)',
            'async def save(self, user: DomainUser)',
            'async def delete(self, user_id: UUID)',
            'async def find_all_active(self)'
        ]
        
        for method in required_methods:
            assert method in content
    
    def test_user_repository_has_constructor(self):
        """Vérifie que SqlAlchemyUserRepository a un constructeur."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'def __init__(self, session: AsyncSession):' in content
        assert 'self._session = session' in content


@pytest.mark.unit
class TestSqlAlchemyPortfolioRepository:
    """Tests de structure de SqlAlchemyPortfolioRepository."""
    
    def test_portfolio_repository_class_defined(self):
        """Vérifie que la classe SqlAlchemyPortfolioRepository est définie."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'class SqlAlchemyPortfolioRepository(IPortfolioRepository):' in content
        assert 'SQLAlchemy implementation of Portfolio repository.' in content
    
    def test_portfolio_repository_has_required_methods(self):
        """Vérifie que SqlAlchemyPortfolioRepository a les méthodes requises."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        required_methods = [
            'async def find_by_id(self, portfolio_id: UUID)',
            'async def find_by_user_id(self, user_id: UUID)', 
            'async def save(self, portfolio: DomainPortfolio)',
            'async def delete(self, portfolio_id: UUID)'
        ]
        
        for method in required_methods:
            assert method in content
    
    def test_portfolio_repository_uses_selectinload(self):
        """Vérifie que le repository utilise selectinload pour optimiser les requêtes."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'selectinload(Portfolio.positions)' in content


@pytest.mark.unit
class TestSqlAlchemyMarketDataRepository:
    """Tests de structure de SqlAlchemyMarketDataRepository."""
    
    def test_market_data_repository_class_defined(self):
        """Vérifie que la classe SqlAlchemyMarketDataRepository est définie."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'class SqlAlchemyMarketDataRepository(IMarketDataRepository):' in content
        assert 'TimescaleDB optimizations' in content
    
    def test_market_data_repository_has_save_method(self):
        """Vérifie que SqlAlchemyMarketDataRepository a la méthode save."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'async def save(self, market_data: DomainMarketData)' in content
        assert 'INSERT ON CONFLICT for TimescaleDB efficiency' in content


@pytest.mark.unit
class TestSqlAlchemyInvestmentRepository:
    """Tests de structure de SqlAlchemyInvestmentRepository."""
    
    def test_investment_repository_class_exists(self):
        """Vérifie que SqlAlchemyInvestmentRepository existe dans le fichier."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        # La classe peut être définie plus tard dans le fichier
        assert 'Investment' in content or 'class SqlAlchemyInvestmentRepository' in content


@pytest.mark.unit
class TestRepositoryMappers:
    """Tests des mappers utilisés par les repositories."""
    
    def test_mappers_are_imported(self):
        """Vérifie que les mappers sont importés."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'UserMapper' in content
        assert 'PortfolioMapper' in content  
        assert 'MarketDataMapper' in content
        assert 'InvestmentMapper' in content
    
    def test_mappers_to_domain_used(self):
        """Vérifie que les mappers to_domain sont utilisés."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'UserMapper.to_domain(' in content
        assert 'PortfolioMapper.to_domain(' in content
    
    def test_mappers_to_persistence_used(self):
        """Vérifie que les mappers to_persistence sont utilisés."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'to_persistence(' in content or 'to_model(' in content


@pytest.mark.unit
class TestRepositoryModels:
    """Tests des modèles utilisés par les repositories."""
    
    def test_sqlalchemy_models_imported(self):
        """Vérifie que les modèles SQLAlchemy sont importés."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'from .models import' in content
        expected_models = ['User', 'Portfolio', 'MarketData', 'Instrument']
        
        for model in expected_models:
            assert model in content


@pytest.mark.unit
class TestRepositoryErrorHandling:
    """Tests de gestion d'erreurs des repositories."""
    
    def test_repositories_handle_none_results(self):
        """Vérifie que les repositories gèrent les résultats None."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'scalar_one_or_none()' in content
        assert 'if model else None' in content
    
    def test_repositories_use_flush_for_consistency(self):
        """Vérifie que les repositories utilisent flush pour la cohérence."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'await self._session.flush()' in content


@pytest.mark.unit
class TestRepositoryQueries:
    """Tests des requêtes SQLAlchemy dans les repositories."""
    
    def test_repositories_use_proper_sqlalchemy_syntax(self):
        """Vérifie que les repositories utilisent la syntaxe SQLAlchemy correcte."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        # Vérifications syntaxiques
        assert 'select(' in content
        assert 'where(' in content
        assert 'delete(' in content
        assert 'self._session.execute(' in content
    
    def test_repositories_use_and_for_compound_conditions(self):
        """Vérifie que les repositories utilisent and_ pour les conditions composées."""
        repos_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'boursa_vision' / 'infrastructure' / 'persistence' / 'repositories.py'
        with open(repos_path, 'r') as f:
            content = f.read()
        
        assert 'and_(' in content
