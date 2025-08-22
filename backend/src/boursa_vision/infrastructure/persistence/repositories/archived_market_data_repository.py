"""
Archive-based Market Data Repository
Provides market data from archived records using Clean Architecture patterns
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

from boursa_vision.domain.entities.market_data import MarketData as DomainMarketData
from boursa_vision.domain.repositories.market_data_repository import IMarketDataRepository

logger = logging.getLogger(__name__)


# Use os and subprocess for database operations to avoid external dependencies
def execute_sql_query(
    database_url: str, query: str, params: tuple = ()
) -> List[Dict[str, Any]]:
    """Execute SQL query and return results as list of dictionaries"""
    try:
        # Simple connection without external dependencies
        import psycopg2
        from psycopg2.extras import RealDictCursor

        with psycopg2.connect(database_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
    except ImportError:
        # Fallback if psycopg2 not available
        logger.error("psycopg2 not available, cannot execute database queries")
        return []


class ArchivedMarketDataRepository:
    """Repository for accessing archived market data with Clean Architecture compliance"""

    def __init__(self, database_url: str):
        self.database_url = database_url

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def get_available_symbols(self) -> List[str]:
        """Get all symbols that have archived data"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT i.symbol 
                    FROM instruments i
                    JOIN market_data md ON md.instrument_id = i.id
                    WHERE md.interval_type = 'archiver'
                    AND i.is_active = true
                    ORDER BY i.symbol
                """
                )
                return [row["symbol"] for row in cur.fetchall()]

    def get_symbol_data(
        self, symbol: str, days_back: int = 252
    ) -> Optional[pd.DataFrame]:
        """Get historical data for a symbol as pandas DataFrame"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get data for the symbol
                cur.execute(
                    """
                    SELECT 
                        md.time,
                        md.open_price,
                        md.high_price,
                        md.low_price,
                        md.close_price,
                        md.adjusted_close,
                        md.volume,
                        i.symbol,
                        i.name
                    FROM market_data md
                    JOIN instruments i ON md.instrument_id = i.id
                    WHERE i.symbol = %s 
                    AND md.interval_type = 'archiver'
                    AND md.time >= NOW() - INTERVAL '%s days'
                    ORDER BY md.time DESC
                    LIMIT %s
                """,
                    (symbol, days_back, days_back * 2),
                )  # Allow for some buffer

                rows = cur.fetchall()

                if not rows:
                    logger.warning(f"No archived data found for symbol {symbol}")
                    return None

                # Convert to DataFrame
                df = pd.DataFrame(rows)
                df["time"] = pd.to_datetime(df["time"])
                df.set_index("time", inplace=True)
                df.sort_index(inplace=True)  # Sort chronologically

                # Rename columns to match yfinance convention
                df = df.rename(
                    columns={
                        "open_price": "Open",
                        "high_price": "High",
                        "low_price": "Low",
                        "close_price": "Close",
                        "adjusted_close": "Adj Close",
                        "volume": "Volume",
                    }
                )

                logger.info(f"Retrieved {len(df)} records for {symbol} from archive")
                return df

    def get_latest_price_data(self, symbol: str) -> Optional[Dict]:
        """Get latest price data for a symbol"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        md.close_price as current_price,
                        md.volume,
                        md.time as last_updated,
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

                row = cur.fetchone()
                if row:
                    return dict(row)
                return None

    def get_symbols_with_sufficient_data(self, min_records: int = 30) -> List[str]:
        """Get symbols that have sufficient data for analysis"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT i.symbol, COUNT(*) as record_count
                    FROM instruments i
                    JOIN market_data md ON md.instrument_id = i.id
                    WHERE md.interval_type = 'archiver'
                    AND i.is_active = true
                    GROUP BY i.symbol
                    HAVING COUNT(*) >= %s
                    ORDER BY COUNT(*) DESC
                """,
                    (min_records,),
                )

                return [row["symbol"] for row in cur.fetchall()]

    def get_market_data_for_analysis(self, symbol: str) -> Optional[Dict]:
        """Get market data formatted for analysis (compatible with existing analyzer)"""
        df = self.get_symbol_data(symbol)
        if df is None or len(df) < 20:
            return None

        # Get additional metadata
        latest_data = self.get_latest_price_data(symbol)
        if not latest_data:
            return None

        # Format for compatibility with existing AdvancedInvestmentAnalyzer
        return {
            "history": df,
            "info": {
                "symbol": symbol,
                "shortName": latest_data.get("name", symbol),
                "currency": latest_data.get("currency", "USD"),
                "currentPrice": float(latest_data["current_price"]),
                "volume": int(latest_data.get("volume", 0)),
                "lastUpdated": latest_data["last_updated"],
            },
        }

    def get_bulk_analysis_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data for multiple symbols for bulk analysis"""
        results = {}

        for symbol in symbols:
            try:
                data = self.get_market_data_for_analysis(symbol)
                if data:
                    results[symbol] = data
                    logger.debug(f"✅ {symbol}: {len(data['history'])} records loaded")
                else:
                    logger.warning(f"⚠️ {symbol}: No sufficient data")
            except Exception as e:
                logger.error(f"❌ {symbol}: Error loading data - {e}")

        logger.info(f"Loaded analysis data for {len(results)}/{len(symbols)} symbols")
        return results


class ArchiveMarketDataAdapter(IMarketDataRepository):
    """Adapter to make ArchivedMarketDataRepository compatible with domain repository interface"""

    def __init__(self, archive_repository: ArchivedMarketDataRepository):
        self.archive_repo = archive_repository

    async def find_by_symbol_and_timerange(
        self,
        symbol: str,
        start_time,
        end_time,
        interval_type: str = "1d",
        limit: Optional[int] = None,
    ) -> List[DomainMarketData]:
        """Find market data by symbol and time range from archive"""
        # Calculate days back from time range
        if isinstance(start_time, datetime):
            days_back = (datetime.now() - start_time).days
        else:
            days_back = 252  # Default to 1 year

        df = self.archive_repo.get_symbol_data(symbol, days_back)
        if df is None:
            return []

        # Convert DataFrame rows to domain entities
        result = []
        for timestamp, row in df.iterrows():
            market_data = DomainMarketData(
                symbol=symbol,
                timestamp=timestamp,
                open_price=float(row["Open"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                close_price=float(row["Close"]),
                volume=int(row["Volume"]),
                interval_type="1d",
            )
            result.append(market_data)

        # Apply limit if specified
        if limit:
            result = result[-limit:]  # Get most recent records

        return result

    async def find_latest_by_symbol(
        self, symbol: str, interval_type: str = "1d"
    ) -> Optional[DomainMarketData]:
        """Find latest market data for symbol from archive"""
        latest = self.archive_repo.get_latest_price_data(symbol)
        if not latest:
            return None

        return DomainMarketData(
            symbol=symbol,
            timestamp=latest["last_updated"],
            close_price=float(latest["current_price"]),
            volume=int(latest.get("volume", 0)),
            interval_type="1d",
        )

    async def save(self, market_data: DomainMarketData) -> DomainMarketData:
        """Archive repository is read-only"""
        raise NotImplementedError("Archive repository is read-only")

    async def find_by_symbols(
        self, symbols: List[str], interval_type: str = "1d", limit: Optional[int] = None
    ) -> List[DomainMarketData]:
        """Find latest market data for multiple symbols from archive"""
        result = []
        for symbol in symbols:
            latest = await self.find_latest_by_symbol(symbol, interval_type)
            if latest:
                result.append(latest)
        return result

    async def delete_old_data(self, days_to_keep: int) -> int:
        """Archive repository is read-only"""
        raise NotImplementedError("Archive repository is read-only")
