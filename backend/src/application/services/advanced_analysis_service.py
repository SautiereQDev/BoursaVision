"""Advanced Investment Analysis Service with comprehensive scoring system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Protocol
import math
import statistics
import yfinance as yf
import pandas as pd
import numpy as np

from src.domain.entities.investment import Investment, TechnicalData, FundamentalData
from src.domain.value_objects.money import Money


class AnalysisStrategy(ABC):
    """Strategy pattern for different analysis approaches."""
    
    @abstractmethod
    def calculate_score(self, investment: Investment, market_data: Dict[str, Any]) -> float:
        """Calculate score for this strategy (0-100)."""
        pass
    
    @abstractmethod
    def get_insights(self, investment: Investment, market_data: Dict[str, Any]) -> List[str]:
        """Get human-readable insights from this analysis."""
        pass


@dataclass
class AnalysisWeights:
    """Configurable weights for different analysis dimensions."""
    technical: float = 0.25
    fundamental: float = 0.30
    momentum: float = 0.15
    value: float = 0.15
    growth: float = 0.10
    quality: float = 0.05
    
    def __post_init__(self):
        total = (self.technical + self.fundamental + self.momentum + 
                self.value + self.growth + self.quality)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class TechnicalAnalysisStrategy(AnalysisStrategy):
    """Advanced technical analysis with multiple indicators."""
    
    def calculate_score(self, investment: Investment, market_data: Dict[str, Any]) -> float:
        """Calculate technical score based on multiple indicators."""
        try:
            hist_data = market_data.get('history')
            if hist_data is None or len(hist_data) < 50:
                return 50.0  # Neutral score if insufficient data
            
            scores = []
            
            # RSI Score (0-100)
            rsi_score = self._calculate_rsi_score(hist_data)
            scores.append(('RSI', rsi_score, 0.25))
            
            # MACD Score
            macd_score = self._calculate_macd_score(hist_data)
            scores.append(('MACD', macd_score, 0.25))
            
            # Moving Averages Score
            ma_score = self._calculate_moving_average_score(hist_data)
            scores.append(('Moving Averages', ma_score, 0.20))
            
            # Bollinger Bands Score
            bb_score = self._calculate_bollinger_score(hist_data)
            scores.append(('Bollinger Bands', bb_score, 0.15))
            
            # Volume Analysis Score
            volume_score = self._calculate_volume_score(hist_data)
            scores.append(('Volume', volume_score, 0.15))
            
            # Calculate weighted average
            weighted_sum = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            
            return weighted_sum / total_weight if total_weight > 0 else 50.0
            
        except Exception as e:
            print(f"Error in technical analysis: {e}")
            return 50.0
    
    def _calculate_rsi_score(self, hist_data: pd.DataFrame) -> float:
        """Calculate RSI-based score."""
        try:
            close_prices = hist_data['Close']
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            # Score based on RSI value
            if 30 <= current_rsi <= 70:  # Neutral zone
                return 60.0 + (50 - abs(current_rsi - 50)) * 0.8
            elif 20 <= current_rsi < 30:  # Oversold (potential buy)
                return 80.0 + (30 - current_rsi) * 2
            elif 70 < current_rsi <= 80:  # Overbought (potential sell)
                return 40.0 - (current_rsi - 70) * 2
            else:  # Extreme levels
                return 20.0
                
        except Exception:
            return 50.0
    
    def _calculate_macd_score(self, hist_data: pd.DataFrame) -> float:
        """Calculate MACD-based score."""
        try:
            close_prices = hist_data['Close']
            ema_12 = close_prices.ewm(span=12).mean()
            ema_26 = close_prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            current_macd = macd.iloc[-1]
            current_signal = signal.iloc[-1]
            current_histogram = histogram.iloc[-1]
            
            score = 50.0
            
            # MACD above signal line is bullish
            if current_macd > current_signal:
                score += 25.0
            else:
                score -= 15.0
            
            # Histogram growing is bullish
            if len(histogram) > 1 and current_histogram > histogram.iloc[-2]:
                score += 15.0
            else:
                score -= 10.0
            
            return max(0.0, min(100.0, score))
            
        except Exception:
            return 50.0
    
    def _calculate_moving_average_score(self, hist_data: pd.DataFrame) -> float:
        """Calculate moving averages score."""
        try:
            close_prices = hist_data['Close']
            current_price = close_prices.iloc[-1]
            
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            sma_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else sma_50
            
            score = 50.0
            
            # Price above moving averages is bullish
            if current_price > sma_20:
                score += 20.0
            if current_price > sma_50:
                score += 15.0
            if current_price > sma_200:
                score += 15.0
            
            # Moving average trend
            if sma_20 > sma_50 > sma_200:
                score += 20.0  # Golden cross formation
            elif sma_20 < sma_50 < sma_200:
                score -= 20.0  # Death cross formation
            
            return max(0.0, min(100.0, score))
            
        except Exception:
            return 50.0
    
    def _calculate_bollinger_score(self, hist_data: pd.DataFrame) -> float:
        """Calculate Bollinger Bands score."""
        try:
            close_prices = hist_data['Close']
            sma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()
            
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            current_price = close_prices.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            
            # Position within bands
            band_width = current_upper - current_lower
            if band_width == 0:
                return 50.0
            
            position = (current_price - current_lower) / band_width
            
            # Score based on position
            if 0.2 <= position <= 0.8:  # Normal range
                return 70.0
            elif position < 0.2:  # Near lower band (oversold)
                return 85.0
            elif position > 0.8:  # Near upper band (overbought)
                return 35.0
            else:
                return 50.0
                
        except Exception:
            return 50.0
    
    def _calculate_volume_score(self, hist_data: pd.DataFrame) -> float:
        """Calculate volume-based score."""
        try:
            volumes = hist_data['Volume']
            if len(volumes) < 20:
                return 50.0
            
            avg_volume = volumes.rolling(window=20).mean().iloc[-1]
            current_volume = volumes.iloc[-1]
            
            # Volume trend over last 5 days
            recent_volumes = volumes.tail(5)
            volume_trend = recent_volumes.pct_change().mean()
            
            score = 50.0
            
            # High volume is generally bullish
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            if volume_ratio > 1.5:
                score += 25.0
            elif volume_ratio > 1.2:
                score += 15.0
            elif volume_ratio < 0.5:
                score -= 15.0
            
            # Volume trend
            if volume_trend > 0.05:  # Increasing volume
                score += 15.0
            elif volume_trend < -0.05:  # Decreasing volume
                score -= 10.0
            
            return max(0.0, min(100.0, score))
            
        except Exception:
            return 50.0
    
    def get_insights(self, investment: Investment, market_data: Dict[str, Any]) -> List[str]:
        """Generate technical analysis insights."""
        insights = []
        
        try:
            hist_data = market_data.get('history')
            if hist_data is None or len(hist_data) < 20:
                return ["Insufficient historical data for technical analysis"]
            
            close_prices = hist_data['Close']
            current_price = close_prices.iloc[-1]
            
            # RSI insights
            if len(close_prices) >= 14:
                delta = close_prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                if current_rsi < 30:
                    insights.append(f"RSI ({current_rsi:.1f}) indicates oversold conditions - potential buying opportunity")
                elif current_rsi > 70:
                    insights.append(f"RSI ({current_rsi:.1f}) indicates overbought conditions - consider taking profits")
            
            # Moving average insights
            if len(close_prices) >= 50:
                sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
                sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
                
                if current_price > sma_20 > sma_50:
                    insights.append("Price is above key moving averages - bullish trend")
                elif current_price < sma_20 < sma_50:
                    insights.append("Price is below key moving averages - bearish trend")
            
            # Volume insights
            volumes = hist_data['Volume']
            if len(volumes) >= 20:
                avg_volume = volumes.rolling(window=20).mean().iloc[-1]
                current_volume = volumes.iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                if volume_ratio > 2.0:
                    insights.append("Exceptionally high volume detected - significant market interest")
                elif volume_ratio > 1.5:
                    insights.append("Above-average volume confirms price movement")
                
        except Exception as e:
            insights.append(f"Error generating technical insights: {e}")
        
        return insights


class FundamentalAnalysisStrategy(AnalysisStrategy):
    """Advanced fundamental analysis with comprehensive metrics."""
    
    def calculate_score(self, investment: Investment, market_data: Dict[str, Any]) -> float:
        """Calculate fundamental score based on financial metrics."""
        try:
            info = market_data.get('info', {})
            if not info:
                return 50.0
            
            scores = []
            
            # Valuation metrics
            pe_score = self._calculate_pe_score(info)
            scores.append(('P/E Ratio', pe_score, 0.20))
            
            # Profitability metrics
            roe_score = self._calculate_roe_score(info)
            scores.append(('ROE', roe_score, 0.25))
            
            # Growth metrics
            growth_score = self._calculate_growth_score(info)
            scores.append(('Growth', growth_score, 0.20))
            
            # Financial health
            debt_score = self._calculate_debt_score(info)
            scores.append(('Financial Health', debt_score, 0.15))
            
            # Profitability margins
            margin_score = self._calculate_margin_score(info)
            scores.append(('Margins', margin_score, 0.10))
            
            # Dividend score
            dividend_score = self._calculate_dividend_score(info)
            scores.append(('Dividend', dividend_score, 0.10))
            
            # Calculate weighted average
            weighted_sum = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            
            return weighted_sum / total_weight if total_weight > 0 else 50.0
            
        except Exception as e:
            print(f"Error in fundamental analysis: {e}")
            return 50.0
    
    def _calculate_pe_score(self, info: Dict[str, Any]) -> float:
        """Calculate P/E ratio score."""
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')
        if pe_ratio is None or pe_ratio <= 0:
            return 50.0
        
        # Optimal P/E range is 10-20
        if 10 <= pe_ratio <= 20:
            return 85.0
        elif 5 <= pe_ratio < 10:
            return 75.0
        elif 20 < pe_ratio <= 30:
            return 65.0
        elif 30 < pe_ratio <= 50:
            return 40.0
        else:
            return 20.0
    
    def _calculate_roe_score(self, info: Dict[str, Any]) -> float:
        """Calculate Return on Equity score."""
        roe = info.get('returnOnEquity')
        if roe is None:
            return 50.0
        
        roe_percent = roe * 100 if roe < 1 else roe
        
        if roe_percent >= 20:
            return 90.0
        elif roe_percent >= 15:
            return 80.0
        elif roe_percent >= 10:
            return 70.0
        elif roe_percent >= 5:
            return 50.0
        else:
            return 30.0
    
    def _calculate_growth_score(self, info: Dict[str, Any]) -> float:
        """Calculate growth score based on revenue and earnings growth."""
        revenue_growth = info.get('revenueGrowth')
        earnings_growth = info.get('earningsGrowth')
        
        scores = []
        
        if revenue_growth is not None:
            rev_growth_percent = revenue_growth * 100 if revenue_growth < 1 else revenue_growth
            if rev_growth_percent >= 20:
                scores.append(90.0)
            elif rev_growth_percent >= 10:
                scores.append(80.0)
            elif rev_growth_percent >= 5:
                scores.append(70.0)
            elif rev_growth_percent >= 0:
                scores.append(60.0)
            else:
                scores.append(30.0)
        
        if earnings_growth is not None:
            earn_growth_percent = earnings_growth * 100 if earnings_growth < 1 else earnings_growth
            if earn_growth_percent >= 25:
                scores.append(90.0)
            elif earn_growth_percent >= 15:
                scores.append(80.0)
            elif earn_growth_percent >= 10:
                scores.append(70.0)
            elif earn_growth_percent >= 0:
                scores.append(60.0)
            else:
                scores.append(30.0)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calculate_debt_score(self, info: Dict[str, Any]) -> float:
        """Calculate debt-to-equity score."""
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        
        scores = []
        
        if debt_to_equity is not None:
            if debt_to_equity <= 0.3:
                scores.append(90.0)
            elif debt_to_equity <= 0.6:
                scores.append(80.0)
            elif debt_to_equity <= 1.0:
                scores.append(70.0)
            elif debt_to_equity <= 2.0:
                scores.append(50.0)
            else:
                scores.append(30.0)
        
        if current_ratio is not None:
            if current_ratio >= 2.0:
                scores.append(90.0)
            elif current_ratio >= 1.5:
                scores.append(80.0)
            elif current_ratio >= 1.0:
                scores.append(60.0)
            else:
                scores.append(40.0)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calculate_margin_score(self, info: Dict[str, Any]) -> float:
        """Calculate profitability margins score."""
        gross_margin = info.get('grossMargins')
        operating_margin = info.get('operatingMargins')
        profit_margin = info.get('profitMargins')
        
        scores = []
        
        for margin_type, margin in [('gross', gross_margin), ('operating', operating_margin), ('profit', profit_margin)]:
            if margin is not None:
                margin_percent = margin * 100 if margin < 1 else margin
                if margin_percent >= 30:
                    scores.append(90.0)
                elif margin_percent >= 20:
                    scores.append(80.0)
                elif margin_percent >= 10:
                    scores.append(70.0)
                elif margin_percent >= 5:
                    scores.append(60.0)
                else:
                    scores.append(40.0)
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _calculate_dividend_score(self, info: Dict[str, Any]) -> float:
        """Calculate dividend score."""
        dividend_yield = info.get('dividendYield')
        payout_ratio = info.get('payoutRatio')
        
        if dividend_yield is None:
            return 50.0  # Neutral for non-dividend stocks
        
        yield_percent = dividend_yield * 100 if dividend_yield < 1 else dividend_yield
        
        score = 50.0
        
        # Dividend yield score
        if 2 <= yield_percent <= 6:
            score += 25.0
        elif 1 <= yield_percent < 2 or 6 < yield_percent <= 8:
            score += 15.0
        elif yield_percent > 10:
            score -= 20.0  # Suspiciously high yield
        
        # Payout ratio score
        if payout_ratio is not None:
            payout_percent = payout_ratio * 100 if payout_ratio < 1 else payout_ratio
            if 30 <= payout_percent <= 60:
                score += 15.0
            elif payout_percent > 80:
                score -= 15.0  # Unsustainable payout
        
        return max(0.0, min(100.0, score))
    
    def get_insights(self, investment: Investment, market_data: Dict[str, Any]) -> List[str]:
        """Generate fundamental analysis insights."""
        insights = []
        
        try:
            info = market_data.get('info', {})
            if not info:
                return ["No fundamental data available"]
            
            # P/E insights
            pe_ratio = info.get('trailingPE') or info.get('forwardPE')
            if pe_ratio:
                if pe_ratio < 15:
                    insights.append(f"Low P/E ratio ({pe_ratio:.1f}) suggests potentially undervalued stock")
                elif pe_ratio > 30:
                    insights.append(f"High P/E ratio ({pe_ratio:.1f}) indicates high growth expectations or overvaluation")
            
            # ROE insights
            roe = info.get('returnOnEquity')
            if roe:
                roe_percent = roe * 100 if roe < 1 else roe
                if roe_percent > 15:
                    insights.append(f"Strong ROE ({roe_percent:.1f}%) indicates efficient use of shareholder equity")
                elif roe_percent < 10:
                    insights.append(f"Low ROE ({roe_percent:.1f}%) may indicate operational inefficiencies")
            
            # Growth insights
            revenue_growth = info.get('revenueGrowth')
            if revenue_growth:
                growth_percent = revenue_growth * 100 if revenue_growth < 1 else revenue_growth
                if growth_percent > 10:
                    insights.append(f"Strong revenue growth ({growth_percent:.1f}%) shows business expansion")
                elif growth_percent < 0:
                    insights.append(f"Negative revenue growth ({growth_percent:.1f}%) indicates declining business")
            
            # Debt insights
            debt_to_equity = info.get('debtToEquity')
            if debt_to_equity:
                if debt_to_equity < 0.5:
                    insights.append(f"Low debt-to-equity ({debt_to_equity:.2f}) indicates strong financial position")
                elif debt_to_equity > 1.5:
                    insights.append(f"High debt-to-equity ({debt_to_equity:.2f}) may indicate financial risk")
            
            # Dividend insights
            dividend_yield = info.get('dividendYield')
            if dividend_yield:
                yield_percent = dividend_yield * 100 if dividend_yield < 1 else dividend_yield
                if yield_percent > 4:
                    insights.append(f"Attractive dividend yield ({yield_percent:.1f}%) for income investors")
                
        except Exception as e:
            insights.append(f"Error generating fundamental insights: {e}")
        
        return insights


class MomentumAnalysisStrategy(AnalysisStrategy):
    """Momentum analysis based on price movements and trends."""
    
    def calculate_score(self, investment: Investment, market_data: Dict[str, Any]) -> float:
        """Calculate momentum score."""
        try:
            hist_data = market_data.get('history')
            if hist_data is None or len(hist_data) < 30:
                return 50.0
            
            close_prices = hist_data['Close']
            current_price = close_prices.iloc[-1]
            
            scores = []
            
            # Price momentum over different periods
            periods = [5, 10, 20, 60]  # days
            weights = [0.4, 0.3, 0.2, 0.1]
            
            for period, weight in zip(periods, weights):
                if len(close_prices) > period:
                    past_price = close_prices.iloc[-(period+1)]
                    return_pct = ((current_price - past_price) / past_price) * 100
                    
                    # Score based on return magnitude
                    if return_pct > 10:
                        score = 90.0
                    elif return_pct > 5:
                        score = 80.0
                    elif return_pct > 2:
                        score = 70.0
                    elif return_pct > -2:
                        score = 60.0
                    elif return_pct > -5:
                        score = 40.0
                    else:
                        score = 20.0
                    
                    scores.append((f'{period}d momentum', score, weight))
            
            # Trend consistency score
            if len(close_prices) >= 20:
                recent_prices = close_prices.tail(20)
                trend_score = self._calculate_trend_consistency(recent_prices)
                scores.append(('Trend Consistency', trend_score, 0.2))
            
            # Calculate weighted average
            weighted_sum = sum(score * weight for _, score, weight in scores)
            total_weight = sum(weight for _, _, weight in scores)
            
            return weighted_sum / total_weight if total_weight > 0 else 50.0
            
        except Exception as e:
            print(f"Error in momentum analysis: {e}")
            return 50.0
    
    def _calculate_trend_consistency(self, prices: pd.Series) -> float:
        """Calculate trend consistency score."""
        try:
            # Calculate daily returns
            returns = prices.pct_change().dropna()
            if len(returns) == 0:
                return 50.0
            
            # Count positive vs negative days
            positive_days = (returns > 0).sum()
            total_days = len(returns)
            positive_ratio = positive_days / total_days
            
            # Score based on consistency
            if positive_ratio >= 0.7:
                return 90.0
            elif positive_ratio >= 0.6:
                return 80.0
            elif positive_ratio >= 0.5:
                return 70.0
            elif positive_ratio >= 0.4:
                return 60.0
            else:
                return 40.0
                
        except Exception:
            return 50.0
    
    def get_insights(self, investment: Investment, market_data: Dict[str, Any]) -> List[str]:
        """Generate momentum insights."""
        insights = []
        
        try:
            hist_data = market_data.get('history')
            if hist_data is None or len(hist_data) < 10:
                return ["Insufficient data for momentum analysis"]
            
            close_prices = hist_data['Close']
            current_price = close_prices.iloc[-1]
            
            # Calculate returns over different periods
            periods = [('1 week', 5), ('1 month', 20), ('3 months', 60)]
            
            for period_name, days in periods:
                if len(close_prices) > days:
                    past_price = close_prices.iloc[-(days+1)]
                    return_pct = ((current_price - past_price) / past_price) * 100
                    
                    if return_pct > 10:
                        insights.append(f"Strong {period_name} momentum: +{return_pct:.1f}%")
                    elif return_pct < -10:
                        insights.append(f"Negative {period_name} momentum: {return_pct:.1f}%")
            
            # Trend analysis
            if len(close_prices) >= 20:
                recent_prices = close_prices.tail(20)
                returns = recent_prices.pct_change().dropna()
                positive_days = (returns > 0).sum()
                total_days = len(returns)
                positive_ratio = positive_days / total_days
                
                if positive_ratio >= 0.7:
                    insights.append(f"Consistent uptrend: {positive_ratio:.1%} positive days in last 20 sessions")
                elif positive_ratio <= 0.3:
                    insights.append(f"Consistent downtrend: {positive_ratio:.1%} positive days in last 20 sessions")
                
        except Exception as e:
            insights.append(f"Error generating momentum insights: {e}")
        
        return insights


@dataclass
class ComprehensiveAnalysisResult:
    """Comprehensive analysis result with all dimensions."""
    investment_symbol: str
    overall_score: float
    risk_level: str
    recommendation: str
    confidence: float
    
    technical_score: float
    fundamental_score: float
    momentum_score: float
    
    strengths: List[str]
    weaknesses: List[str]
    insights: List[str]
    
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


class AdvancedInvestmentAnalyzer:
    """Advanced investment analyzer using multiple strategies."""
    
    def __init__(self, weights: Optional[AnalysisWeights] = None):
        self.weights = weights or AnalysisWeights()
        self.technical_strategy = TechnicalAnalysisStrategy()
        self.fundamental_strategy = FundamentalAnalysisStrategy()
        self.momentum_strategy = MomentumAnalysisStrategy()
    
    def analyze_investment(self, symbol: str) -> ComprehensiveAnalysisResult:
        """Perform comprehensive analysis of an investment."""
        try:
            # Fetch data from YFinance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1y")
            
            if hist.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            market_data = {
                'info': info,
                'history': hist
            }
            
            # Calculate scores for each strategy
            technical_score = self.technical_strategy.calculate_score(None, market_data)
            fundamental_score = self.fundamental_strategy.calculate_score(None, market_data)
            momentum_score = self.momentum_strategy.calculate_score(None, market_data)
            
            # Calculate weighted overall score
            overall_score = (
                technical_score * self.weights.technical +
                fundamental_score * self.weights.fundamental +
                momentum_score * self.weights.momentum
            )
            
            # Determine recommendation and risk level
            recommendation = self._determine_recommendation(overall_score, technical_score, fundamental_score)
            risk_level = self._assess_risk_level(info, hist)
            confidence = self._calculate_confidence(info, hist)
            
            # Generate insights
            insights = []
            insights.extend(self.technical_strategy.get_insights(None, market_data))
            insights.extend(self.fundamental_strategy.get_insights(None, market_data))
            insights.extend(self.momentum_strategy.get_insights(None, market_data))
            
            # Identify strengths and weaknesses
            strengths, weaknesses = self._identify_strengths_weaknesses(
                technical_score, fundamental_score, momentum_score, info
            )
            
            # Calculate target price and stop loss
            target_price, stop_loss = self._calculate_price_targets(info, hist, overall_score)
            
            return ComprehensiveAnalysisResult(
                investment_symbol=symbol,
                overall_score=overall_score,
                risk_level=risk_level,
                recommendation=recommendation,
                confidence=confidence,
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                momentum_score=momentum_score,
                strengths=strengths,
                weaknesses=weaknesses,
                insights=insights,
                target_price=target_price,
                stop_loss=stop_loss
            )
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            # Return neutral analysis in case of error
            return ComprehensiveAnalysisResult(
                investment_symbol=symbol,
                overall_score=50.0,
                risk_level="UNKNOWN",
                recommendation="HOLD",
                confidence=0.0,
                technical_score=50.0,
                fundamental_score=50.0,
                momentum_score=50.0,
                strengths=[],
                weaknesses=["Analysis failed due to data issues"],
                insights=[f"Error: {str(e)}"]
            )
    
    def _determine_recommendation(self, overall_score: float, technical_score: float, fundamental_score: float) -> str:
        """Determine buy/hold/sell recommendation."""
        if overall_score >= 75 and technical_score >= 70 and fundamental_score >= 70:
            return "STRONG_BUY"
        elif overall_score >= 65:
            return "BUY"
        elif overall_score >= 55:
            return "HOLD"
        elif overall_score >= 45:
            return "WEAK_HOLD"
        else:
            return "SELL"
    
    def _assess_risk_level(self, info: Dict[str, Any], hist: pd.DataFrame) -> str:
        """Assess risk level based on volatility and fundamentals."""
        try:
            # Calculate volatility
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * math.sqrt(252)  # Annualized volatility
            
            # Get beta
            beta = info.get('beta', 1.0)
            
            # Get debt metrics
            debt_to_equity = info.get('debtToEquity', 0.5)
            
            risk_score = 0
            
            # Volatility risk
            if volatility > 0.4:
                risk_score += 3
            elif volatility > 0.25:
                risk_score += 2
            elif volatility > 0.15:
                risk_score += 1
            
            # Beta risk
            if beta > 1.5:
                risk_score += 2
            elif beta > 1.2:
                risk_score += 1
            
            # Debt risk
            if debt_to_equity > 1.0:
                risk_score += 2
            elif debt_to_equity > 0.5:
                risk_score += 1
            
            if risk_score >= 5:
                return "VERY_HIGH"
            elif risk_score >= 4:
                return "HIGH"
            elif risk_score >= 2:
                return "MODERATE"
            elif risk_score >= 1:
                return "LOW"
            else:
                return "VERY_LOW"
                
        except Exception:
            return "MODERATE"
    
    def _calculate_confidence(self, info: Dict[str, Any], hist: pd.DataFrame) -> float:
        """Calculate confidence in the analysis."""
        confidence = 1.0
        
        # Reduce confidence if missing key data
        key_fields = ['trailingPE', 'returnOnEquity', 'revenueGrowth', 'debtToEquity']
        missing_fields = sum(1 for field in key_fields if info.get(field) is None)
        confidence -= missing_fields * 0.1
        
        # Reduce confidence for insufficient historical data
        if len(hist) < 100:
            confidence -= 0.2
        elif len(hist) < 200:
            confidence -= 0.1
        
        # Reduce confidence for high volatility (uncertain predictions)
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * math.sqrt(252)
        if volatility > 0.5:
            confidence -= 0.3
        elif volatility > 0.3:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _identify_strengths_weaknesses(
        self, technical_score: float, fundamental_score: float, momentum_score: float, info: Dict[str, Any]
    ) -> tuple[List[str], List[str]]:
        """Identify key strengths and weaknesses."""
        strengths = []
        weaknesses = []
        
        # Technical analysis
        if technical_score >= 75:
            strengths.append("Strong technical indicators")
        elif technical_score <= 35:
            weaknesses.append("Weak technical indicators")
        
        # Fundamental analysis
        if fundamental_score >= 75:
            strengths.append("Solid fundamental metrics")
        elif fundamental_score <= 35:
            weaknesses.append("Poor fundamental metrics")
        
        # Momentum analysis
        if momentum_score >= 75:
            strengths.append("Strong price momentum")
        elif momentum_score <= 35:
            weaknesses.append("Weak price momentum")
        
        # Specific fundamental strengths/weaknesses
        roe = info.get('returnOnEquity')
        if roe and (roe * 100 if roe < 1 else roe) > 20:
            strengths.append("Excellent return on equity")
        elif roe and (roe * 100 if roe < 1 else roe) < 5:
            weaknesses.append("Poor return on equity")
        
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity and debt_to_equity < 0.3:
            strengths.append("Low debt levels")
        elif debt_to_equity and debt_to_equity > 1.5:
            weaknesses.append("High debt levels")
        
        return strengths, weaknesses
    
    def _calculate_price_targets(
        self, info: Dict[str, Any], hist: pd.DataFrame, overall_score: float
    ) -> tuple[Optional[float], Optional[float]]:
        """Calculate target price and stop loss."""
        try:
            current_price = hist['Close'].iloc[-1]
            
            # Calculate volatility for stop loss
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std()
            
            # Target price based on score
            if overall_score >= 75:
                target_multiplier = 1.2  # 20% upside
            elif overall_score >= 65:
                target_multiplier = 1.15  # 15% upside
            elif overall_score >= 55:
                target_multiplier = 1.1  # 10% upside
            else:
                target_multiplier = 1.05  # 5% upside
            
            target_price = current_price * target_multiplier
            
            # Stop loss based on volatility (2 standard deviations)
            stop_loss = current_price * (1 - 2 * volatility)
            
            return float(target_price), float(stop_loss)
            
        except Exception:
            return None, None
