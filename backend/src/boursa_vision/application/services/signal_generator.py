"""
Signal Generator Application Service
===================================

Application service that generates trading signals based on
technical analysis and market conditions.
"""

from datetime import datetime

from ..dtos import SignalDTO, TechnicalAnalysisDTO
from .technical_analyzer import TechnicalAnalyzer


class SignalGenerator:
    """
    Application service for generating trading signals.

    Uses technical analysis and market conditions to generate
    actionable trading signals with confidence scores.
    """

    def __init__(self, technical_analyzer: TechnicalAnalyzer) -> None:
        """Initialize signal generator with technical analyzer."""
        self._technical_analyzer = technical_analyzer

    async def generate_signal(self, symbol: str) -> SignalDTO:
        """
        Generate a trading signal for a given symbol.

        Args:
            symbol: Stock symbol to analyze

        Returns:
            SignalDTO with trading recommendation
        """
        try:
            # Get technical analysis
            analysis = await self._technical_analyzer.analyze_investment(symbol)

            # Determine signal action and confidence
            action, confidence, reason = self._determine_signal_action(analysis)

            # Create signal metadata
            metadata = self._create_signal_metadata(analysis)

            return SignalDTO(
                symbol=symbol,
                action=action,
                confidence=confidence,
                price=analysis.sma_20 if analysis.sma_20 else None,
                target_price=analysis.resistance_level if action == "BUY" else analysis.support_level,
                stop_loss=analysis.support_level if action == "BUY" else analysis.resistance_level,
                reason=reason,
                metadata=metadata,
                timestamp=datetime.now()
            )
        except Exception as e:
            return SignalDTO(
                symbol=symbol,
                action="ERROR",
                confidence=0.0,
                price=None,
                target_price=None,
                stop_loss=None,
                reason=f"Error generating signal: {e!s}",
                metadata={},
                timestamp=datetime.now()
            )

    async def generate_signals_for_portfolio(
        self, symbols: list[str]
    ) -> dict[str, SignalDTO]:
        """
        Generate signals for multiple symbols in a portfolio.

        Args:
            symbols: List of stock symbols to analyze

        Returns:
            Dictionary mapping symbols to their signals
        """
        if not symbols:
            return {}

        signals = {}
        for symbol in symbols:
            try:
                signals[symbol] = await self.generate_signal(symbol)
            except Exception as e:
                signals[symbol] = SignalDTO(
                    symbol=symbol,
                    action="ERROR",
                    confidence=0.0,
                    price=None,
                    target_price=None,
                    stop_loss=None,
                    reason=f"Error generating signal: {e!s}",
                    metadata={},
                    timestamp=datetime.now()
                )

        return signals

    def _determine_signal_action(
        self, analysis: TechnicalAnalysisDTO
    ) -> tuple[str, float, str]:
        """
        Determine signal action based on technical analysis.

        Args:
            analysis: Technical analysis data

        Returns:
            Tuple of (action, confidence, reason)
        """
        # Check if we have sufficient data
        indicators = [
            analysis.rsi,
            analysis.macd,
            analysis.bollinger_position,
            analysis.sma_20,
            analysis.sma_50,
        ]

        if all(indicator is None for indicator in indicators):
            return "HOLD", 0.0, "Insufficient data for analysis"

        buy_signals = 0
        sell_signals = 0
        signal_strength = 0.0
        reasons = []

        # RSI analysis
        if analysis.rsi is not None:
            if analysis.rsi < 30:  # Oversold
                buy_signals += 1
                signal_strength += 0.2
                reasons.append("RSI oversold")
            elif analysis.rsi > 70:  # Overbought
                sell_signals += 1
                signal_strength += 0.2
                reasons.append("RSI overbought")

        # MACD analysis
        if analysis.macd is not None:
            if analysis.macd > 0.1:  # Strong positive MACD
                buy_signals += 1
                signal_strength += 0.15
                reasons.append("MACD bullish")
            elif analysis.macd < -0.1:  # Strong negative MACD
                sell_signals += 1
                signal_strength += 0.15
                reasons.append("MACD bearish")

        # Bollinger Bands analysis
        if analysis.bollinger_position is not None:
            if analysis.bollinger_position < 0.2:  # Near lower band
                buy_signals += 1
                signal_strength += 0.1
                reasons.append("Price near lower Bollinger band")
            elif analysis.bollinger_position > 0.8:  # Near upper band
                sell_signals += 1
                signal_strength += 0.1
                reasons.append("Price near upper Bollinger band")

        # SMA trend analysis
        if analysis.sma_20 is not None and analysis.sma_50 is not None:
            sma_diff = (analysis.sma_20 - analysis.sma_50) / analysis.sma_50
            if sma_diff > 0.02:  # 20-day SMA significantly above 50-day
                buy_signals += 1
                signal_strength += 0.15
                reasons.append("SMA trend bullish")
            elif sma_diff < -0.02:  # 20-day SMA significantly below 50-day
                sell_signals += 1
                signal_strength += 0.15
                reasons.append("SMA trend bearish")

        # Volume trend
        if analysis.volume_trend is not None and analysis.volume_trend > 0.3:
            signal_strength += 0.1  # Volume confirmation

        # Determine final action
        # Single signal is enough, multiple signals increase confidence
        if buy_signals > sell_signals and buy_signals >= 1:
            action = "BUY"
            confidence = min(signal_strength, 0.9)
            reason = f"Buy signal: {', '.join(reasons)}"
        elif sell_signals > buy_signals and sell_signals >= 1:
            action = "SELL"
            confidence = min(signal_strength, 0.9)
            reason = f"Sell signal: {', '.join(reasons)}"
        else:
            action = "HOLD"
            confidence = 0.0 if not reasons else min(signal_strength * 0.5, 0.5)
            reason = f"Neutral signal: {'Mixed signals' if reasons else 'No strong signals'}"

        return action, confidence, reason

    def _create_signal_metadata(
        self, analysis: TechnicalAnalysisDTO
    ) -> dict[str, str | float | int]:
        """Create metadata for the signal."""
        return {
            "rsi": analysis.rsi or 0.0,
            "macd": analysis.macd or 0.0,
            "bollinger_position": analysis.bollinger_position or 0.0,
            "sma_20": analysis.sma_20 or 0.0,
            "sma_50": analysis.sma_50 or 0.0,
            "volume_trend": analysis.volume_trend or 0.0,
            "analysis_date": analysis.analysis_date.isoformat() if analysis.analysis_date else "",
        }
