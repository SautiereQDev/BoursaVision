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
        Generate a trading signal for a specific investment.

        Args:
            symbol: Investment symbol to analyze

        Returns:
            SignalDTO: Generated trading signal
        """
        try:
            # Get technical analysis
            analysis = await self._technical_analyzer.analyze_investment(symbol)

            # Generate signal based on analysis
            action, confidence, reasoning = self._determine_signal_action(analysis)

            return SignalDTO(
                symbol=symbol,
                action=action,
                confidence=confidence,
                price=None,  # Would be populated with current price
                target_price=None,  # Would be calculated based on analysis
                stop_loss=None,  # Would be calculated based on risk management
                reason=reasoning,
                metadata=self._create_signal_metadata(analysis),
                timestamp=datetime.now(),
            )

        except Exception as e:
            # Return neutral signal on error
            return SignalDTO(
                symbol=symbol,
                action="HOLD",
                confidence=0.0,
                price=None,
                target_price=None,
                stop_loss=None,
                reason=f"Error generating signal: {e!s}",
                metadata={},
                timestamp=datetime.now(),
            )

    async def generate_signals_for_portfolio(
        self, symbols: list[str]
    ) -> dict[str, SignalDTO]:
        """
        Generate trading signals for multiple investments.

        Args:
            symbols: List of investment symbols to analyze

        Returns:
            Dictionary mapping symbols to trading signals (excludes failed analyses)
        """
        signals = {}

        for symbol in symbols:
            try:
                signal = await self.generate_signal(symbol)
                # Only add successful signals (exclude error signals)
                if not signal.reason.startswith("Error:"):
                    signals[symbol] = signal
            except Exception as e:
                # Log error but exclude from results for portfolio analysis
                print(f"Failed to generate signal for {symbol}: {e}")
                continue

        return signals

    def _determine_signal_action(
        self, analysis: TechnicalAnalysisDTO
    ) -> tuple[str, float, str]:
        """
        Determine signal action based on technical analysis.

        Args:
            analysis: Technical analysis data

        Returns:
            Tuple of (action, confidence, reasoning)
        """
        signals = []
        reasons = []

        # RSI Analysis
        if analysis.rsi is not None:
            if analysis.rsi <= 30:  # Include exactly 30 as oversold
                signals.append(("BUY", 0.7))
                reasons.append("RSI oversold")
                print(f"DEBUG: RSI {analysis.rsi} -> BUY (oversold)")
            elif analysis.rsi >= 70:  # Include exactly 70 as overbought
                signals.append(("SELL", 0.7))
                reasons.append("RSI overbought")
                print(f"DEBUG: RSI {analysis.rsi} -> SELL (overbought)")
            else:
                signals.append(("HOLD", 0.3))
                reasons.append("RSI neutral")
                print(f"DEBUG: RSI {analysis.rsi} -> HOLD (neutral)")

        # MACD Analysis
        if analysis.macd is not None:
            if analysis.macd > 0.1:  # Positive threshold for significance
                signals.append(("BUY", 0.6))
                reasons.append("MACD positive")
            elif analysis.macd < -0.1:  # Negative threshold for significance
                signals.append(("SELL", 0.6))
                reasons.append("MACD negative")
            else:
                signals.append(("HOLD", 0.3))
                reasons.append("MACD neutral")

        # Moving Average Analysis
        if analysis.sma_20 is not None and analysis.sma_50 is not None:
            ma_diff_percent = abs(analysis.sma_20 - analysis.sma_50) / analysis.sma_50
            if ma_diff_percent > 0.01:  # 1% difference threshold
                if analysis.sma_20 > analysis.sma_50:
                    signals.append(("BUY", 0.5))
                    reasons.append("Short MA above long MA")
                else:
                    signals.append(("SELL", 0.5))
                    reasons.append("Short MA below long MA")
            else:
                signals.append(("HOLD", 0.3))
                reasons.append("Moving averages converged")

        # Bollinger Bands Analysis
        if analysis.bollinger_position is not None:
            if analysis.bollinger_position < 0.2:
                signals.append(("BUY", 0.6))
                reasons.append("Near lower Bollinger band")
            elif analysis.bollinger_position > 0.8:
                signals.append(("SELL", 0.6))
                reasons.append("Near upper Bollinger band")

        # Volume Analysis
        if (
            analysis.volume_trend is not None
            and analysis.volume_trend > 0.2
            and signals
            and signals[-1][0] in ["BUY", "SELL"]
        ):
            # Increase confidence if volume supports the trend
            last_signal = signals[-1]
            signals[-1] = (last_signal[0], min(1.0, last_signal[1] + 0.1))
            reasons.append("Strong volume trend")

        # Aggregate signals
        if not signals:
            return "HOLD", 0.0, "Insufficient data for analysis"

        # Count signal types
        buy_count = sum(1 for s in signals if s[0] == "BUY")
        sell_count = sum(1 for s in signals if s[0] == "SELL")

        if buy_count > sell_count:
            avg_confidence = sum(s[1] for s in signals if s[0] == "BUY") / buy_count
            action = "BUY"
        elif sell_count > buy_count:
            avg_confidence = sum(s[1] for s in signals if s[0] == "SELL") / sell_count
            action = "SELL"
        else:
            action = "HOLD"
            avg_confidence = 0.3

        reasoning = "; ".join(reasons) if reasons else "Technical analysis complete"

        return action, round(avg_confidence, 2), reasoning

    def _create_signal_metadata(
        self, analysis: TechnicalAnalysisDTO
    ) -> dict[str, str | float | int]:
        """Create metadata for the signal."""
        metadata = {}

        if analysis.rsi is not None:
            metadata["rsi"] = analysis.rsi
        if analysis.macd is not None:
            metadata["macd"] = analysis.macd
        if analysis.bollinger_position is not None:
            metadata["bollinger_position"] = analysis.bollinger_position
        if analysis.volume_trend is not None:
            metadata["volume_trend"] = analysis.volume_trend

        metadata["analysis_timestamp"] = datetime.now().isoformat()

        return metadata
