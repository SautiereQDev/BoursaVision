"""
Enhanced Investment Recommendation Service using Archived Data
Integrates with Clean Architecture and uses Repository pattern
"""

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
import psycopg2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ArchivedRecommendation:
    """Recommendation based on archived market data"""

    symbol: str
    name: str
    current_price: float
    recommendation: str  # "BUY", "HOLD", "SELL"
    overall_score: float
    confidence: float
    risk_level: str

    # Detailed scores
    technical_score: float
    momentum_score: float
    volume_score: float

    # Price analysis
    price_change_1d: float
    price_change_7d: float
    price_change_30d: float
    volatility: float

    # Volume analysis
    avg_volume: float
    volume_trend: str

    # Insights
    strengths: list[str]
    weaknesses: list[str]
    key_insights: list[str]


class ArchiveDataRepository:
    """Repository for accessing archived market data"""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)

    def get_available_symbols(self) -> list[str]:
        """Get all symbols with archived data"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT i.symbol
                    FROM instruments i
                    JOIN market_data md ON i.id = md.instrument_id
                    WHERE md.interval_type = 'archiver'
                    ORDER BY i.symbol
                """
                )
                return [row[0] for row in cur.fetchall()]

    def get_market_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Get market data for a symbol"""
        with self.get_connection() as conn:
            query = """
                SELECT 
                    md.time,
                    md.open_price as open,
                    md.high_price as high,
                    md.low_price as low,
                    md.close_price as close,
                    md.volume
                FROM market_data md
                JOIN instruments i ON md.instrument_id = i.id
                WHERE i.symbol = %s 
                AND md.interval_type = 'archiver'
                AND md.time >= NOW() - INTERVAL '%s days'
                ORDER BY md.time
            """

            df = pd.read_sql_query(query, conn, params=(symbol, days))
            if not df.empty:
                df["time"] = pd.to_datetime(df["time"])
                df.set_index("time", inplace=True)
            return df

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Get basic symbol information"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT symbol, name, instrument_type, currency
                    FROM instruments
                    WHERE symbol = %s
                """,
                    (symbol,),
                )

                result = cur.fetchone()
                if result:
                    return {
                        "symbol": result[0],
                        "name": result[1] or f"{result[0]} Security",
                        "instrument_type": result[2] or "stock",
                        "currency": result[3] or "USD",
                    }
                return {}


class TechnicalAnalyzer:
    """Technical analysis using archived data"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if not enough data

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    @staticmethod
    def calculate_moving_averages(prices: pd.Series) -> dict[str, float]:
        """Calculate moving averages"""
        mas = {}
        for period in [5, 10, 20, 50]:
            if len(prices) >= period:
                mas[f"ma_{period}"] = float(
                    prices.rolling(window=period).mean().iloc[-1]
                )
            else:
                mas[f"ma_{period}"] = float(prices.mean())
        return mas

    @staticmethod
    def calculate_volatility(prices: pd.Series, period: int = 20) -> float:
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
        returns = prices.pct_change().dropna()
        return (
            float(
                returns.rolling(window=min(period, len(returns))).std().iloc[-1] * 100
            )
            if len(returns) > 0
            else 0.0
        )


class ArchiveBasedRecommendationService:
    """Recommendation service using archived data with Clean Architecture"""

    def __init__(self, database_url: str):
        self.repository = ArchiveDataRepository(database_url)
        self.technical_analyzer = TechnicalAnalyzer()

    def get_recommendations(
        self, max_recommendations: int = 10, min_score: float = 60.0
    ) -> list[ArchivedRecommendation]:
        """Generate recommendations based on archived data"""
        logger.info("Generating recommendations from archived data...")

        # Get available symbols
        symbols = self.repository.get_available_symbols()
        logger.info(f"Found {len(symbols)} symbols with archived data")

        recommendations = []

        for symbol in symbols:
            try:
                recommendation = self._analyze_symbol(symbol)
                if recommendation and recommendation.overall_score >= min_score:
                    recommendations.append(recommendation)
                    logger.info(
                        f"✅ {symbol}: Score {recommendation.overall_score:.1f}"
                    )
                else:
                    logger.info(f"⚠️ {symbol}: Score too low or analysis failed")

            except Exception as e:
                logger.error(f"❌ {symbol}: Error - {e}")

        # Sort by overall score and return top recommendations
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        return recommendations[:max_recommendations]

    def _analyze_symbol(self, symbol: str) -> ArchivedRecommendation | None:
        """Analyze a single symbol"""
        # Get market data
        df = self.repository.get_market_data(symbol, days=30)
        if df.empty or len(df) < 5:
            return None

        # Get symbol info
        symbol_info = self.repository.get_symbol_info(symbol)

        # Calculate technical indicators
        close_prices = df["close"]
        current_price = float(close_prices.iloc[-1])

        # RSI Analysis
        rsi = self.technical_analyzer.calculate_rsi(close_prices)
        rsi_score = self._score_rsi(rsi)

        # Moving Averages
        mas = self.technical_analyzer.calculate_moving_averages(close_prices)
        ma_score = self._score_moving_averages(current_price, mas)

        # Price Changes
        price_changes = self._calculate_price_changes(close_prices)
        momentum_score = self._score_momentum(price_changes)

        # Volume Analysis
        volume_analysis = self._analyze_volume(df)
        volume_score = self._score_volume(volume_analysis)

        # Volatility
        volatility = self.technical_analyzer.calculate_volatility(close_prices)

        # Overall scoring
        technical_score = (rsi_score + ma_score) / 2
        overall_score = (
            technical_score * 0.4 + momentum_score * 0.3 + volume_score * 0.3
        )

        # Risk assessment
        risk_level = self._assess_risk(volatility, price_changes)

        # Confidence calculation
        confidence = self._calculate_confidence(df, rsi, volatility)

        # Recommendation
        recommendation_type = self._determine_recommendation(
            overall_score, technical_score, momentum_score
        )

        # Generate insights
        strengths, weaknesses, insights = self._generate_insights(
            rsi, mas, price_changes, volume_analysis, current_price
        )

        return ArchivedRecommendation(
            symbol=symbol,
            name=symbol_info.get("name", f"{symbol} Security"),
            current_price=current_price,
            recommendation=recommendation_type,
            overall_score=overall_score,
            confidence=confidence,
            risk_level=risk_level,
            technical_score=technical_score,
            momentum_score=momentum_score,
            volume_score=volume_score,
            price_change_1d=price_changes.get("1d", 0.0),
            price_change_7d=price_changes.get("7d", 0.0),
            price_change_30d=price_changes.get("30d", 0.0),
            volatility=volatility,
            avg_volume=volume_analysis.get("avg_volume", 0),
            volume_trend=volume_analysis.get("trend", "STABLE"),
            strengths=strengths,
            weaknesses=weaknesses,
            key_insights=insights,
        )

    def _score_rsi(self, rsi: float) -> float:
        """Score RSI (0-100)"""
        if rsi <= 30:
            return 85  # Oversold - good buy opportunity
        if rsi <= 40:
            return 75
        if rsi <= 60:
            return 65  # Neutral
        if rsi <= 70:
            return 45
        return 25  # Overbought - risky

    def _score_moving_averages(
        self, current_price: float, mas: dict[str, float]
    ) -> float:
        """Score moving average position"""
        score = 50

        # Check if price is above moving averages
        above_count = 0
        total_mas = 0

        for ma_value in mas.values():
            if current_price > ma_value:
                above_count += 1
            total_mas += 1

        if total_mas > 0:
            above_ratio = above_count / total_mas
            score = 30 + (above_ratio * 40)  # 30-70 range

        return score

    def _calculate_price_changes(self, prices: pd.Series) -> dict[str, float]:
        """Calculate price changes over different periods"""
        current = prices.iloc[-1]
        changes = {}

        periods = {"1d": 1, "7d": 7, "30d": 30}

        for period_name, days in periods.items():
            if len(prices) > days:
                past_price = prices.iloc[-days - 1]
                change_pct = ((current - past_price) / past_price) * 100
                changes[period_name] = float(change_pct)
            else:
                changes[period_name] = 0.0

        return changes

    def _score_momentum(self, price_changes: dict[str, float]) -> float:
        """Score momentum based on price changes"""
        # Weight recent changes more heavily
        score = (
            price_changes.get("1d", 0) * 0.5
            + price_changes.get("7d", 0) * 0.3
            + price_changes.get("30d", 0) * 0.2
        )

        # Convert to 0-100 scale
        if score > 10:
            return 90
        if score > 5:
            return 80
        if score > 2:
            return 70
        if score > 0:
            return 60
        if score > -2:
            return 50
        elif score > -5:
            return 40
        else:
            return 20

    def _analyze_volume(self, df: pd.DataFrame) -> dict[str, Any]:
        """Analyze volume trends"""
        volumes = df["volume"]
        avg_volume = float(volumes.mean())

        # Volume trend
        recent_volume = volumes.tail(5).mean()
        older_volume = (
            volumes.head(len(volumes) - 5).mean() if len(volumes) > 10 else avg_volume
        )

        if recent_volume > older_volume * 1.2:
            trend = "INCREASING"
        elif recent_volume < older_volume * 0.8:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        return {
            "avg_volume": avg_volume,
            "trend": trend,
            "recent_vs_avg": recent_volume / avg_volume if avg_volume > 0 else 1.0,
        }

    def _score_volume(self, volume_analysis: dict[str, Any]) -> float:
        """Score volume characteristics"""
        if volume_analysis["trend"] == "INCREASING":
            return 75
        if volume_analysis["trend"] == "STABLE":
            return 60
        return 45

    def _assess_risk(self, volatility: float, price_changes: dict[str, float]) -> str:
        """Assess risk level"""
        risk_score = volatility + abs(price_changes.get("7d", 0))

        if risk_score < 5:
            return "LOW"
        if risk_score < 15:
            return "MODERATE"
        return "HIGH"

    def _calculate_confidence(
        self, df: pd.DataFrame, rsi: float, volatility: float
    ) -> float:
        """Calculate confidence in the analysis"""
        # Base confidence on data quality and consistency
        base_confidence = min(len(df) / 50, 1.0)  # More data = higher confidence

        # Adjust for extreme values
        if 20 <= rsi <= 80 and volatility < 20:
            base_confidence *= 1.1
        elif (rsi < 10 or rsi > 90) or volatility > 30:
            base_confidence *= 0.8

        return min(base_confidence, 1.0)

    def _determine_recommendation(
        self, overall_score: float, technical_score: float, _: float
    ) -> str:
        """Determine buy/hold/sell recommendation"""
        if overall_score >= 75 and technical_score >= 65:
            return "BUY"
        if overall_score >= 55:
            return "HOLD"
        return "SELL"

    def _generate_insights(
        self,
        rsi: float,
        mas: dict[str, float],
        price_changes: dict[str, float],
        volume_analysis: dict[str, Any],
        current_price: float,
    ) -> tuple[list[str], list[str], list[str]]:
        """Generate human-readable insights"""
        strengths = []
        weaknesses = []
        insights = []

        # RSI insights
        if rsi <= 30:
            strengths.append("Oversold conditions - potential buying opportunity")
            insights.append(f"RSI at {rsi:.1f} indicates oversold conditions")
        elif rsi >= 70:
            weaknesses.append("Overbought conditions - potential selling pressure")
            insights.append(f"RSI at {rsi:.1f} indicates overbought conditions")

        # Price momentum
        if price_changes.get("7d", 0) > 5:
            strengths.append("Strong positive momentum over past week")
        elif price_changes.get("7d", 0) < -5:
            weaknesses.append("Negative momentum over past week")

        # Volume trend
        if volume_analysis["trend"] == "INCREASING":
            strengths.append("Increasing volume supports price movement")
        elif volume_analysis["trend"] == "DECREASING":
            weaknesses.append("Decreasing volume may indicate weakening interest")

        # Moving average position
        above_mas = sum(1 for ma in mas.values() if current_price > ma)
        if above_mas >= 3:
            strengths.append("Price above most moving averages - bullish trend")
        elif above_mas <= 1:
            weaknesses.append("Price below most moving averages - bearish trend")

        # General insights
        insights.append(
            f"Current price trend: {price_changes.get('30d', 0):.1f}% over 30 days"
        )
        insights.append(f"Volume trend: {volume_analysis['trend'].lower()}")

        return strengths, weaknesses, insights


def main():
    """Test the archive-based recommendation service"""
    import os

    database_url = os.getenv("DATABASE_URL")
    service = ArchiveBasedRecommendationService(database_url)

    recommendations = service.get_recommendations(max_recommendations=5, min_score=50.0)

    print(f"\\n📊 Found {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\\n{i}. {rec.symbol} - {rec.recommendation}")
        print(f"   Score: {rec.overall_score:.1f} | Confidence: {rec.confidence:.2f}")
        print(f"   Price: ${rec.current_price:.2f} | Risk: {rec.risk_level}")
        print(f"   Strengths: {', '.join(rec.strengths[:2])}")


if __name__ == "__main__":
    main()
