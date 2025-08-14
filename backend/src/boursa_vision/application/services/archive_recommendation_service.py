"""
Archive-Enhanced Investment Recommendation Service
Integrates archived data with existing Clean Architecture
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArchiveDataProvider:
    """Provides market data from archived records"""

    def __init__(self):
        # Get database URL from environment
        self.database_url = (
            os.getenv("DATABASE_URL")
            or "postgresql://postgres:postgres@localhost:5432/trading_platform"
        )

    def get_market_data_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data for a symbol from archive in YFinance-compatible format"""
        try:
            # Import here to avoid dependency issues
            import psycopg2
            from psycopg2.extras import RealDictCursor

            with psycopg2.connect(
                self.database_url, cursor_factory=RealDictCursor
            ) as conn:
                with conn.cursor() as cur:
                    # Get historical data
                    cur.execute(
                        """
                        SELECT 
                            md.time,
                            md.open_price as "Open",
                            md.high_price as "High", 
                            md.low_price as "Low",
                            md.close_price as "Close",
                            md.adjusted_close as "Adj Close",
                            md.volume as "Volume"
                        FROM market_data md
                        JOIN instruments i ON md.instrument_id = i.id
                        WHERE i.symbol = %s 
                        AND md.interval_type = 'archiver'
                        ORDER BY md.time DESC
                        LIMIT 252
                    """,
                        (symbol,),
                    )

                    rows = cur.fetchall()
                    if len(rows) < 20:  # Need minimum data for analysis
                        return None

                    # Convert to DataFrame-like structure
                    import pandas as pd

                    df = pd.DataFrame(rows)
                    df["time"] = pd.to_datetime(df["time"])
                    df = df.set_index("time")
                    df = df.sort_index()  # Sort chronologically (fixed inplace issue)

                    # Get latest price and info
                    cur.execute(
                        """
                        SELECT 
                            md.close_price as current_price,
                            i.name,
                            i.currency
                        FROM market_data md
                        JOIN instruments i ON md.instrument_id = i.id
                        WHERE i.symbol = %s 
                        AND md.interval_type = 'archiver'
                        ORDER BY md.time DESC
                        LIMIT 1
                    """,
                        (symbol,),
                    )

                    latest = cur.fetchone()
                    if not latest:
                        return None

                    # Return in format compatible with existing analyzer
                    return {
                        "history": df,
                        "info": {
                            "symbol": symbol,
                            "shortName": latest["name"] or symbol,
                            "currency": latest["currency"] or "USD",
                            "currentPrice": float(latest["current_price"]),
                            "regularMarketPrice": float(latest["current_price"]),
                        },
                    }

        except Exception as e:
            logger.error(f"Error getting archive data for {symbol}: {e}")
            return None

    def get_available_symbols(self) -> List[str]:
        """Get symbols that have sufficient archived data"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            with psycopg2.connect(
                self.database_url, cursor_factory=RealDictCursor
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT i.symbol, COUNT(*) as record_count
                        FROM instruments i
                        JOIN market_data md ON md.instrument_id = i.id
                        WHERE md.interval_type = 'archiver'
                        AND i.is_active = true
                        GROUP BY i.symbol
                        HAVING COUNT(*) >= 30
                        ORDER BY COUNT(*) DESC
                    """
                    )

                    return [row["symbol"] for row in cur.fetchall()]

        except Exception as e:
            logger.error(f"Error getting available symbols: {e}")
            return []


class ArchiveEnhancedAdvancedAnalyzer:
    """Enhanced analyzer that can use both live and archived data"""

    def __init__(self, original_analyzer):
        self.original_analyzer = original_analyzer
        self.archive_provider = ArchiveDataProvider()

    def analyze_investment(self, symbol: str):
        """Analyze investment using archived data as fallback"""
        try:
            # First try original analyzer (live data)
            result = self.original_analyzer.analyze_investment(symbol)
            if result and result.overall_score > 40:  # Good result from live data
                logger.debug(
                    f"✅ {symbol}: Using live data analysis (score: {result.overall_score:.1f})"
                )
                return result
        except Exception as e:
            logger.debug(f"⚠️ {symbol}: Live data failed, trying archive - {e}")

        # Fallback to archived data
        try:
            archive_data = self.archive_provider.get_market_data_for_symbol(symbol)
            if archive_data:
                # Create a mock yfinance ticker-like object
                class MockTicker:
                    def __init__(self, data):
                        self.history_data = data["history"]
                        self.info_data = data["info"]

                    def history(self, period="1y", **kwargs):
                        return self.history_data

                    @property
                    def info(self):
                        return self.info_data

                # Use original analyzer with archived data
                mock_ticker = MockTicker(archive_data)

                # Monkey patch for this analysis
                original_yf_ticker = None
                try:
                    import yfinance as yf

                    original_yf_ticker = yf.Ticker
                    yf.Ticker = lambda x: mock_ticker

                    result = self.original_analyzer.analyze_investment(symbol)
                    logger.info(
                        f"✅ {symbol}: Using archived data analysis (score: {result.overall_score:.1f})"
                    )
                    return result

                finally:
                    # Restore original
                    if original_yf_ticker:
                        yf.Ticker = original_yf_ticker

        except Exception as e:
            logger.error(f"❌ {symbol}: Archive analysis failed - {e}")

        return None


def patch_investment_recommendation_service():
    """Patch the existing service to use archive-enhanced analyzer"""
    try:
        from src.application.services.advanced_analysis_service import (
            AdvancedInvestmentAnalyzer,
        )
        from src.application.services.investment_recommendation_service import (
            InvestmentRecommendationService,
        )

        # Store original init
        original_init = InvestmentRecommendationService.__init__

        def enhanced_init(self):
            """Enhanced initialization with archive support"""
            original_init(self)
            # Replace analyzer with archive-enhanced version
            original_analyzer = self.analyzer
            self.analyzer = ArchiveEnhancedAdvancedAnalyzer(original_analyzer)
            logger.info(
                "✅ Investment recommendation service enhanced with archive data support"
            )

        # Apply patch
        InvestmentRecommendationService.__init__ = enhanced_init
        logger.info("🔧 Patched InvestmentRecommendationService to use archived data")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to patch service: {e}")
        return False


# Auto-patch when module is imported
if __name__ != "__main__":
    patch_investment_recommendation_service()
