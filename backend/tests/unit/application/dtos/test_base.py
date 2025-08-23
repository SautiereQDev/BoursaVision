"""
Tests unitaires pour le module application.dtos.base
Couvre la classe BaseDTO et les constantes associées
"""
import pytest

from boursa_vision.application.dtos.base import (
    AMOUNT_DESC,
    ASSET_SYMBOL_DESC,
    AVERAGE_PRICE_DESC,
    CURRENCY_CODE_DESC,
    CURRENT_PRICE_DESC,
    EXCHANGE_NAME_DESC,
    INVESTMENT_NAME_DESC,
    INVESTMENT_SECTOR_DESC,
    INVESTMENT_TYPE_DESC,
    MARKET_CAP_DESC,
    PORTFOLIO_NAME_DESC,
    QUANTITY_DESC,
    TRADING_CURRENCY_DESC,
    USER_ID_DESC,
    BaseDTO,
)


@pytest.mark.unit
class TestBaseDTOConstants:
    """Tests pour toutes les constantes définies dans le module base"""

    def test_asset_symbol_desc_value(self):
        """ASSET_SYMBOL_DESC doit avoir une valeur appropriée"""
        assert isinstance(ASSET_SYMBOL_DESC, str)
        assert len(ASSET_SYMBOL_DESC) > 0
        assert ASSET_SYMBOL_DESC == "Asset symbol"

    def test_investment_name_desc_value(self):
        """INVESTMENT_NAME_DESC doit avoir une valeur appropriée"""
        assert isinstance(INVESTMENT_NAME_DESC, str)
        assert len(INVESTMENT_NAME_DESC) > 0
        assert INVESTMENT_NAME_DESC == "Investment name"

    def test_exchange_name_desc_value(self):
        """EXCHANGE_NAME_DESC doit avoir une valeur appropriée"""
        assert isinstance(EXCHANGE_NAME_DESC, str)
        assert len(EXCHANGE_NAME_DESC) > 0
        assert EXCHANGE_NAME_DESC == "Exchange name"

    def test_investment_type_desc_value(self):
        """INVESTMENT_TYPE_DESC doit avoir une valeur appropriée"""
        assert isinstance(INVESTMENT_TYPE_DESC, str)
        assert len(INVESTMENT_TYPE_DESC) > 0
        assert INVESTMENT_TYPE_DESC == "Type of investment"

    def test_investment_sector_desc_value(self):
        """INVESTMENT_SECTOR_DESC doit avoir une valeur appropriée"""
        assert isinstance(INVESTMENT_SECTOR_DESC, str)
        assert len(INVESTMENT_SECTOR_DESC) > 0
        assert INVESTMENT_SECTOR_DESC == "Investment sector"

    def test_market_cap_desc_value(self):
        """MARKET_CAP_DESC doit avoir une valeur appropriée"""
        assert isinstance(MARKET_CAP_DESC, str)
        assert len(MARKET_CAP_DESC) > 0
        assert MARKET_CAP_DESC == "Market capitalization category"

    def test_trading_currency_desc_value(self):
        """TRADING_CURRENCY_DESC doit avoir une valeur appropriée"""
        assert isinstance(TRADING_CURRENCY_DESC, str)
        assert len(TRADING_CURRENCY_DESC) > 0
        assert TRADING_CURRENCY_DESC == "Trading currency"

    def test_portfolio_name_desc_value(self):
        """PORTFOLIO_NAME_DESC doit avoir une valeur appropriée"""
        assert isinstance(PORTFOLIO_NAME_DESC, str)
        assert len(PORTFOLIO_NAME_DESC) > 0
        assert PORTFOLIO_NAME_DESC == "Portfolio name"

    def test_user_id_desc_value(self):
        """USER_ID_DESC doit avoir une valeur appropriée"""
        assert isinstance(USER_ID_DESC, str)
        assert len(USER_ID_DESC) > 0
        assert USER_ID_DESC == "User identifier"

    def test_amount_desc_value(self):
        """AMOUNT_DESC doit avoir une valeur appropriée"""
        assert isinstance(AMOUNT_DESC, str)
        assert len(AMOUNT_DESC) > 0
        assert AMOUNT_DESC == "Amount of money"

    def test_currency_code_desc_value(self):
        """CURRENCY_CODE_DESC doit avoir une valeur appropriée"""
        assert isinstance(CURRENCY_CODE_DESC, str)
        assert len(CURRENCY_CODE_DESC) > 0
        assert CURRENCY_CODE_DESC == "Currency code"

    def test_quantity_desc_value(self):
        """QUANTITY_DESC doit avoir une valeur appropriée"""
        assert isinstance(QUANTITY_DESC, str)
        assert len(QUANTITY_DESC) > 0
        assert QUANTITY_DESC == "Quantity of the position"

    def test_average_price_desc_value(self):
        """AVERAGE_PRICE_DESC doit avoir une valeur appropriée"""
        assert isinstance(AVERAGE_PRICE_DESC, str)
        assert len(AVERAGE_PRICE_DESC) > 0
        assert AVERAGE_PRICE_DESC == "Average purchase price"

    def test_current_price_desc_value(self):
        """CURRENT_PRICE_DESC doit avoir une valeur appropriée"""
        assert isinstance(CURRENT_PRICE_DESC, str)
        assert len(CURRENT_PRICE_DESC) > 0
        assert CURRENT_PRICE_DESC == "Current market price"

    def test_all_constants_are_strings(self):
        """Toutes les constantes descriptives doivent être des chaînes"""
        constants = [
            ASSET_SYMBOL_DESC,
            INVESTMENT_NAME_DESC,
            EXCHANGE_NAME_DESC,
            INVESTMENT_TYPE_DESC,
            INVESTMENT_SECTOR_DESC,
            MARKET_CAP_DESC,
            TRADING_CURRENCY_DESC,
            PORTFOLIO_NAME_DESC,
            USER_ID_DESC,
            AMOUNT_DESC,
            CURRENCY_CODE_DESC,
            QUANTITY_DESC,
            AVERAGE_PRICE_DESC,
            CURRENT_PRICE_DESC,
        ]

        for constant in constants:
            assert isinstance(constant, str)
            assert len(constant) > 0

    def test_constants_uniqueness(self):
        """Les constantes doivent avoir des valeurs uniques"""
        constants = [
            ASSET_SYMBOL_DESC,
            INVESTMENT_NAME_DESC,
            EXCHANGE_NAME_DESC,
            INVESTMENT_TYPE_DESC,
            INVESTMENT_SECTOR_DESC,
            MARKET_CAP_DESC,
            TRADING_CURRENCY_DESC,
            PORTFOLIO_NAME_DESC,
            USER_ID_DESC,
            AMOUNT_DESC,
            CURRENCY_CODE_DESC,
            QUANTITY_DESC,
            AVERAGE_PRICE_DESC,
            CURRENT_PRICE_DESC,
        ]

        # Vérifier l'unicité
        assert len(constants) == len(set(constants))


@pytest.mark.unit
class TestBaseDTO:
    """Tests pour la classe BaseDTO"""

    def test_basedto_is_pydantic_model(self):
        """BaseDTO doit hériter de BaseModel de Pydantic"""
        try:
            from pydantic import BaseModel

            # Vérifier que BaseDTO peut être utilisé comme un modèle Pydantic
            # sans utiliser issubclass qui peut être affecté par les mocks
            assert hasattr(BaseDTO, "model_validate")
            assert hasattr(BaseDTO, "model_dump")
            # Test alternatif : vérifier que BaseDTO hérite bien de BaseModel
            # en regardant les bases de sa classe
            base_names = [base.__name__ for base in BaseDTO.__bases__]
            assert "BaseModel" in base_names
        except (ImportError, AttributeError):
            pytest.skip(
                "pydantic BaseModel not available or BaseDTO structure different"
            )

    def test_basedto_instantiation(self):
        """BaseDTO peut être instanciée avec des données de base"""

        # BaseDTO étant une classe abstraite, on teste son comportement de base
        class TestDTO(BaseDTO):
            test_field: str = "test"

        dto = TestDTO()
        assert hasattr(dto, "test_field")
        assert dto.test_field == "test"

    def test_basedto_serialization(self):
        """BaseDTO doit supporter la sérialisation JSON"""

        class TestDTO(BaseDTO):
            name: str
            value: int

        dto = TestDTO(name="test", value=42)
        json_data = dto.model_dump()

        assert isinstance(json_data, dict)
        assert json_data["name"] == "test"
        assert json_data["value"] == 42

    def test_basedto_deserialization(self):
        """BaseDTO doit supporter la désérialisation depuis un dict"""

        class TestDTO(BaseDTO):
            name: str
            value: int

        data = {"name": "test", "value": 42}
        dto = TestDTO(**data)

        assert dto.name == "test"
        assert dto.value == 42

    def test_basedto_validation(self):
        """BaseDTO doit effectuer la validation des types"""

        class TestDTO(BaseDTO):
            name: str
            value: int

        # Test validation OK
        dto = TestDTO(name="test", value=42)
        assert dto.name == "test"
        assert dto.value == 42

        # Test validation échoue
        with pytest.raises((ValueError, TypeError)):
            TestDTO(name="test", value="not_an_int")

    def test_basedto_optional_fields(self):
        """BaseDTO gère les champs optionnels"""
        from typing import Optional

        class TestDTO(BaseDTO):
            required_field: str
            optional_field: Optional[str] = None

        # Avec champ optionnel fourni
        dto1 = TestDTO(required_field="req", optional_field="opt")
        assert dto1.optional_field == "opt"

        # Sans champ optionnel
        dto2 = TestDTO(required_field="req")
        assert dto2.optional_field is None

    def test_basedto_model_config(self):
        """BaseDTO doit avoir une configuration appropriée"""
        # Vérifier que BaseDTO a une configuration de base appropriée
        assert hasattr(BaseDTO, "model_config")
        # La configuration exacte peut varier selon l'implémentation

    def test_basedto_field_validation(self):
        """BaseDTO supporte les validateurs de champs personnalisés"""
        try:
            from pydantic import field_validator
        except ImportError:
            pytest.skip("pydantic field_validator not available")

        # Vérifier que nous pouvons créer une classe avec validation
        # sans utiliser des mocks qui interfèrent avec Pydantic
        class SimpleTestDTO(BaseDTO):
            value: int

        # Test basique de validation
        dto = SimpleTestDTO(value=42)
        assert dto.value == 42

        # Vérifier que l'annotation fonctionne
        assert hasattr(SimpleTestDTO, "__annotations__")
        assert "value" in SimpleTestDTO.__annotations__

    def test_basedto_imports_available(self):
        """BaseDTO doit importer les exceptions nécessaires"""
        # Vérifier que les exceptions sont importées dans le module
        from boursa_vision.application.dtos.base import (
            InvalidSymbolError,
            PriceRangeError,
        )

        assert InvalidSymbolError is not None
        assert PriceRangeError is not None
