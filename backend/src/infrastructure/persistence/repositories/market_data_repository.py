"""
SQLAlchemy repository implementation for MarketData with TimescaleDB optimizations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.market_data import MarketData as DomainMarketData
from src.domain.repositories.market_data_repository import IMarketDataRepository
from src.infrastructure.persistence.mappers import MapperFactory
from src.infrastructure.persistence.models.market_data import MarketData
from src.infrastructure.persistence.sqlalchemy.database import get_db_session


class SQLAlchemyMarketDataRepository(IMarketDataRepository):
    """
    SQLAlchemy implementation of market data repository with TimescaleDB optimizations.
    Implements high-performance time-series queries.
    """

    def __init__(self):
        self._mapper = MapperFactory.get_mapper("market_data")

    async def find_latest_by_symbol(self, symbol: str) -> Optional[DomainMarketData]:
        """Find latest market data for symbol."""
        async with get_db_session() as session:
            query = (
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .order_by(desc(MarketData.time))
                .limit(1)
            )
            result = await session.execute(query)
            market_data_model = result.scalar_one_or_none()

            if market_data_model is None:
                return None

            return self._mapper.to_domain(market_data_model)

    async def find_by_symbol_and_timerange(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: str = "1d",
    ) -> List[DomainMarketData]:
        """Find market data for symbol within time range."""
        async with get_db_session() as session:
            query = (
                select(MarketData)
                .where(
                    and_(
                        MarketData.symbol == symbol,
                        MarketData.interval_type == interval_type,
                        MarketData.time >= start_time,
                        MarketData.time <= end_time,
                    )
                )
                .order_by(MarketData.time)
            )
            result = await session.execute(query)
            market_data_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in market_data_models]

    async def find_latest_prices(
        self, symbols: List[str]
    ) -> Dict[str, DomainMarketData]:
        """Find latest prices for multiple symbols (optimized query)."""
        async with get_db_session() as session:
            # Use TimescaleDB's last() function for optimal performance
            query = text(
                """
                SELECT DISTINCT ON (symbol) symbol, time, open_price, high_price, 
                       low_price, close_price, adjusted_close, volume, 
                       interval_type, source, created_at
                FROM market_data 
                WHERE symbol = ANY(:symbols)
                ORDER BY symbol, time DESC
            """
            )

            result = await session.execute(query, {"symbols": symbols})
            rows = result.fetchall()

            latest_prices = {}
            for row in rows:
                # Create MarketData model from row
                market_data_model = MarketData(
                    time=row.time,
                    symbol=row.symbol,
                    interval_type=row.interval_type,
                    open_price=row.open_price,
                    high_price=row.high_price,
                    low_price=row.low_price,
                    close_price=row.close_price,
                    adjusted_close=row.adjusted_close,
                    volume=row.volume,
                    source=row.source,
                    created_at=row.created_at,
                )
                latest_prices[row.symbol] = self._mapper.to_domain(market_data_model)

            return latest_prices

    async def save(self, market_data: DomainMarketData) -> DomainMarketData:
        """Save market data."""
        async with get_db_session() as session:
            market_data_dict = self._mapper.to_persistence(market_data)

            # Check if data exists (time + symbol + interval is unique)
            query = select(MarketData).where(
                and_(
                    MarketData.time == market_data_dict["time"],
                    MarketData.symbol == market_data_dict["symbol"],
                    MarketData.interval_type == market_data_dict["interval_type"],
                )
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                for key, value in market_data_dict.items():
                    if key not in ["time", "symbol", "interval_type"]:
                        setattr(existing, key, value)
                market_data_model = existing
            else:
                # Create new
                market_data_model = MarketData(**market_data_dict)
                session.add(market_data_model)

            await session.flush()
            await session.refresh(market_data_model)

            return self._mapper.to_domain(market_data_model)

    async def save_bulk(self, market_data_list: List[DomainMarketData]) -> None:
        """Bulk save market data for better performance."""
        async with get_db_session() as session:
            market_data_dicts = [
                self._mapper.to_persistence(md) for md in market_data_list
            ]

            # Use TimescaleDB's ON CONFLICT for upserts
            from sqlalchemy.dialects.postgresql import insert

            stmt = insert(MarketData).values(market_data_dicts)
            stmt = stmt.on_conflict_do_update(
                index_elements=["time", "symbol", "interval_type"],
                set_={
                    "open_price": stmt.excluded.open_price,
                    "high_price": stmt.excluded.high_price,
                    "low_price": stmt.excluded.low_price,
                    "close_price": stmt.excluded.close_price,
                    "adjusted_close": stmt.excluded.adjusted_close,
                    "volume": stmt.excluded.volume,
                    "source": stmt.excluded.source,
                    "created_at": stmt.excluded.created_at,
                },
            )

            await session.execute(stmt)
            await session.flush()

    async def delete_old_data(self, older_than_days: int = 365) -> int:
        """Delete old market data to manage storage (TimescaleDB optimization)."""
        async with get_db_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            # Use TimescaleDB's drop_chunks for optimal performance
            query = text(
                """
                SELECT drop_chunks('market_data', :cutoff_date);
            """
            )

            result = await session.execute(query, {"cutoff_date": cutoff_date})
            await session.flush()

            return result.rowcount or 0

    async def get_market_summary(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market summary statistics using TimescaleDB functions."""
        async with get_db_session() as session:
            # Use TimescaleDB's time_bucket for aggregations
            query = text(
                """
                WITH latest_data AS (
                    SELECT DISTINCT ON (symbol) 
                           symbol, close_price, volume, time
                    FROM market_data 
                    WHERE symbol = ANY(:symbols)
                      AND time >= NOW() - INTERVAL '7 days'
                    ORDER BY symbol, time DESC
                ),
                daily_stats AS (
                    SELECT symbol,
                           AVG(close_price) as avg_price,
                           MIN(close_price) as min_price,
                           MAX(close_price) as max_price,
                           SUM(volume) as total_volume
                    FROM market_data
                    WHERE symbol = ANY(:symbols)
                      AND time >= NOW() - INTERVAL '30 days'
                    GROUP BY symbol
                )
                SELECT l.symbol, l.close_price, l.volume, l.time,
                       d.avg_price, d.min_price, d.max_price, d.total_volume
                FROM latest_data l
                JOIN daily_stats d ON l.symbol = d.symbol
            """
            )

            result = await session.execute(query, {"symbols": symbols})
            rows = result.fetchall()

            summary = {}
            for row in rows:
                summary[row.symbol] = {
                    "current_price": float(row.close_price),
                    "current_volume": int(row.volume or 0),
                    "last_update": row.time,
                    "avg_price_30d": float(row.avg_price),
                    "min_price_30d": float(row.min_price),
                    "max_price_30d": float(row.max_price),
                    "total_volume_30d": int(row.total_volume or 0),
                }

            return summary
