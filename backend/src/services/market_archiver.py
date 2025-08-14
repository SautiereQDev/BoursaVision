"""Simple market data archiver service for Boursa Vision."""

import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import yfinance as yf
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.infrastructure.persistence.models import MarketDataArchive


class MarketDataArchiver:
    """
    Simple market data archiver that collects and stores financial data.

    Features:
    - YFinance integration for real financial data
    - TimescaleDB storage with automatic compression
    - Duplicate handling with unique constraints
    - Support for multiple symbols and intervals
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

    def __init__(self, database_url: Optional[str] = None):
        """Initialize the archiver with database connection."""
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://boursa_user:boursa_dev_password_2024@localhost:5432/boursa_vision",
        )

        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        print(f"📊 MarketDataArchiver initialized with {len(self.SYMBOLS)} symbols")

    def fetch_and_store_data(
        self, symbol: str, interval: str = "1d", period: str = "5d"
    ) -> Dict:
        """
        Fetch data for a symbol and store it in the database.

        Args:
            symbol: Financial symbol (e.g., 'AAPL', 'BTC-USD')
            interval: Data interval ('1m', '5m', '1h', '1d')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y')

        Returns:
            Dict with archiving results
        """
        try:
            print(f"📈 Fetching {symbol} data ({interval}, {period})...")

            # Fetch data from YFinance
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)

            if data.empty:
                return {
                    "symbol": symbol,
                    "status": "no_data",
                    "records_added": 0,
                    "records_skipped": 0,
                }

            # Store in database
            session = self.SessionLocal()
            records_added = 0
            records_skipped = 0

            try:
                for timestamp, row in data.iterrows():
                    try:
                        # Create MarketDataArchive instance
                        archive_record = MarketDataArchive.create_from_yfinance(
                            symbol=symbol, data_row=row, interval=interval
                        )
                        archive_record.timestamp = timestamp.to_pydatetime().replace(
                            tzinfo=timezone.utc
                        )

                        session.add(archive_record)
                        session.commit()
                        records_added += 1

                    except IntegrityError:
                        # Record already exists (duplicate)
                        session.rollback()
                        records_skipped += 1
                        continue

                return {
                    "symbol": symbol,
                    "status": "success",
                    "records_added": records_added,
                    "records_skipped": records_skipped,
                    "total_records": len(data),
                }

            finally:
                session.close()

        except Exception as e:
            print(f"❌ Error archiving {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(e),
                "records_added": 0,
                "records_skipped": 0,
            }

    def archive_all_symbols(
        self, interval: str = "1d", period: str = "5d", delay: float = 0.2
    ) -> List[Dict]:
        """
        Archive data for all configured symbols.

        Args:
            interval: Data interval ('1m', '5m', '1h', '1d')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y')
            delay: Delay between requests to avoid rate limiting

        Returns:
            List of results for each symbol
        """
        print(f"🚀 Starting archival for {len(self.SYMBOLS)} symbols...")
        print(f"⚙️  Settings: interval={interval}, period={period}, delay={delay}s")

        results = []
        start_time = time.time()

        for i, symbol in enumerate(self.SYMBOLS, 1):
            print(f"[{i}/{len(self.SYMBOLS)}] Processing {symbol}...")

            result = self.fetch_and_store_data(symbol, interval, period)
            results.append(result)

            # Print result
            if result["status"] == "success":
                print(
                    f"✅ {symbol}: {result['records_added']} added, {result['records_skipped']} skipped"
                )
            elif result["status"] == "no_data":
                print(f"⚠️  {symbol}: No data available")
            else:
                print(f"❌ {symbol}: Error - {result.get('error', 'Unknown error')}")

            # Delay to avoid rate limiting
            if i < len(self.SYMBOLS):
                time.sleep(delay)

        total_time = time.time() - start_time
        total_added = sum(r["records_added"] for r in results)
        total_skipped = sum(r["records_skipped"] for r in results)

        print(f"\n🎉 Archival completed in {total_time:.1f}s")
        print(f"📊 Total: {total_added} records added, {total_skipped} skipped")

        return results

    def get_archive_stats(self) -> Dict:
        """Get statistics about archived data."""
        session = self.SessionLocal()

        try:
            # Total records
            total_records = session.query(MarketDataArchive).count()

            # Records by symbol
            from sqlalchemy import func

            symbol_stats = (
                session.query(
                    MarketDataArchive.symbol,
                    func.count(MarketDataArchive.id).label("count"),
                    func.min(MarketDataArchive.timestamp).label("oldest"),
                    func.max(MarketDataArchive.timestamp).label("newest"),
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
                    }
                    for stat in symbol_stats
                ],
            }

        finally:
            session.close()


def main():
    """Main function for standalone execution."""
    print("🏛️  Boursa Vision - Market Data Archiver")
    print("=" * 50)

    archiver = MarketDataArchiver()

    # Archive recent data
    results = archiver.archive_all_symbols(interval="1d", period="5d")

    # Show statistics
    print("\n📊 Archive Statistics:")
    print("-" * 30)
    stats = archiver.get_archive_stats()
    print(f"Total records: {stats['total_records']}")

    for symbol_stat in stats["symbols"]:
        print(f"{symbol_stat['symbol']}: {symbol_stat['count']} records")


if __name__ == "__main__":
    main()
