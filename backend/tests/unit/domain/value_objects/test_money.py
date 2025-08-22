"""
Tests unitaires pour Money Value Object
======================================

Tests des règles métier pour les opérations monétaires,
validation et calculs arithmétiques.
"""

import pytest
from decimal import Decimal, InvalidOperation
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.mark.unit
@pytest.mark.fast
class TestCurrency:
    """Tests pour l'énumération Currency."""
    
    def test_should_have_correct_symbols(self):
        """Les devises doivent avoir les bons symboles."""
        # Arrange & Act & Assert
        assert Currency.USD.symbol == "$"
        assert Currency.EUR.symbol == "€"
        assert Currency.GBP.symbol == "£"
        assert Currency.JPY.symbol == "¥"
        assert Currency.CHF.symbol == "Fr"
        assert Currency.CAD.symbol == "C$"
        assert Currency.AUD.symbol == "A$"
    
    def test_should_have_correct_decimal_places(self):
        """Les devises doivent avoir le bon nombre de décimales."""
        # Arrange & Act & Assert
        assert Currency.USD.decimal_places == 2
        assert Currency.EUR.decimal_places == 2
        assert Currency.JPY.decimal_places == 0  # Yen n'a pas de centimes
        assert Currency.CHF.decimal_places == 2
    
    def test_should_have_correct_names(self):
        """Les devises doivent avoir les bons noms."""
        # Arrange & Act & Assert
        assert Currency.USD.names == "US Dollar"
        assert Currency.EUR.names == "Euro"
        assert Currency.GBP.names == "British Pound"
        assert Currency.JPY.names == "Japanese Yen"


@pytest.mark.unit
@pytest.mark.fast
class TestMoneyCreation:
    """Tests de création et validation des objets Money."""
    
    def test_should_create_money_with_decimal_amount(self):
        """Devrait créer un objet Money avec un montant décimal."""
        # Arrange
        amount = Decimal("100.50")
        currency = Currency.USD
        
        # Act
        money = Money(amount, currency)
        
        # Assert
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.USD
    
    def test_should_create_money_with_float_amount(self):
        """Devrait convertir automatiquement un float en Decimal."""
        # Arrange
        amount = 100.50
        currency = Currency.USD
        
        # Act
        money = Money(amount, currency)
        
        # Assert
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.USD
    
    def test_should_create_money_with_string_amount(self):
        """Devrait convertir une chaîne en Decimal."""
        # Arrange
        amount = "100.50"
        currency = Currency.EUR
        
        # Act
        money = Money(amount, currency)
        
        # Assert
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.EUR
    
    def test_should_round_amount_to_currency_decimal_places(self):
        """Devrait arrondir selon les décimales de la devise."""
        # Arrange & Act
        usd_money = Money(Decimal("100.123"), Currency.USD)  # 2 décimales
        jpy_money = Money(Decimal("100.789"), Currency.JPY)  # 0 décimales
        
        # Assert
        assert usd_money.amount == Decimal("100.12")
        assert jpy_money.amount == Decimal("101")
    
    def test_should_raise_error_for_negative_amount(self):
        """Devrait lever une erreur pour un montant négatif."""
        # Arrange
        negative_amount = Decimal("-100.00")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            Money(negative_amount, Currency.USD)
    
    def test_should_raise_error_for_too_large_amount(self):
        """Devrait lever une erreur pour un montant trop élevé."""
        # Arrange
        large_amount = Decimal("9999999999999.99")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount too large"):
            Money(large_amount, Currency.USD)
    
    def test_should_accept_zero_amount(self):
        """Devrait accepter un montant de zéro."""
        # Arrange & Act
        money = Money(Decimal("0.00"), Currency.USD)
        
        # Assert
        assert money.amount == Decimal("0.00")
        assert money.currency == Currency.USD


@pytest.mark.unit 
@pytest.mark.fast
class TestMoneyArithmetic:
    """Tests des opérations arithmétiques sur Money."""
    
    def test_should_add_money_with_same_currency(self):
        """Devrait additionner deux montants de même devise."""
        # Arrange
        money1 = Money(Decimal("100.00"), Currency.USD)
        money2 = Money(Decimal("50.25"), Currency.USD)
        
        # Act
        result = money1 + money2
        
        # Assert
        assert result.amount == Decimal("150.25")
        assert result.currency == Currency.USD
    
    def test_should_subtract_money_with_same_currency(self):
        """Devrait soustraire deux montants de même devise."""
        # Arrange
        money1 = Money(Decimal("100.00"), Currency.USD)
        money2 = Money(Decimal("30.25"), Currency.USD)
        
        # Act
        result = money1 - money2
        
        # Assert
        assert result.amount == Decimal("69.75")
        assert result.currency == Currency.USD
    
    def test_should_multiply_by_number(self):
        """Devrait multiplier par un nombre."""
        # Arrange
        money = Money(Decimal("100.00"), Currency.USD)
        multiplier = Decimal("1.5")
        
        # Act
        result = money * multiplier
        
        # Assert
        assert result.amount == Decimal("150.00")
        assert result.currency == Currency.USD
    
    def test_should_divide_by_number(self):
        """Devrait diviser par un nombre."""
        # Arrange
        money = Money(Decimal("100.00"), Currency.USD)
        divisor = Decimal("4")
        
        # Act
        result = money / divisor
        
        # Assert
        assert result.amount == Decimal("25.00")
        assert result.currency == Currency.USD
    
    def test_should_raise_error_when_dividing_by_zero(self):
        """Devrait lever une erreur lors de la division par zéro."""
        # Arrange
        money = Money(Decimal("100.00"), Currency.USD)
        
        # Act & Assert
        with pytest.raises(ZeroDivisionError):
            money / Decimal("0")
    
    def test_should_handle_multiplication_with_zero(self):
        """Devrait gérer la multiplication par zéro."""
        # Arrange
        money = Money(Decimal("100.00"), Currency.USD)
        
        # Act
        result = money * Decimal("0")
        
        # Assert
        assert result.amount == Decimal("0.00")
        assert result.currency == Currency.USD


@pytest.mark.unit
@pytest.mark.fast
class TestMoneyComparison:
    """Tests des comparaisons entre objets Money."""
    
    def test_should_compare_equal_money(self):
        """Devrait comparer correctement des montants égaux."""
        # Arrange
        money1 = Money(Decimal("100.00"), Currency.USD)
        money2 = Money(Decimal("100.00"), Currency.USD)
        
        # Act & Assert
        assert money1 == money2
        assert not (money1 != money2)
    
    def test_should_compare_different_amounts(self):
        """Devrait comparer correctement des montants différents."""
        # Arrange
        money1 = Money(Decimal("100.00"), Currency.USD)
        money2 = Money(Decimal("50.00"), Currency.USD)
        
        # Act & Assert
        assert money1 > money2
        assert money2 < money1
        assert money1 >= money2
        assert money2 <= money1
        assert money1 != money2
    
    def test_should_raise_error_when_comparing_different_currencies(self):
        """Devrait lever une erreur lors de la comparaison de devises différentes."""
        # Arrange
        usd_money = Money(Decimal("100.00"), Currency.USD)
        eur_money = Money(Decimal("100.00"), Currency.EUR)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            usd_money > eur_money
        
        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            usd_money < eur_money
        
        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            usd_money >= eur_money
        
        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            usd_money <= eur_money
    
    def test_should_allow_equality_comparison_different_currencies(self):
        """Devrait permettre la comparaison d'égalité entre devises différentes."""
        # Arrange
        usd_money = Money(Decimal("100.00"), Currency.USD)
        eur_money = Money(Decimal("100.00"), Currency.EUR)
        
        # Act & Assert
        assert usd_money != eur_money  # Différentes devises ne sont jamais égales


@pytest.mark.unit
@pytest.mark.fast
class TestMoneyFormatting:
    """Tests du formatage des objets Money."""
    
    def test_should_format_money_as_string(self):
        """Devrait formater Money comme chaîne de caractères."""
        # Arrange
        money = Money(Decimal("100.50"), Currency.USD)
        
        # Act
        result = str(money)
        
        # Assert
        assert "$100.50" in result or "100.50 USD" in result
    
    
    def test_should_have_readable_repr(self):
        """Devrait avoir une représentation lisible."""
        # Arrange
        money = Money(Decimal("100.50"), Currency.USD)
        
        # Act
        result = repr(money)
        
        # Assert
        assert "Money" in result
        assert "100.50" in result
        assert "USD" in result


@pytest.mark.unit
@pytest.mark.fast
class TestMoneyImmutability:
    """Tests de l'immutabilité des objets Money."""
    
    def test_should_be_immutable(self):
        """Les objets Money doivent être immutables."""
        # Arrange
        money = Money(Decimal("100.00"), Currency.USD)
        
        # Act & Assert
        with pytest.raises(AttributeError):
            money.amount = Decimal("200.00")
        
        with pytest.raises(AttributeError):
            money.currency = Currency.EUR
    
    def test_should_be_hashable(self):
        """Les objets Money doivent être hashable (utilisables comme clés)."""
        # Arrange
        money1 = Money(Decimal("100.00"), Currency.USD)
        money2 = Money(Decimal("100.00"), Currency.USD)
        money3 = Money(Decimal("50.00"), Currency.USD)
        
        # Act
        money_set = {money1, money2, money3}
        
        # Assert
        assert len(money_set) == 2  # money1 et money2 sont identiques
        assert money1 in money_set
        assert money3 in money_set


@pytest.mark.unit
@pytest.mark.fast
class TestMoneyEdgeCases:
    """Tests des cas limites pour Money."""
    
    def test_should_handle_very_small_amounts(self):
        """Devrait gérer les très petits montants."""
        # Arrange & Act
        small_money = Money(Decimal("0.01"), Currency.USD)
        
        # Assert
        assert small_money.amount == Decimal("0.01")
    
    def test_should_handle_rounding_edge_cases(self):
        """Devrait gérer correctement les cas limites d'arrondi."""
        # Arrange & Act
        money1 = Money(Decimal("0.125"), Currency.USD)  # Milieu -> arrondi vers le haut
        money2 = Money(Decimal("0.124"), Currency.USD)  # En dessous du milieu
        
        # Assert
        assert money1.amount == Decimal("0.13")
        assert money2.amount == Decimal("0.12")
    
    def test_should_handle_precision_loss(self):
        """Devrait gérer la perte de précision dans les calculs."""
        # Arrange
        money = Money(Decimal("1.00"), Currency.USD)
        
        # Act - Division puis multiplication
        result = (money / Decimal("3")) * Decimal("3")
        
        # Assert - Devrait être proche de 1.00 mais peut ne pas être exactement égal
        assert abs(result.amount - Decimal("1.00")) <= Decimal("0.01")
    
    @pytest.mark.parametrize("invalid_amount", [
        "not_a_number",
        "",
        None,
        float('inf'),
        float('-inf'),
    ])
    def test_should_raise_error_for_invalid_amounts(self, invalid_amount):
        """Devrait lever une erreur pour des montants invalides."""
        # Act & Assert
        with pytest.raises((ValueError, InvalidOperation, TypeError)):
            Money(invalid_amount, Currency.USD)
    
    def test_should_handle_string_conversion_edge_cases(self):
        """Devrait gérer les cas limites de conversion de chaînes."""
        # Arrange & Act & Assert
        money1 = Money("100.00000", Currency.USD)  # Trop de décimales
        assert money1.amount == Decimal("100.00")
        
        money2 = Money("100", Currency.USD)  # Pas de décimales
        assert money2.amount == Decimal("100.00")
        
        money3 = Money(" 100.50 ", Currency.USD)  # Espaces
        assert money3.amount == Decimal("100.50")
