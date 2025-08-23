"""
Technical Analysis Application Service
=====================================

Application service that coordinates technical analysis operations
and orchestrates domain services for market analysis.
"""

from datetime import datetime, timedelta
from typing import Any

from ..dtos import TechnicalAnalysisDTO


class TechnicalAnalyzer:
    """
    Application service for technical analysis operations.

    Coordinates between domain services and repositories to provide
    technical analysis capabilities for investments.
    """

    def __init__(
        self,
        investment_repository: Any,
        market_data_repository: Any,
        scoring_service: Any,
    ) -> None:
        """Initialize technical analyzer with dependencies."""
        self._investment_repository = investment_repository
        self._market_data_repository = market_data_repository
        self._scoring_service = scoring_service

    async def analyze_investment(
        self, symbol: str, period_days: int = 252
    ) -> TechnicalAnalysisDTO:
        """
        Perform comprehensive technical analysis for an investment.

        Args:
            symbol: Investment symbol to analyze
            period_days: Number of days to analyze (default: 252 trading days)

        Returns:
            TechnicalAnalysisDTO: Technical analysis results

        Raises:
            ValueError: If symbol is invalid or no data available
        """
        try:
            # Get investment data
            investment = await self._investment_repository.find_by_symbol(symbol)
            if not investment:
                raise ValueError(f"Investment with symbol {symbol} not found")

            # Get market data for analysis period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            market_data = await self._market_data_repository.get_price_history(
                symbol=symbol, start_date=start_date, end_date=end_date
            )

            if (
                not market_data
                or not hasattr(market_data, "price_data")
                or not market_data.price_data
            ):
                raise ValueError(f"Insufficient market data for {symbol}")

            # Calculate technical indicators
            indicators = self._calculate_technical_indicators(market_data)

            # Create and return DTO
            return TechnicalAnalysisDTO(
                symbol=symbol,
                rsi=indicators.get("rsi"),
                macd=indicators.get("macd"),
                bollinger_position=indicators.get("bollinger_position"),
                sma_20=indicators.get("sma_20"),
                sma_50=indicators.get("sma_50"),
                volume_trend=indicators.get("volume_trend"),
                support_level=indicators.get("support_level"),
                resistance_level=indicators.get("resistance_level"),
            )

        except ValueError:
            # Re-raise ValueError for proper error handling in tests
            raise
        except Exception as e:
            # In production, log the error and return gracefully for other exceptions
            print(f"Error analyzing investment {symbol}: {e}")
            return self._create_empty_analysis(symbol)

    async def analyze_multiple_investments(
        self, symbols: list[str], period_days: int = 252
    ) -> dict[str, TechnicalAnalysisDTO]:
        """
        Analyze multiple investments for technical indicators.

        Args:
            symbols: List of investment symbols to analyze
            period_days: Number of days to analyze

        Returns:
            Dictionary mapping symbols to technical analysis results
        """
        results = {}

        for symbol in symbols:
            try:
                analysis = await self.analyze_investment(symbol, period_days)
                results[symbol] = analysis
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                # Skip failed analyses - don't add to results
                continue

        return results

    def _create_empty_analysis(self, symbol: str = "") -> TechnicalAnalysisDTO:
        """Create empty technical analysis DTO."""
        return TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=None,
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
        )

    def _calculate_technical_indicators(
        self, market_data: Any
    ) -> dict[str, float | None]:
        """
        Calculate various technical indicators from market data.

        Args:
            market_data: Market data entity with price history

        Returns:
            Dictionary of calculated indicators
        """
        try:
            # Extract price and volume data safely
            if not hasattr(market_data, "price_data") or not market_data.price_data:
                return {}

            prices = []
            volumes = []

            for price_point in market_data.price_data:
                try:
                    close_price = float(getattr(price_point, "close", 0))
                    volume = float(getattr(price_point, "volume", 0))
                    if close_price > 0:
                        prices.append(close_price)
                        volumes.append(volume)
                except (ValueError, AttributeError):
                    continue

            if len(prices) < 14:  # Minimum data points for RSI
                return {}

            # Calculate indicators
            rsi = self._calculate_rsi(prices)
            macd = self._calculate_macd(prices)
            bollinger_position = self._calculate_bollinger_position(prices)
            sma_20 = self._calculate_sma(prices, 20)
            sma_50 = self._calculate_sma(prices, 50)
            volume_trend = self._calculate_volume_trend(volumes)

            return {
                "rsi": rsi,
                "macd": macd,
                "bollinger_position": bollinger_position,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "volume_trend": volume_trend,
                "support_level": min(prices[-20:]) if len(prices) >= 20 else None,
                "resistance_level": max(prices[-20:]) if len(prices) >= 20 else None,
            }

        except Exception as e:
            print(f"Error calculating technical indicators: {e}")
            return {}

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float | None:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return None

        try:
            gains = []
            losses = []

            for i in range(1, len(prices)):
                change = prices[i] - prices[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(abs(change))

            if len(gains) < period:
                return None

            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return round(rsi, 2)

        except (ZeroDivisionError, ValueError):
            return None

    def _calculate_macd(self, prices: list[float]) -> float | None:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < 26:
            return None

        try:
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)

            if ema_12 is None or ema_26 is None:
                return None

            return round(ema_12 - ema_26, 4)

        except (ValueError, TypeError):
            return None

    def _calculate_ema(self, prices: list[float], period: int) -> float | None:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None

        try:
            multiplier = 2 / (period + 1)
            ema = sum(prices[:period]) / period

            for price in prices[period:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))

            return ema

        except (ValueError, TypeError):
            return None

    def _calculate_sma(self, prices: list[float], period: int) -> float | None:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None

        try:
            return sum(prices[-period:]) / period
        except (ValueError, TypeError):
            return None

    def _calculate_bollinger_position(
        self, prices: list[float], period: int = 20
    ) -> float | None:
        """Calculate position within Bollinger Bands."""
        if len(prices) < period:
            return None

        try:
            recent_prices = prices[-period:]
            sma = sum(recent_prices) / period

            variance = sum((price - sma) ** 2 for price in recent_prices) / period
            std_dev = variance**0.5

            upper_band = sma + (2 * std_dev)
            lower_band = sma - (2 * std_dev)
            current_price = prices[-1]

            if upper_band == lower_band:
                return 0.5

            position = (current_price - lower_band) / (upper_band - lower_band)
            return round(max(0, min(1, position)), 3)

        except (ValueError, TypeError, ZeroDivisionError):
            return None

    def _calculate_volume_trend(
        self, volumes: list[float], period: int = 10
    ) -> float | None:
        """Calculate volume trend indicator."""
        if len(volumes) < period * 2:
            return None

        try:
            recent_avg = sum(volumes[-period:]) / period
            older_avg = sum(volumes[-period * 2 : -period]) / period

            if older_avg == 0:
                return 0.0

            trend = (recent_avg - older_avg) / older_avg
            return round(trend, 3)

        except (ValueError, TypeError, ZeroDivisionError):
            return None
