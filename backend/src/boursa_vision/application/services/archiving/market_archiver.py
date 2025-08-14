"""
Enhanced Market Data Archiver with Pattern-Based Data Processing.

This module provides a robust archiving system that prevents data inconsistencies
and duplicates using design patterns and data validation.
"""

import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

# Add the src directory to Python path for imports
sys.path.insert(0, "/app/src")

try:
    import yfinance as yf
    from sqlalchemy import (
        BigInteger,
        Column,
        DateTime,
        Index,
        Integer,
        Numeric,
        String,
        UniqueConstraint,
        create_engine,
    )
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.sql import func

    # Import our pattern-based processing
    from tools.market_patterns.market_data_patterns import (
        MarketDataPoint,
        MarketDataProcessor,
        ProcessorFactory,
    )

except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# Database model
Base = declarative_base()


class MarketDataArchive(Base):
    """Enhanced market data archive model with better precision."""

    __tablename__ = "market_data_archive"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Numeric(20, 8), nullable=True)
    high_price = Column(Numeric(20, 8), nullable=True)
    low_price = Column(Numeric(20, 8), nullable=True)
    close_price = Column(Numeric(20, 8), nullable=True)
    volume = Column(BigInteger, nullable=True)
    interval_type = Column(String(10), nullable=False, server_default="1d")
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable
    data_source = Column(String(50), nullable=False, server_default="yfinance")

    __table_args__ = (
        UniqueConstraint(
            "symbol", "timestamp", "interval_type", name="uix_symbol_timestamp_interval"
        ),
        Index("idx_market_data_archive_symbol_timestamp", "symbol", "timestamp"),
    )

    @classmethod
    def from_market_data_point(
        cls, data_point: MarketDataPoint, source: str = "yfinance"
    ):
        """Create database model from normalized MarketDataPoint."""
        return cls(
            symbol=data_point.symbol,
            timestamp=data_point.timestamp,
            open_price=data_point.open_price,
            high_price=data_point.high_price,
            low_price=data_point.low_price,
            close_price=data_point.close_price,
            volume=data_point.volume,
            interval_type=data_point.interval_type,
            data_source=source,
        )


class EnhancedMarketDataArchiver:
    """
    Enhanced market data archiver with pattern-based processing.

    Features:
    - Data normalization and validation
    - Duplicate detection with fuzzy matching
    - Consistent timestamp and price handling
    - Comprehensive error logging
    """

    # Financial symbols to archive
    SYMBOLS = [
        # US ETFs
        "SPY",
        "QQQ",
        "DIA",
        "VTI",
        # Tech Stocks
        "AAPL",
        "MSFT",
        "GOOGL",
        "TSLA",
        "AMZN",
        "NVDA",
        "META",
        # Crypto
        "BTC-USD",
        "ETH-USD",
        # Forex
        "EURUSD=X",
        "GBPUSD=X",
        # Commodities
        "GC=F",
        "CL=F",
    ]

    def __init__(
        self, database_url: Optional[str] = None, use_fuzzy_detection: bool = True
    ):
        """Initialize the enhanced archiver."""
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://boursa_user:boursa_dev_password_2024@postgres:5432/boursa_vision",
        )

        self.engine = create_engine(self.database_url)
        self.session_local = sessionmaker(  # pylint: disable=invalid-name
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Create pattern-based processor
        self.processor = ProcessorFactory.create_yfinance_processor(
            price_precision=8,
            use_fuzzy_duplicate_detection=use_fuzzy_detection,
            price_tolerance_percent=Decimal("0.01"),  # 1% tolerance
        )

        # Statistics
        self.stats = {
            "processed": 0,
            "validated": 0,
            "duplicates_detected": 0,
            "db_added": 0,
            "db_skipped": 0,
            "errors": 0,
        }

        print("📊 Enhanced MarketDataArchiver initialized")
        print(f"   Symbols: {len(self.SYMBOLS)}")
        print(f"   Fuzzy duplicate detection: {use_fuzzy_detection}")

    def fetch_and_process_symbol_data(
        self, symbol: str, interval: str = "1d", period: str = "7d"
    ) -> Dict:
        """
        Fetch and process data for a single symbol using pattern-based processing.

        Args:
            symbol: Financial symbol
            interval: Data interval
            period: Data period

        Returns:
            Processing results
        """
        try:
            print(f"📈 Processing {symbol} data ({interval}, {period})...")

            # Fetch data from YFinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)

            if data.empty:
                return {
                    "symbol": symbol,
                    "status": "no_data",
                    "records_processed": 0,
                    "records_added": 0,
                    "records_skipped": 0,
                }

            # Process each data point
            session = self.session_local()
            records_added = 0
            records_skipped = 0
            records_processed = 0

            try:
                for timestamp, row in data.iterrows():
                    records_processed += 1
                    self.stats["processed"] += 1

                    # Prepare raw data for processing
                    raw_data = {
                        "symbol": symbol,
                        "timestamp": timestamp,
                        "Open": row["Open"],
                        "High": row["High"],
                        "Low": row["Low"],
                        "Close": row["Close"],
                        "Volume": row["Volume"],
                        "interval_type": interval,
                    }

                    # Process through pattern-based system
                    processed_data = self.processor.process_data(raw_data)

                    if processed_data is None:
                        # Data was invalid or duplicate
                        records_skipped += 1
                        self.stats["db_skipped"] += 1
                        if records_processed > self.stats["validated"]:
                            self.stats["duplicates_detected"] += 1
                        continue

                    self.stats["validated"] += 1

                    # Try to save to database
                    try:
                        db_record = MarketDataArchive.from_market_data_point(
                            processed_data
                        )
                        session.add(db_record)
                        session.commit()
                        records_added += 1
                        self.stats["db_added"] += 1

                    except IntegrityError:
                        # Database constraint prevented duplicate
                        session.rollback()
                        records_skipped += 1
                        self.stats["db_skipped"] += 1
                        continue

                return {
                    "symbol": symbol,
                    "status": "success",
                    "records_processed": records_processed,
                    "records_added": records_added,
                    "records_skipped": records_skipped,
                    "total_records": len(data),
                }

            finally:
                session.close()

        except Exception as e:
            self.stats["errors"] += 1
            print(f"❌ Error processing {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(e),
                "records_processed": 0,
                "records_added": 0,
                "records_skipped": 0,
            }

    def archive_all_symbols(
        self, interval: str = "1d", period: str = "7d", delay: float = 0.5
    ) -> List[Dict]:
        """
        Archive data for all configured symbols with enhanced processing.

        Args:
            interval: Data interval
            period: Data period
            delay: Delay between requests

        Returns:
            List of processing results
        """
        print(f"🚀 Starting enhanced archival for {len(self.SYMBOLS)} symbols...")
        print(f"⚙️  Settings: interval={interval}, period={period}, delay={delay}s")

        results = []
        start_time = time.time()

        for i, symbol in enumerate(self.SYMBOLS, 1):
            print(f"[{i}/{len(self.SYMBOLS)}] Processing {symbol}...")

            result = self.fetch_and_process_symbol_data(symbol, interval, period)
            results.append(result)

            # Print detailed result
            if result["status"] == "success":
                added = result['records_added']
                skipped = result['records_skipped']
                print(f"✅ {symbol}: {added} added, {skipped} skipped")
            elif result["status"] == "no_data":
                print(f"⚠️  {symbol}: No data available")
            else:
                print(f"❌ {symbol}: Error - {result.get('error', 'Unknown error')}")

            # Delay to avoid rate limiting
            if i < len(self.SYMBOLS):
                time.sleep(delay)

        total_time = time.time() - start_time

        # Print comprehensive statistics
        self._print_final_statistics(results, total_time)

        return results

    def _print_final_statistics(self, results: List[Dict], total_time: float):
        """Print comprehensive statistics."""
        # Variables used for future statistics - pylint disable
        _ = sum(r["records_added"] for r in results)  # total_added
        _ = sum(r["records_skipped"] for r in results)  # total_skipped
        _ = sum(r["records_processed"] for r in results)  # total_processed

        print(f"\n🎉 Enhanced archival completed in {total_time:.1f}s")
        print("📊 Processing Statistics:")
        print(f"   Raw records processed: {self.stats['processed']}")
        print(f"   Records validated: {self.stats['validated']}")
        print(f"   Pattern duplicates detected: {self.stats['duplicates_detected']}")
        print(f"   Database records added: {self.stats['db_added']}")
        print(f"   Database records skipped: {self.stats['db_skipped']}")
        print(f"   Processing errors: {self.stats['errors']}")

        # Pattern processor statistics
        processor_stats = self.processor.get_statistics()
        print("📈 Pattern Processor Statistics:")
        print(f"   Unique data points processed: {processor_stats['total_processed']}")
        print(f"   Symbols in memory: {processor_stats['symbols']}")
        print(f"   Intervals processed: {processor_stats['intervals']}")

    def get_archive_stats(self) -> Dict:
        """Get database archive statistics."""
        session = self.session_local()

        try:
            # Total records
            total_records = session.query(MarketDataArchive).count()

            # Records by symbol with quality metrics
            from sqlalchemy import distinct, func  # pylint: disable=import-outside-toplevel

            symbol_stats = (
                session.query(
                    MarketDataArchive.symbol,
                    func.count(MarketDataArchive.id).label("count"),  # pylint: disable=not-callable
                    func.min(MarketDataArchive.timestamp).label("oldest"),  # pylint: disable=not-callable
                    func.max(MarketDataArchive.timestamp).label("newest"),  # pylint: disable=not-callable
                    func.count(distinct(MarketDataArchive.data_source)).label(  # pylint: disable=not-callable
                        "sources"
                    ),
                )
                .group_by(MarketDataArchive.symbol)
                .all()
            )

            return {
                "total_records": total_records,
                "symbols": [
                    {
                        "symbol": stat.symbol,
                        "count": stat.count,
                        "oldest": stat.oldest.isoformat() if stat.oldest else None,
                        "newest": stat.newest.isoformat() if stat.newest else None,
                        "sources": stat.sources,
                    }
                    for stat in symbol_stats
                ],
            }

        finally:
            session.close()

    def detect_potential_duplicates(self) -> List[Dict]:
        """Detect potential data quality issues in the database."""
        session = self.session_local()

        try:
            # Find records with identical timestamps but different prices
            from sqlalchemy import and_  # pylint: disable=import-outside-toplevel

            duplicates_query = (
                session.query(
                    MarketDataArchive.symbol,
                    MarketDataArchive.timestamp,
                    MarketDataArchive.interval_type,
                    func.count(MarketDataArchive.id).label("count"),  # pylint: disable=not-callable
                    func.array_agg(MarketDataArchive.close_price).label("prices"),  # pylint: disable=not-callable
                )
                .group_by(
                    MarketDataArchive.symbol,
                    MarketDataArchive.timestamp,
                    MarketDataArchive.interval_type,
                )
                .having(func.count(MarketDataArchive.id) > 1)  # pylint: disable=not-callable
            )

            potential_issues = []
            for result in duplicates_query.all():
                unique_prices = {str(p) for p in result.prices if p is not None}
                if len(unique_prices) > 1:
                    potential_issues.append(
                        {
                            "symbol": result.symbol,
                            "timestamp": result.timestamp.isoformat(),
                            "interval": result.interval_type,
                            "count": result.count,
                            "different_prices": list(unique_prices),
                        }
                    )

            return potential_issues

        finally:
            session.close()


def main():
    """Main function for enhanced archiving."""
    print("🏛️  Boursa Vision - Enhanced Market Data Archiver")
    print("=" * 65)
    print(f"⏰ Time: {datetime.now().isoformat()}")

    # Create enhanced archiver with fuzzy duplicate detection
    archiver = EnhancedMarketDataArchiver(use_fuzzy_detection=True)

    # Check for existing data quality issues
    print("\n🔍 Checking for existing data quality issues...")
    issues = archiver.detect_potential_duplicates()
    if issues:
        print(f"⚠️  Found {len(issues)} potential data quality issues:")
        for issue in issues[:5]:  # Show first 5
            symbol = issue['symbol']
            timestamp = issue['timestamp']
            prices_count = len(issue['different_prices'])
            print(f"   {symbol} at {timestamp}: {prices_count} different prices")
    else:
        print("✅ No data quality issues detected")

    # Archive recent data
    print("\n📊 Starting enhanced data archival...")
    # Options: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
    _ = archiver.archive_all_symbols(interval="1wk", period="6mo", delay=0.5)  # results unused

    # Show final archive statistics
    print("\n📈 Final Archive Statistics:")
    stats = archiver.get_archive_stats()
    print(f"Total records: {stats['total_records']}")

    if stats["symbols"]:
        print("\nTop symbols by record count:")
        sorted_symbols = sorted(
            stats["symbols"], key=lambda x: x["count"], reverse=True
        )
        for symbol_stat in sorted_symbols[:10]:
            print(f"  {symbol_stat['symbol']}: {symbol_stat['count']} records")


if __name__ == "__main__":
    main()
