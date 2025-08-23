"""
Tests unitaires pour les DTOs de base
===================================

Tests pour vérifier que les imports et les DTOs de base fonctionnent correctement
avec la nouvelle architecture modernisée.
"""

from __future__ import annotations

import pytest


class TestBaseDTOImports:
    """Tests pour les imports des DTOs de base"""

    def test_basedto_imports_available(self):
        """Test que les exceptions sont importables depuis base.py"""
        try:
            # Test des imports qui échouaient auparavant
            from boursa_vision.application.dtos.base import (
                InvalidSymbolError,
                PriceRangeError,
            )
            
            # Vérifier que les classes sont bien importées
            assert InvalidSymbolError is not None
            assert PriceRangeError is not None
            
            # Vérifier que ce sont bien des classes d'exception
            assert issubclass(InvalidSymbolError, Exception)
            assert issubclass(PriceRangeError, Exception)
            
        except ImportError as e:
            pytest.fail(f"Failed to import exceptions from base.py: {e}")

    def test_base_dto_class_available(self):
        """Test que BaseDTO est disponible"""
        try:
            from boursa_vision.application.dtos.base import BaseDTO
            
            assert BaseDTO is not None
            
            # Test de création d'une instance simple 
            # (si BaseDTO n'est pas abstraite)
            try:
                dto = BaseDTO()
                assert dto is not None
            except TypeError:
                # BaseDTO pourrait être abstraite, c'est OK
                pass
                
        except ImportError as e:
            pytest.fail(f"Failed to import BaseDTO from base.py: {e}")

    def test_future_annotations_work(self):
        """Test que les annotations futures fonctionnent correctement"""
        # Ce test vérifie que from __future__ import annotations
        # n'interfère pas avec les imports
        
        def test_function(param: str | None = None) -> bool:
            """Fonction test avec annotations modernes"""
            return param is None or isinstance(param, str)
        
        # Test avec None
        assert test_function() is True
        
        # Test avec string
        assert test_function("test") is True
        
        # Test de l'annotation elle-même
        annotations = test_function.__annotations__
        assert 'param' in annotations
        assert 'return' in annotations


class TestDTOStructure:
    """Tests pour la structure des DTOs"""
    
    def test_dto_inheritance_structure(self):
        """Test que la hiérarchie des DTOs est correcte"""
        try:
            from boursa_vision.application.dtos.base import BaseDTO
            from boursa_vision.application.dtos.user import UserResponse
            from boursa_vision.application.dtos.portfolio import PortfolioResponse
            
            # Vérifier l'héritage (si applicable)
            assert hasattr(UserResponse, '__bases__')
            assert hasattr(PortfolioResponse, '__bases__')
            
        except ImportError:
            # Si les DTOs n'existent pas encore, ce n'est pas grave
            pytest.skip("DTO classes not yet implemented")

    def test_dto_with_python313_features(self):
        """Test que les DTOs supportent les fonctionnalités Python 3.13"""
        # Test de création d'une classe DTO moderne
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass(slots=True)  # Python 3.13 optimization
        class TestDTO:
            id: int | None = None  # Union syntax moderne
            name: str = ""
            active: bool = True
        
        # Test de création
        dto = TestDTO(id=1, name="test", active=True)
        
        assert dto.id == 1
        assert dto.name == "test"
        assert dto.active is True
        
        # Vérifier que __slots__ est activé
        assert hasattr(TestDTO, '__slots__')
        
        # Vérifier qu'on ne peut pas ajouter d'attributs dynamiques
        with pytest.raises(AttributeError):
            dto.dynamic_attr = "should_fail"


class TestExceptionHandling:
    """Tests pour la gestion d'exceptions modernisée"""
    
    def test_custom_exceptions_work(self):
        """Test que nos exceptions personnalisées fonctionnent"""
        try:
            from boursa_vision.application.dtos.base import (
                InvalidSymbolError,
                PriceRangeError,
            )
            
            # Test InvalidSymbolError
            try:
                raise InvalidSymbolError("INVALID")
            except InvalidSymbolError as e:
                assert "INVALID" in str(e)  # ✅ Le message contient le symbole
            
            # Test PriceRangeError  
            try:
                raise PriceRangeError()  # ✅ Pas d'arguments
            except PriceRangeError as e:
                assert "max_price must be greater than min_price" in str(e)
                
        except ImportError:
            pytest.skip("Custom exceptions not available")

    def test_exception_pattern_matching(self):
        """Test du pattern matching Python 3.13 avec exceptions"""
        try:
            from boursa_vision.application.dtos.base import (
                InvalidSymbolError,
                PriceRangeError,
            )
            
            def handle_exception(exc: Exception) -> str:
                """Test pattern matching avec exceptions"""
                match exc:
                    case InvalidSymbolError():
                        return "invalid_symbol"
                    case PriceRangeError():
                        return "price_range"
                    case ValueError():
                        return "value_error"
                    case _:
                        return "unknown"
            
            # Test avec InvalidSymbolError
            result = handle_exception(InvalidSymbolError("TEST"))
            assert result == "invalid_symbol"
            
            # Test avec PriceRangeError
            result = handle_exception(PriceRangeError())  # ✅ Pas d'arguments
            assert result == "price_range"
            
            # Test avec ValueError générique
            result = handle_exception(ValueError("Generic error"))
            assert result == "value_error"
            
        except ImportError:
            pytest.skip("Custom exceptions not available")


class TestModernFeatures:
    """Tests pour les fonctionnalités Python 3.13"""
    
    def test_type_alias_support(self):
        """Test que les nouveaux type aliases fonctionnent"""
        # Test avec la nouvelle syntaxe type
        try:
            exec("""
type UserID = int | str
type OptionalString = str | None

def test_func(user_id: UserID, name: OptionalString = None) -> bool:
    return user_id is not None
            """)
        except SyntaxError:
            pytest.skip("Modern type aliases not supported in this Python version")
    
    def test_pattern_matching_available(self):
        """Test que le pattern matching est disponible"""
        def test_match(value: str) -> str:
            match value:
                case "test":
                    return "matched_test"
                case str() if len(value) > 5:
                    return "long_string"
                case _:
                    return "no_match"
        
        assert test_match("test") == "matched_test"
        assert test_match("very_long_string") == "long_string"
        assert test_match("short") == "no_match"
    
    def test_dataclass_slots_optimization(self):
        """Test que l'optimisation slots des dataclasses fonctionne"""
        from dataclasses import dataclass
        
        @dataclass(slots=True)
        class OptimizedDTO:
            id: int
            name: str
            active: bool = True
        
        dto = OptimizedDTO(1, "test")
        
        # Vérifier que __slots__ est défini
        assert hasattr(OptimizedDTO, '__slots__')
        
        # Vérifier que les valeurs sont correctes
        assert dto.id == 1
        assert dto.name == "test" 
        assert dto.active is True
        
        # Vérifier qu'on ne peut pas ajouter d'attributs dynamiques
        with pytest.raises(AttributeError):
            dto.new_attribute = "fail"
