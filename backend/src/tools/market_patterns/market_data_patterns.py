"""
Market Data Validation and Normalization Patterns for Boursa Vision.

This module implements design patterns to ensure data consistency and prevent
duplicate/inconsistent entries for the same financial instrument at the same time.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Protocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketDataPoint:
    """Immutable data class representing a normalized market data point."""

    symbol: str
    timestamp: datetime
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Optional[Decimal]
    volume: Optional[int]
    interval_type: str

    def __post_init__(self):
        """Validate data after initialization."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.timestamp.tzinfo:
            raise ValueError("Timestamp must be timezone-aware")
        if self.open_price and self.open_price < 0:
            raise ValueError("Open price cannot be negative")
        if self.close_price and self.close_price < 0:
            raise ValueError("Close price cannot be negative")


class DataNormalizer(ABC):
    """Abstract base class for data normalization strategies."""

    @abstractmethod
    def normalize(self, raw_data: Dict[str, Any]) -> MarketDataPoint:
        """Normalize raw data into a standardized MarketDataPoint."""
        pass


class YFinanceDataNormalizer(DataNormalizer):
    """Concrete normalizer for YFinance data."""

    def __init__(self, price_precision: int = 8):
        self.price_precision = price_precision

    def normalize(self, raw_data: Dict[str, Any]) -> MarketDataPoint:
        """
        Normalize YFinance data with proper precision and timezone handling.

        Args:
            raw_data: Dictionary containing symbol, timestamp, OHLCV data, interval

        Returns:
            Normalized MarketDataPoint
        """
        symbol = raw_data["symbol"]
        timestamp = self._normalize_timestamp(raw_data["timestamp"])
        interval_type = raw_data.get("interval_type", "1d")

        # Normalize prices with consistent precision
        open_price = self._normalize_price(raw_data.get("Open"))
        high_price = self._normalize_price(raw_data.get("High"))
        low_price = self._normalize_price(raw_data.get("Low"))
        close_price = self._normalize_price(raw_data.get("Close"))

        # Normalize volume
        volume = self._normalize_volume(raw_data.get("Volume"))

        return MarketDataPoint(
            symbol=symbol,
            timestamp=timestamp,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            interval_type=interval_type,
        )

    def _normalize_timestamp(self, timestamp: Any) -> datetime:
        """Normalize timestamp to UTC timezone with consistent precision."""
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif hasattr(timestamp, "to_pydatetime"):
            dt = timestamp.to_pydatetime()
        else:
            dt = timestamp

        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)

        # Round to minute precision for daily data
        if hasattr(self, "_current_interval") and self._current_interval == "1d":
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

        return dt

    def _normalize_price(self, price: Any) -> Optional[Decimal]:
        """Normalize price to consistent decimal precision."""
        if price is None or str(price).lower() in ("nan", "none", ""):
            return None

        try:
            # Convert to Decimal for precise arithmetic
            decimal_price = Decimal(str(price))
            # Round to specified precision
            return decimal_price.quantize(
                Decimal("0." + "0" * self.price_precision), rounding=ROUND_HALF_UP
            )
        except (ValueError, TypeError):
            logger.warning(f"Invalid price value: {price}")
            return None

    def _normalize_volume(self, volume: Any) -> Optional[int]:
        """Normalize volume to integer."""
        if volume is None or str(volume).lower() in ("nan", "none", ""):
            return None

        try:
            return int(float(volume))
        except (ValueError, TypeError):
            logger.warning(f"Invalid volume value: {volume}")
            return None


class DataValidator:
    """Validates market data for consistency and business rules."""

    def __init__(self):
        self.validation_rules = [
            self._validate_price_consistency,
            self._validate_volume_consistency,
            self._validate_timestamp_consistency,
        ]

    def validate(self, data_point: MarketDataPoint) -> List[str]:
        """
        Validate a market data point against business rules.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        for rule in self.validation_rules:
            try:
                rule_errors = rule(data_point)
                errors.extend(rule_errors)
            except Exception as e:
                errors.append(f"Validation rule error: {str(e)}")

        return errors

    def _validate_price_consistency(self, data: MarketDataPoint) -> List[str]:
        """Validate that OHLC prices are logically consistent."""
        errors = []

        prices = [
            p
            for p in [
                data.open_price,
                data.high_price,
                data.low_price,
                data.close_price,
            ]
            if p is not None
        ]

        if not prices:
            return errors

        if data.high_price and data.low_price:
            if data.high_price < data.low_price:
                errors.append(
                    f"High price ({data.high_price}) cannot be less than low price ({data.low_price})"
                )

        if data.high_price:
            for price in [data.open_price, data.close_price]:
                if price and price > data.high_price:
                    errors.append(
                        f"Price ({price}) cannot be higher than high price ({data.high_price})"
                    )

        if data.low_price:
            for price in [data.open_price, data.close_price]:
                if price and price < data.low_price:
                    errors.append(
                        f"Price ({price}) cannot be lower than low price ({data.low_price})"
                    )

        return errors

    def _validate_volume_consistency(self, data: MarketDataPoint) -> List[str]:
        """Validate volume data."""
        errors = []

        if data.volume is not None and data.volume < 0:
            errors.append(f"Volume cannot be negative: {data.volume}")

        return errors

    def _validate_timestamp_consistency(self, data: MarketDataPoint) -> List[str]:
        """Validate timestamp data."""
        errors = []

        # Check if timestamp is in the future (allowing some tolerance)
        now = datetime.now(timezone.utc)
        if data.timestamp > now:
            errors.append(f"Timestamp cannot be in the future: {data.timestamp}")

        return errors


class DuplicateDetectionStrategy(ABC):
    """Abstract strategy for duplicate detection."""

    @abstractmethod
    def is_duplicate(
        self, new_data: MarketDataPoint, existing_data: List[MarketDataPoint]
    ) -> bool:
        """Check if new data is a duplicate of existing data."""
        pass


class ExactMatchDuplicateDetection(DuplicateDetectionStrategy):
    """Detect exact duplicates based on symbol, timestamp, and interval."""

    def is_duplicate(
        self, new_data: MarketDataPoint, existing_data: List[MarketDataPoint]
    ) -> bool:
        """Check for exact matches on key fields."""
        for existing in existing_data:
            if (
                existing.symbol == new_data.symbol
                and existing.timestamp == new_data.timestamp
                and existing.interval_type == new_data.interval_type
            ):
                return True
        return False


class FuzzyDuplicateDetection(DuplicateDetectionStrategy):
    """Detect fuzzy duplicates with small variations in prices."""

    def __init__(self, price_tolerance_percent: Decimal = Decimal("0.01")):
        self.price_tolerance = price_tolerance_percent / 100

    def is_duplicate(
        self, new_data: MarketDataPoint, existing_data: List[MarketDataPoint]
    ) -> bool:
        """Check for fuzzy matches allowing small price variations."""
        for existing in existing_data:
            if (
                existing.symbol == new_data.symbol
                and existing.timestamp == new_data.timestamp
                and existing.interval_type == new_data.interval_type
            ):
                # Check if prices are within tolerance
                if self._prices_within_tolerance(new_data, existing):
                    logger.info(
                        f"Fuzzy duplicate detected for {new_data.symbol} at {new_data.timestamp}"
                    )
                    return True

        return False

    def _prices_within_tolerance(
        self, data1: MarketDataPoint, data2: MarketDataPoint
    ) -> bool:
        """Check if prices are within acceptable tolerance."""
        price_pairs = [
            (data1.open_price, data2.open_price),
            (data1.high_price, data2.high_price),
            (data1.low_price, data2.low_price),
            (data1.close_price, data2.close_price),
        ]

        for price1, price2 in price_pairs:
            if price1 is not None and price2 is not None:
                if not self._within_tolerance(price1, price2):
                    return False

        return True

    def _within_tolerance(self, price1: Decimal, price2: Decimal) -> bool:
        """Check if two prices are within tolerance."""
        if price1 == 0 or price2 == 0:
            return price1 == price2

        diff = abs(price1 - price2)
        avg_price = (price1 + price2) / 2
        tolerance = avg_price * self.price_tolerance

        return diff <= tolerance


class MarketDataProcessor:
    """
    Main processor that orchestrates data normalization, validation, and duplicate detection.

    Uses Strategy pattern for different validation and duplicate detection strategies.
    """

    def __init__(
        self,
        normalizer: DataNormalizer,
        validator: DataValidator,
        duplicate_detector: DuplicateDetectionStrategy,
    ):
        self.normalizer = normalizer
        self.validator = validator
        self.duplicate_detector = duplicate_detector
        self.processed_data: List[MarketDataPoint] = []

    def process_data(self, raw_data: Dict[str, Any]) -> Optional[MarketDataPoint]:
        """
        Process raw market data through normalization, validation, and duplicate detection.

        Args:
            raw_data: Raw data from YFinance or other sources

        Returns:
            Normalized and validated MarketDataPoint, or None if invalid/duplicate
        """
        try:
            # Step 1: Normalize data
            normalized_data = self.normalizer.normalize(raw_data)
            logger.debug(f"Normalized data for {normalized_data.symbol}")

            # Step 2: Validate data
            validation_errors = self.validator.validate(normalized_data)
            if validation_errors:
                logger.warning(
                    f"Validation errors for {normalized_data.symbol}: {validation_errors}"
                )
                return None

            # Step 3: Check for duplicates
            if self.duplicate_detector.is_duplicate(
                normalized_data, self.processed_data
            ):
                logger.info(
                    f"Duplicate detected for {normalized_data.symbol} at {normalized_data.timestamp}"
                )
                return None

            # Step 4: Add to processed data
            self.processed_data.append(normalized_data)
            logger.info(f"Successfully processed data for {normalized_data.symbol}")

            return normalized_data

        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_processed": len(self.processed_data),
            "symbols": len(set(data.symbol for data in self.processed_data)),
            "intervals": set(data.interval_type for data in self.processed_data),
        }


# Factory pattern for creating processors
class ProcessorFactory:
    """Factory for creating market data processors with different configurations."""

    @staticmethod
    def create_yfinance_processor(
        price_precision: int = 8,
        use_fuzzy_duplicate_detection: bool = True,
        price_tolerance_percent: Decimal = Decimal("0.01"),
    ) -> MarketDataProcessor:
        """Create a processor optimized for YFinance data."""

        normalizer = YFinanceDataNormalizer(price_precision=price_precision)
        validator = DataValidator()

        if use_fuzzy_duplicate_detection:
            duplicate_detector = FuzzyDuplicateDetection(price_tolerance_percent)
        else:
            duplicate_detector = ExactMatchDuplicateDetection()

        return MarketDataProcessor(normalizer, validator, duplicate_detector)

    @staticmethod
    def create_strict_processor() -> MarketDataProcessor:
        """Create a processor with strict validation and exact duplicate detection."""

        normalizer = YFinanceDataNormalizer(price_precision=8)
        validator = DataValidator()
        duplicate_detector = ExactMatchDuplicateDetection()

        return MarketDataProcessor(normalizer, validator, duplicate_detector)
