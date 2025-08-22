"""
Tests unitaires pour Investment Entity
====================================

Tests des règles métier pour les investissements,
création, validation et comportements métier.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from boursa_vision.domain.entities.investment import (
    Investment,
    InvestmentSector,
    InvestmentType,
    MarketCap,
    FundamentalData,
    TechnicalData,
    InvestmentValidationException,
    AnalysisDataMissingException,
)
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.mark.unit
@pytest.mark.fast
class TestInvestmentType:
    """Tests pour l'énumération InvestmentType."""
    
    def test_should_have_expected_investment_types(self):
        """Devrait avoir les types d'investissement attendus."""
        # Act & Assert
        assert InvestmentType.STOCK.value == "STOCK"
        assert InvestmentType.BOND.value == "BOND"
        assert InvestmentType.ETF.value == "ETF"
        # Supprimer CRYPTO et COMMODITY car non implémentés


@pytest.mark.unit
@pytest.mark.fast
class TestInvestmentSector:
    """Tests pour l'énumération InvestmentSector."""
    
    def test_should_have_expected_sectors(self):
        """Devrait avoir tous les secteurs attendus."""
        # Act & Assert
        expected_sectors = [
            "TECHNOLOGY", "HEALTHCARE", "FINANCIAL",
            "CONSUMER_DISCRETIONARY", "CONSUMER_STAPLES",
            "ENERGY", "UTILITIES", "MATERIALS",
            "INDUSTRIALS", "TELECOMMUNICATIONS", "REAL_ESTATE"
        ]
        
        actual_sectors = [sector.value for sector in InvestmentSector]
        
        for expected in expected_sectors:
            assert expected in actual_sectors


@pytest.mark.unit
@pytest.mark.fast 
class TestMarketCap:
    """Tests pour l'énumération MarketCap."""
    
    def test_should_have_correct_market_cap_categories(self):
        """Devrait avoir les bonnes catégories de capitalisation."""
        # Act & Assert
        assert MarketCap.NANO.value == "NANO"
        assert MarketCap.MICRO.value == "MICRO"
        assert MarketCap.SMALL.value == "SMALL"
        assert MarketCap.MID.value == "MID"
        assert MarketCap.LARGE.value == "LARGE"
        assert MarketCap.MEGA.value == "MEGA"


@pytest.mark.unit
@pytest.mark.fast
class TestInvestmentCreation:
    """Tests de création des entités Investment."""
    
    def test_should_create_investment_with_valid_data(self):
        """Devrait créer un investissement avec des données valides."""
        # Arrange
        symbol = "AAPL"
        name = "Apple Inc."
        investment_type = InvestmentType.STOCK
        sector = InvestmentSector.TECHNOLOGY
        market_cap = MarketCap.LARGE
        exchange = "NASDAQ"
        currency = Currency.USD
        
        # Act
        investment = Investment.create(
            symbol=symbol,
            name=name,
            investment_type=investment_type,
            sector=sector,
            market_cap=market_cap,
            exchange=exchange,
            currency=currency
        )
        
        # Assert
        assert investment.symbol == symbol
        assert investment.name == name
        assert investment.investment_type == investment_type
        assert investment.sector == sector
        assert investment.market_cap == market_cap
        assert investment.exchange == exchange
        assert investment.currency == currency
        assert investment.id is not None
        assert isinstance(investment.created_at, datetime)
    
    def test_should_generate_unique_id_for_each_investment(self):
        """Devrait générer un ID unique pour chaque investissement."""
        # Arrange & Act
        investment1 = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD
        )
        
        investment2 = Investment.create(
            symbol="MSFT",
            name="Microsoft Corporation",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ", 
            currency=Currency.USD
        )
        
        # Assert
        assert investment1.id != investment2.id
    
    def test_should_set_timestamps_on_creation(self):
        """Devrait définir les timestamps lors de la création."""
        # Arrange
        before_creation = datetime.now(timezone.utc)
        
        # Act
        investment = Investment.create(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD
        )
        
        after_creation = datetime.now(timezone.utc)
        
        # Assert
        assert before_creation <= investment.created_at <= after_creation


@pytest.mark.unit
@pytest.mark.fast
class TestInvestmentValidation:
    """Tests de validation des investissements."""
    
    def test_should_raise_error_for_empty_symbol(self):
        """Devrait lever une erreur pour un symbole vide."""
        # Act & Assert
        with pytest.raises(InvestmentValidationException, match="Symbol cannot be empty"):
            Investment.create(
                symbol="",
                name="Test Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.LARGE,
                exchange="NASDAQ",
                currency=Currency.USD
            )
    
    def test_should_raise_error_for_empty_name(self):
        """Devrait lever une erreur pour un nom vide."""
        # Act & Assert
        with pytest.raises(InvestmentValidationException, match="Name cannot be empty"):
            Investment.create(
                symbol="TEST",
                name="",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.LARGE,
                exchange="NASDAQ",
                currency=Currency.USD
            )
    
    def test_should_normalize_symbol_to_uppercase(self):
        """Devrait normaliser le symbole en majuscules."""
        # Arrange & Act
        investment = Investment.create(
            symbol="aapl",
            name="Apple Inc.",
            investment_type=InvestmentType.STOCK,
            sector=InvestmentSector.TECHNOLOGY,
            market_cap=MarketCap.LARGE,
            exchange="NASDAQ",
            currency=Currency.USD
        )
        
        # Assert
        assert investment.symbol == "AAPL"
    
    def test_should_validate_symbol_format(self):
        """Devrait valider le format du symbole."""
        # Test avec un symbole invalide contenant des caractères spéciaux
        with pytest.raises(InvestmentValidationException):
            Investment.create(
                symbol="AAPL@123",
                name="Test Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.LARGE,
                exchange="NASDAQ",
                currency=Currency.USD
            )
    
    @pytest.mark.parametrize("symbol_length", [0, 1, 2, 11, 15])
    def test_should_validate_symbol_length(self, symbol_length):
        """Devrait valider la longueur du symbole."""
        # Arrange
        symbol = "A" * symbol_length
        
        if 3 <= symbol_length <= 10:
            # Act - Symbole valide
            investment = Investment.create(
                symbol=symbol,
                name="Test Company",
                investment_type=InvestmentType.STOCK,
                sector=InvestmentSector.TECHNOLOGY,
                market_cap=MarketCap.LARGE,
                exchange="NASDAQ",
                currency=Currency.USD
            )
            
            # Assert
            assert investment.symbol == symbol
        else:
            # Act & Assert - Symbole invalide
            with pytest.raises(InvestmentValidationException):
                Investment.create(
                    symbol=symbol,
                    name="Test Company",
                    investment_type=InvestmentType.STOCK,
                    sector=InvestmentSector.TECHNOLOGY,
                    market_cap=MarketCap.LARGE,
                    exchange="NASDAQ",
                    currency=Currency.USD
                )






