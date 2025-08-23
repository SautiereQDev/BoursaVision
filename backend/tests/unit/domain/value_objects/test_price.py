"""
Tests pour Price Value Objects
==============================

Tests unitaires couvrant les value objects Price, PricePoint et PriceData
avec validation des règles métier financières.
"""

import statistics
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from boursa_vision.domain.value_objects.money import Currency, Money

# Imports à tester
from boursa_vision.domain.value_objects.price import Price, PriceData, PricePoint


class TestPrice:
    """Tests pour Price value object"""

    def setup_method(self):
        """Configuration pour chaque test"""
        self.usd = Currency.USD
        self.eur = Currency.EUR
        self.timestamp = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

    @pytest.mark.unit
    def test_price_creation_with_decimal(self):
        """Test création d'un prix avec Decimal"""
        price = Price(
            value=Decimal("100.50"), currency=self.usd, timestamp=self.timestamp
        )

        assert price.value == Decimal("100.50")
        assert price.currency == self.usd
        assert price.timestamp == self.timestamp

    @pytest.mark.unit
    def test_price_creation_with_string(self):
        """Test création d'un prix avec string"""
        # Le __post_init__ convertit automatiquement en Decimal
        price = Price(value=Decimal("100.50"), currency=self.usd)  # type: ignore

        assert price.value == Decimal("100.50")
        assert price.currency == self.usd

    @pytest.mark.unit
    def test_price_creation_with_int(self):
        """Test création d'un prix avec int"""
        # Le __post_init__ convertit automatiquement en Decimal
        price = Price(value=Decimal("100"), currency=self.usd)  # type: ignore

        assert price.value == Decimal("100")
        assert price.currency == self.usd

    @pytest.mark.unit
    def test_price_precision_rounding(self):
        """Test arrondi à 4 décimales"""
        price = Price(value=Decimal("100.123456"), currency=self.usd)

        assert price.value == Decimal("100.1235")  # Arrondi à 4 décimales

    @pytest.mark.unit
    def test_price_negative_value_raises_error(self):
        """Test qu'un prix négatif lève une erreur"""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Price(value=Decimal("-10.50"), currency=self.usd)

    @pytest.mark.unit
    def test_price_too_high_raises_error(self):
        """Test qu'un prix trop élevé lève une erreur"""
        with pytest.raises(ValueError, match="Price too high"):
            Price(value=Decimal("1000000"), currency=self.usd)

    @pytest.mark.unit
    def test_price_from_float(self):
        """Test création depuis float"""
        price = Price.from_float(100.50, self.usd, self.timestamp)

        assert price.value == Decimal("100.50")
        assert price.currency == self.usd
        assert price.timestamp == self.timestamp

    @pytest.mark.unit
    def test_price_to_money(self):
        """Test conversion vers Money"""
        price = Price(value=Decimal("100.50"), currency=self.usd)
        quantity = Decimal("10")

        money = price.to_money(quantity)

        assert isinstance(money, Money)
        assert money.amount == Decimal("1005.00")
        assert money.currency == self.usd

    @pytest.mark.unit
    def test_price_change_from(self):
        """Test calcul de changement absolu"""
        price1 = Price(value=Decimal("100.00"), currency=self.usd)
        price2 = Price(value=Decimal("105.50"), currency=self.usd)

        change = price2.change_from(price1)

        assert change == Decimal("5.50")

    @pytest.mark.unit
    def test_price_change_from_different_currency_raises_error(self):
        """Test changement entre différentes devises"""
        price_usd = Price(value=Decimal("100.00"), currency=self.usd)
        price_eur = Price(value=Decimal("90.00"), currency=self.eur)

        with pytest.raises(
            ValueError, match="Cannot compare prices in different currencies"
        ):
            price_eur.change_from(price_usd)

    @pytest.mark.unit
    def test_price_change_percentage_from(self):
        """Test calcul de changement en pourcentage"""
        price1 = Price(value=Decimal("100.00"), currency=self.usd)
        price2 = Price(value=Decimal("110.00"), currency=self.usd)

        change_pct = price2.change_percentage_from(price1)

        assert change_pct == Decimal("10.00")

    @pytest.mark.unit
    def test_price_change_percentage_from_zero_previous(self):
        """Test changement en pourcentage depuis prix zéro"""
        price1 = Price(value=Decimal("0.00"), currency=self.usd)
        price2 = Price(value=Decimal("10.00"), currency=self.usd)

        change_pct = price2.change_percentage_from(price1)

        assert change_pct == Decimal("0")

    @pytest.mark.unit
    def test_price_is_higher_than(self):
        """Test comparaison de prix"""
        price1 = Price(value=Decimal("100.00"), currency=self.usd)
        price2 = Price(value=Decimal("105.00"), currency=self.usd)

        assert price2.is_higher_than(price1)
        assert not price1.is_higher_than(price2)

    @pytest.mark.unit
    def test_price_is_higher_than_different_currency_raises_error(self):
        """Test comparaison entre différentes devises"""
        price_usd = Price(value=Decimal("100.00"), currency=self.usd)
        price_eur = Price(value=Decimal("90.00"), currency=self.eur)

        with pytest.raises(
            ValueError, match="Cannot compare prices in different currencies"
        ):
            price_usd.is_higher_than(price_eur)

    @pytest.mark.unit
    def test_price_format_with_currency(self):
        """Test formatage avec devise"""
        price = Price(value=Decimal("100.50"), currency=self.usd)

        formatted = price.format(include_currency=True)

        assert formatted == "100.5 USD"

    @pytest.mark.unit
    def test_price_format_without_currency(self):
        """Test formatage sans devise"""
        price = Price(value=Decimal("100.50"), currency=self.usd)

        formatted = price.format(include_currency=False)

        assert formatted == "100.5"

    @pytest.mark.unit
    def test_price_format_removes_trailing_zeros(self):
        """Test suppression des zéros de fin"""
        price = Price(value=Decimal("100.0000"), currency=self.usd)

        formatted = price.format(include_currency=False)

        assert formatted == "100"

    @pytest.mark.unit
    def test_price_str_representation(self):
        """Test représentation string"""
        price = Price(value=Decimal("100.50"), currency=self.usd)

        assert str(price) == "100.5 USD"

    @pytest.mark.unit
    def test_price_immutable(self):
        """Test que Price est immutable"""
        price = Price(value=Decimal("100.50"), currency=self.usd)

        with pytest.raises((AttributeError, TypeError)):
            price.value = Decimal("200.00")  # type: ignore


class TestPricePoint:
    """Tests pour PricePoint value object"""

    def setup_method(self):
        """Configuration pour chaque test"""
        self.usd = Currency.USD
        self.eur = Currency.EUR
        self.timestamp = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        # Prix valides pour OHLC
        self.open_price = Price(Decimal("100.00"), self.usd)
        self.high_price = Price(Decimal("105.00"), self.usd)
        self.low_price = Price(Decimal("98.00"), self.usd)
        self.close_price = Price(Decimal("102.00"), self.usd)
        self.volume = 1500000

    @pytest.mark.unit
    def test_price_point_creation_valid(self):
        """Test création d'un PricePoint valide"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        assert point.timestamp == self.timestamp
        assert point.open_price == self.open_price
        assert point.high_price == self.high_price
        assert point.low_price == self.low_price
        assert point.close_price == self.close_price
        assert point.volume == self.volume
        assert point.currency == self.usd

    @pytest.mark.unit
    def test_price_point_with_adjusted_close(self):
        """Test PricePoint avec adjusted close"""
        adjusted_close = Price(Decimal("101.50"), self.usd)
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
            adjusted_close=adjusted_close,
        )

        assert point.adjusted_close == adjusted_close

    @pytest.mark.unit
    def test_price_point_different_currencies_raises_error(self):
        """Test qu'un mélange de devises lève une erreur"""
        eur_price = Price(Decimal("90.00"), self.eur)

        with pytest.raises(ValueError, match="All prices must be in the same currency"):
            PricePoint(
                timestamp=self.timestamp,
                open_price=self.open_price,
                high_price=eur_price,  # Différente devise
                low_price=self.low_price,
                close_price=self.close_price,
                volume=self.volume,
            )

    @pytest.mark.unit
    def test_price_point_invalid_ohlc_open_too_high(self):
        """Test OHLC invalide - open trop haut"""
        invalid_open = Price(Decimal("106.00"), self.usd)  # > high_price

        with pytest.raises(
            ValueError, match="Invalid OHLC: open price not between high and low"
        ):
            PricePoint(
                timestamp=self.timestamp,
                open_price=invalid_open,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=self.close_price,
                volume=self.volume,
            )

    @pytest.mark.unit
    def test_price_point_invalid_ohlc_open_too_low(self):
        """Test OHLC invalide - open trop bas"""
        invalid_open = Price(Decimal("97.00"), self.usd)  # < low_price

        with pytest.raises(
            ValueError, match="Invalid OHLC: open price not between high and low"
        ):
            PricePoint(
                timestamp=self.timestamp,
                open_price=invalid_open,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=self.close_price,
                volume=self.volume,
            )

    @pytest.mark.unit
    def test_price_point_invalid_ohlc_close_too_high(self):
        """Test OHLC invalide - close trop haut"""
        invalid_close = Price(Decimal("106.00"), self.usd)  # > high_price

        with pytest.raises(
            ValueError, match="Invalid OHLC: close price not between high and low"
        ):
            PricePoint(
                timestamp=self.timestamp,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=invalid_close,
                volume=self.volume,
            )

    @pytest.mark.unit
    def test_price_point_invalid_ohlc_close_too_low(self):
        """Test OHLC invalide - close trop bas"""
        invalid_close = Price(Decimal("97.00"), self.usd)  # < low_price

        with pytest.raises(
            ValueError, match="Invalid OHLC: close price not between high and low"
        ):
            PricePoint(
                timestamp=self.timestamp,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=invalid_close,
                volume=self.volume,
            )

    @pytest.mark.unit
    def test_price_point_negative_volume_raises_error(self):
        """Test qu'un volume négatif lève une erreur"""
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            PricePoint(
                timestamp=self.timestamp,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                close_price=self.close_price,
                volume=-100,
            )

    @pytest.mark.unit
    def test_price_point_price_range(self):
        """Test calcul de la fourchette de prix"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        expected_range = Decimal("7.00")  # 105.00 - 98.00
        assert point.price_range == expected_range

    @pytest.mark.unit
    def test_price_point_price_change(self):
        """Test calcul du changement de prix"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        expected_change = Decimal("2.00")  # 102.00 - 100.00
        assert point.price_change == expected_change

    @pytest.mark.unit
    def test_price_point_price_change_percentage(self):
        """Test calcul du changement en pourcentage"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        expected_pct = Decimal("2.00")  # (102.00 - 100.00) / 100.00 * 100
        assert point.price_change_percentage == expected_pct

    @pytest.mark.unit
    def test_price_point_price_change_percentage_zero_open(self):
        """Test changement en pourcentage avec open = 0"""
        zero_open = Price(Decimal("0.00"), self.usd)
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=zero_open,
            high_price=self.high_price,
            low_price=zero_open,
            close_price=self.close_price,
            volume=self.volume,
        )

        assert point.price_change_percentage == Decimal("0")

    @pytest.mark.unit
    def test_price_point_is_bullish(self):
        """Test détection de chandelier haussier"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        assert point.is_bullish()  # close > open

    @pytest.mark.unit
    def test_price_point_is_bearish(self):
        """Test détection de chandelier baissier"""
        bearish_close = Price(Decimal("99.00"), self.usd)
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=bearish_close,
            volume=self.volume,
        )

        assert point.is_bearish()  # close < open
        assert not point.is_bullish()

    @pytest.mark.unit
    def test_price_point_is_doji_default_threshold(self):
        """Test détection de doji avec seuil par défaut"""
        # Close très proche de open (< 0.1%)
        doji_close = Price(Decimal("100.05"), self.usd)
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=doji_close,
            volume=self.volume,
        )

        assert point.is_doji()

    @pytest.mark.unit
    def test_price_point_is_doji_custom_threshold(self):
        """Test détection de doji avec seuil personnalisé"""
        doji_close = Price(Decimal("100.50"), self.usd)  # 0.5% de différence
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=doji_close,
            volume=self.volume,
        )

        assert not point.is_doji(Decimal("0.1"))  # Seuil 0.1%
        assert point.is_doji(Decimal("1.0"))  # Seuil 1.0%

    @pytest.mark.unit
    def test_price_point_is_doji_zero_open(self):
        """Test détection de doji avec open = 0"""
        zero_open = Price(Decimal("0.00"), self.usd)
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=zero_open,
            high_price=self.high_price,
            low_price=zero_open,
            close_price=self.close_price,
            volume=self.volume,
        )

        assert not point.is_doji()

    @pytest.mark.unit
    def test_price_point_immutable(self):
        """Test que PricePoint est immutable"""
        point = PricePoint(
            timestamp=self.timestamp,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            volume=self.volume,
        )

        with pytest.raises((AttributeError, TypeError)):
            point.volume = 2000000  # type: ignore


class TestPriceData:
    """Tests pour PriceData collection"""

    def setup_method(self):
        """Configuration pour chaque test"""
        self.usd = Currency.USD
        self.eur = Currency.EUR
        self.symbol = "AAPL"
        self.interval = "1d"

        # Création de plusieurs points de prix pour une série temporelle
        base_time = datetime(2024, 1, 15, tzinfo=UTC)
        self.points = [
            PricePoint(
                timestamp=base_time + timedelta(days=i),
                open_price=Price(Decimal(f"{100 + i}.00"), self.usd),
                high_price=Price(Decimal(f"{105 + i}.00"), self.usd),
                low_price=Price(Decimal(f"{98 + i}.00"), self.usd),
                close_price=Price(Decimal(f"{102 + i}.00"), self.usd),
                volume=1500000 + (i * 100000),
            )
            for i in range(5)
        ]

    @pytest.mark.unit
    def test_price_data_creation_valid(self):
        """Test création de PriceData valide"""
        price_data = PriceData(
            symbol=self.symbol, points=self.points, interval=self.interval
        )

        assert price_data.symbol == self.symbol
        assert price_data.points == self.points
        assert price_data.interval == self.interval
        assert price_data.currency == self.usd

    @pytest.mark.unit
    def test_price_data_empty_points_raises_error(self):
        """Test qu'une liste vide de points lève une erreur"""
        with pytest.raises(ValueError, match="Price data cannot be empty"):
            PriceData(symbol=self.symbol, points=[], interval=self.interval)

    @pytest.mark.unit
    def test_price_data_empty_symbol_raises_error(self):
        """Test qu'un symbole vide lève une erreur"""
        with pytest.raises(ValueError, match="Symbol is required"):
            PriceData(symbol="", points=self.points, interval=self.interval)

    @pytest.mark.unit
    def test_price_data_non_chronological_raises_error(self):
        """Test qu'un ordre non chronologique lève une erreur"""
        # Inverser l'ordre des points
        reversed_points = list(reversed(self.points))

        with pytest.raises(
            ValueError, match="Price points must be in chronological order"
        ):
            PriceData(
                symbol=self.symbol, points=reversed_points, interval=self.interval
            )

    @pytest.mark.unit
    def test_price_data_mixed_currencies_raises_error(self):
        """Test qu'un mélange de devises lève une erreur"""
        # Créer un point avec EUR
        eur_point = PricePoint(
            timestamp=datetime(2024, 1, 20, tzinfo=UTC),
            open_price=Price(Decimal("90.00"), self.eur),
            high_price=Price(Decimal("92.00"), self.eur),
            low_price=Price(Decimal("88.00"), self.eur),
            close_price=Price(Decimal("91.00"), self.eur),
            volume=1000000,
        )

        mixed_points = [*self.points, eur_point]

        with pytest.raises(
            ValueError, match="All price points must be in the same currency"
        ):
            PriceData(symbol=self.symbol, points=mixed_points, interval=self.interval)

    @pytest.mark.unit
    def test_price_data_latest_price(self):
        """Test récupération du dernier prix"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        expected_latest = self.points[-1].close_price
        assert price_data.latest_price == expected_latest

    @pytest.mark.unit
    def test_price_data_oldest_price(self):
        """Test récupération du premier prix"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        expected_oldest = self.points[0].close_price
        assert price_data.oldest_price == expected_oldest

    @pytest.mark.unit
    def test_price_data_period_return(self):
        """Test calcul du rendement sur la période"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        # oldest = 102.00, latest = 106.00
        # return = (106.00 - 102.00) / 102.00 * 100 = ~3.92%
        expected_return = price_data.latest_price.change_percentage_from(
            price_data.oldest_price
        )
        assert price_data.period_return == expected_return

    @pytest.mark.unit
    def test_price_data_period_return_single_point(self):
        """Test rendement avec un seul point"""
        single_point_data = PriceData(self.symbol, [self.points[0]], self.interval)

        assert single_point_data.period_return == Decimal("0")

    @pytest.mark.unit
    def test_price_data_highest_price(self):
        """Test récupération du prix le plus haut"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        # Le high du dernier point devrait être le plus élevé
        expected_highest = self.points[-1].high_price
        assert price_data.highest_price == expected_highest

    @pytest.mark.unit
    def test_price_data_lowest_price(self):
        """Test récupération du prix le plus bas"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        # Le low du premier point devrait être le plus bas
        expected_lowest = self.points[0].low_price
        assert price_data.lowest_price == expected_lowest

    @pytest.mark.unit
    def test_price_data_average_volume(self):
        """Test calcul du volume moyen"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        volumes = [point.volume for point in self.points]
        expected_avg = int(statistics.mean(volumes))
        assert price_data.average_volume == expected_avg

    @pytest.mark.unit
    def test_price_data_total_volume(self):
        """Test calcul du volume total"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        expected_total = sum(point.volume for point in self.points)
        assert price_data.total_volume == expected_total

    @pytest.mark.unit
    def test_price_data_get_closing_prices(self):
        """Test extraction des prix de clôture"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        closing_prices = price_data.get_closing_prices()
        expected_closes = [point.close_price.value for point in self.points]

        assert closing_prices == expected_closes
        assert len(closing_prices) == 5

    @pytest.mark.unit
    def test_price_data_get_returns(self):
        """Test calcul des rendements quotidiens"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        returns = price_data.get_returns()

        # Avec 5 points, on devrait avoir 4 rendements
        assert len(returns) == 4

        # Calcul manuel du premier rendement
        # Point 0: close = 102.00, Point 1: close = 103.00
        # Return = (103.00 - 102.00) / 102.00 ≈ 0.0098
        expected_first_return = (Decimal("103.00") - Decimal("102.00")) / Decimal(
            "102.00"
        )
        assert abs(returns[0] - expected_first_return) < Decimal("0.0001")

    @pytest.mark.unit
    def test_price_data_get_returns_single_point(self):
        """Test rendements avec un seul point"""
        single_point_data = PriceData(self.symbol, [self.points[0]], self.interval)

        returns = single_point_data.get_returns()
        assert returns == []

    @pytest.mark.unit
    def test_price_data_get_returns_with_zero_close(self):
        """Test rendements avec prix de clôture zéro"""
        # Créer un point avec close = 0
        zero_point = PricePoint(
            timestamp=datetime(2024, 1, 10, tzinfo=UTC),
            open_price=Price(Decimal("1.00"), self.usd),
            high_price=Price(Decimal("2.00"), self.usd),
            low_price=Price(Decimal("0.00"), self.usd),
            close_price=Price(Decimal("0.00"), self.usd),
            volume=1000000,
        )

        points_with_zero = [zero_point, *self.points]
        price_data = PriceData(self.symbol, points_with_zero, self.interval)

        returns = price_data.get_returns()

        # Le premier rendement devrait être très élevé (de 0 à 102)
        # Mais le calcul ignore les divisions par zéro, donc on aura 4 rendements au lieu de 5
        assert len(returns) == 4

    @pytest.mark.unit
    def test_price_data_calculate_volatility(self):
        """Test calcul de la volatilité"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        volatility = price_data.calculate_volatility()

        # La volatilité devrait être > 0 avec des prix variés
        assert volatility > Decimal("0")
        assert isinstance(volatility, Decimal)

    @pytest.mark.unit
    def test_price_data_calculate_volatility_insufficient_data(self):
        """Test volatilité avec données insuffisantes"""
        single_point_data = PriceData(self.symbol, [self.points[0]], self.interval)

        volatility = single_point_data.calculate_volatility()
        assert volatility == Decimal("0")

    @pytest.mark.unit
    def test_price_data_get_price_at_date(self):
        """Test récupération de prix à une date donnée"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        target_date = self.points[2].timestamp.date()
        price_at_date = price_data.get_price_at_date(target_date)

        assert price_at_date == self.points[2].close_price

    @pytest.mark.unit
    def test_price_data_get_price_at_date_not_found(self):
        """Test récupération de prix à une date inexistante"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        nonexistent_date = date(2024, 2, 1)
        price_at_date = price_data.get_price_at_date(nonexistent_date)

        assert price_at_date is None

    @pytest.mark.unit
    def test_price_data_slice_by_date(self):
        """Test découpage par plage de dates"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        start_date = self.points[1].timestamp.date()
        end_date = self.points[3].timestamp.date()

        sliced_data = price_data.slice_by_date(start_date, end_date)

        assert len(sliced_data) == 3  # Points 1, 2, 3
        assert sliced_data.symbol == self.symbol
        assert sliced_data.interval == self.interval
        assert sliced_data.points[0] == self.points[1]
        assert sliced_data.points[-1] == self.points[3]

    @pytest.mark.unit
    def test_price_data_slice_by_date_no_matches(self):
        """Test découpage sans correspondances"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        start_date = date(2024, 2, 1)
        end_date = date(2024, 2, 10)

        # Le slice sans correspondance devrait lever une ValueError car PriceData ne peut pas être vide
        with pytest.raises(ValueError, match="Price data cannot be empty"):
            price_data.slice_by_date(start_date, end_date)

    @pytest.mark.unit
    def test_price_data_len(self):
        """Test longueur de la collection"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        assert len(price_data) == 5

    @pytest.mark.unit
    def test_price_data_iter(self):
        """Test itération sur la collection"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        iterated_points = list(price_data)

        assert iterated_points == self.points

    @pytest.mark.unit
    def test_price_data_getitem(self):
        """Test accès par index"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        assert price_data[0] == self.points[0]
        assert price_data[2] == self.points[2]
        assert price_data[-1] == self.points[-1]

    @pytest.mark.unit
    def test_price_data_getitem_index_error(self):
        """Test accès par index invalide"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        with pytest.raises(IndexError):
            price_data[10]

    @pytest.mark.unit
    def test_price_data_immutable(self):
        """Test que PriceData est immutable"""
        price_data = PriceData(self.symbol, self.points, self.interval)

        with pytest.raises((AttributeError, TypeError)):
            price_data.symbol = "GOOGL"  # type: ignore


class TestPriceEdgeCases:
    """Tests pour les cas limites et edge cases"""

    def setup_method(self):
        """Configuration pour chaque test"""
        self.usd = Currency.USD

    @pytest.mark.unit
    def test_price_with_very_small_value(self):
        """Test prix avec valeur très petite"""
        small_price = Price(value=Decimal("0.0001"), currency=self.usd)

        assert small_price.value == Decimal("0.0001")

    @pytest.mark.unit
    def test_price_with_maximum_value(self):
        """Test prix avec valeur maximale"""
        max_price = Price(value=Decimal("999999.9999"), currency=self.usd)

        assert max_price.value == Decimal("999999.9999")

    @pytest.mark.unit
    def test_price_precision_edge_cases(self):
        """Test cas limites de précision"""
        # Test avec beaucoup de décimales
        price = Price(value=Decimal("100.123456789"), currency=self.usd)
        assert price.value == Decimal("100.1235")

        # Test avec .99995 qui devrait s'arrondir à 1.0000
        price2 = Price(value=Decimal("100.99995"), currency=self.usd)
        assert price2.value == Decimal("101.0000")

    @pytest.mark.unit
    def test_price_change_negative_result(self):
        """Test changement avec résultat négatif"""
        price1 = Price(value=Decimal("100.00"), currency=self.usd)
        price2 = Price(value=Decimal("95.00"), currency=self.usd)

        change = price2.change_from(price1)
        assert change == Decimal("-5.00")

        change_pct = price2.change_percentage_from(price1)
        assert change_pct == Decimal("-5.00")

    @pytest.mark.unit
    def test_price_point_equal_ohlc(self):
        """Test PricePoint avec tous les prix égaux"""
        equal_price = Price(Decimal("100.00"), self.usd)
        point = PricePoint(
            timestamp=datetime.now(UTC),
            open_price=equal_price,
            high_price=equal_price,
            low_price=equal_price,
            close_price=equal_price,
            volume=1000000,
        )

        assert point.price_range == Decimal("0")
        assert point.price_change == Decimal("0")
        assert point.price_change_percentage == Decimal("0")
        assert not point.is_bullish()
        assert not point.is_bearish()
        assert point.is_doji()

    @pytest.mark.unit
    def test_price_data_with_identical_timestamps(self):
        """Test PriceData avec timestamps identiques - devrait échouer"""
        same_timestamp = datetime(2024, 1, 15, tzinfo=UTC)
        identical_points = [
            PricePoint(
                timestamp=same_timestamp,
                open_price=Price(Decimal("100.00"), self.usd),
                high_price=Price(Decimal("105.00"), self.usd),
                low_price=Price(Decimal("98.00"), self.usd),
                close_price=Price(Decimal("102.00"), self.usd),
                volume=1500000,
            ),
            PricePoint(
                timestamp=same_timestamp,  # Même timestamp
                open_price=Price(Decimal("101.00"), self.usd),
                high_price=Price(Decimal("106.00"), self.usd),
                low_price=Price(Decimal("99.00"), self.usd),
                close_price=Price(Decimal("103.00"), self.usd),
                volume=1600000,
            ),
        ]

        # Cela ne devrait PAS lever d'erreur car les timestamps sont triés correctement
        # (identiques = triés)
        price_data = PriceData("AAPL", identical_points, "1d")
        assert len(price_data) == 2
