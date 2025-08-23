"""
Market Scanner Service - Collecte Massive de Données Boursières
===============================================================

Service orchestrant la collecte massive de données sur des milliers de valeurs boursières,
utilisant les patterns Strategy, Observer et Factory pour une architecture flexible et extensible.

Design Patterns Utilisés:
- Strategy Pattern: Différentes stratégies de scan (secteur, capitalisation, performance)
- Observer Pattern: Notification des résultats d'analyse
- Factory Pattern: Création des scanners spécialisés
- Command Pattern: Exécution des commandes de scan
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar

try:
    import numpy as np
    import pandas as pd
    import yfinance as yf

    YF_AVAILABLE = True
except ImportError:
    yf = None
    pd = None
    np = None
    YF_AVAILABLE = False


logger = logging.getLogger(__name__)


class ScanStrategy(str, Enum):
    """Stratégies de scan du marché"""

    FULL_MARKET = "full_market"
    BY_SECTOR = "by_sector"
    BY_MARKET_CAP = "by_market_cap"
    TOP_VOLUME = "top_volume"
    TOP_GAINERS = "top_gainers"
    TOP_LOSERS = "top_losers"
    TECHNICAL_BREAKOUT = "technical_breakout"
    FUNDAMENTAL_UNDERVALUED = "fundamental_undervalued"


@dataclass
class ScanResult:
    """Résultat d'un scan de marché"""

    symbol: str
    name: str
    sector: str | None
    market_cap: float | None
    price: float
    change_percent: float
    volume: int
    pe_ratio: float | None
    pb_ratio: float | None
    roe: float | None
    debt_to_equity: float | None
    dividend_yield: float | None
    rsi: float | None
    macd_signal: str | None
    technical_score: float
    fundamental_score: float
    overall_score: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convertir en dictionnaire"""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "sector": self.sector,
            "market_cap": self.market_cap,
            "price": self.price,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "roe": self.roe,
            "debt_to_equity": self.debt_to_equity,
            "dividend_yield": self.dividend_yield,
            "rsi": self.rsi,
            "macd_signal": self.macd_signal,
            "technical_score": self.technical_score,
            "fundamental_score": self.fundamental_score,
            "overall_score": self.overall_score,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ScanConfig:
    """Configuration d'un scan de marché"""

    strategy: ScanStrategy
    max_symbols: int = 1000
    min_market_cap: float = 1e9  # 1 billion
    min_volume: int = 100000
    sectors: list[str] | None = None
    exclude_symbols: set[str] = field(default_factory=set)
    include_fundamentals: bool = True
    include_technicals: bool = True
    parallel_requests: int = 50
    timeout_per_symbol: float = 10.0


class ScanResultObserver(ABC):
    """Observer interface pour les résultats de scan"""

    @abstractmethod
    async def on_scan_result(self, result: ScanResult) -> None:
        """Notification d'un nouveau résultat"""
        pass

    @abstractmethod
    async def on_scan_completed(self, results: list[ScanResult]) -> None:
        """Notification de fin de scan"""
        pass


class MarketScannerStrategy(ABC):
    """Interface pour les stratégies de scan"""

    @abstractmethod
    async def get_symbols_to_scan(self, config: ScanConfig) -> list[str]:
        """Récupère la liste des symboles à scanner"""
        pass

    @abstractmethod
    def should_include_symbol(self, symbol: str, data: dict) -> bool:
        """Détermine si un symbole doit être inclus dans les résultats"""
        pass


class FullMarketStrategy(MarketScannerStrategy):
    """Stratégie de scan complet du marché"""

    # Listes prédéfinies de symboles populaires par secteur
    SECTOR_SYMBOLS: ClassVar[dict[str, list[str]]] = {
        "technology": [
            "AAPL",
            "MSFT",
            "GOOGL",
            "GOOG",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "ADBE",
            "CRM",
            "ORCL",
            "INTC",
            "AMD",
            "CSCO",
            "AVGO",
            "TXN",
            "QCOM",
            "INTU",
            "MU",
            "AMAT",
            "LRCX",
            "KLAC",
            "MRVL",
            "FTNT",
            "TEAM",
            "SNOW",
            "PLTR",
            "CRWD",
            "ZS",
        ],
        "healthcare": [
            "JNJ",
            "PFE",
            "UNH",
            "ABBV",
            "TMO",
            "ABT",
            "LLY",
            "DHR",
            "BMY",
            "MRK",
            "AMGN",
            "GILD",
            "ISRG",
            "VRTX",
            "REGN",
            "BIIB",
            "ILMN",
            "MRNA",
            "ZTS",
            "CVS",
        ],
        "financial": [
            "JPM",
            "BAC",
            "WFC",
            "GS",
            "MS",
            "C",
            "AXP",
            "USB",
            "TFC",
            "PNC",
            "COF",
            "SCHW",
            "BLK",
            "SPGI",
            "CME",
            "ICE",
            "MCO",
            "AON",
            "MMC",
            "AJG",
        ],
        "consumer_discretionary": [
            "AMZN",
            "TSLA",
            "HD",
            "MCD",
            "NKE",
            "LOW",
            "SBUX",
            "TJX",
            "BKNG",
            "CMG",
            "LULU",
            "RCL",
            "MAR",
            "GM",
            "F",
            "NCLH",
            "CCL",
            "DIS",
            "ABNB",
            "ETSY",
        ],
        "consumer_staples": [
            "PG",
            "KO",
            "PEP",
            "WMT",
            "COST",
            "MDLZ",
            "CL",
            "KMB",
            "GIS",
            "K",
            "HSY",
            "MKC",
            "SJM",
            "CAG",
            "CPB",
            "CHD",
            "CLX",
            "TSN",
            "HRL",
            "KR",
        ],
        "energy": [
            "XOM",
            "CVX",
            "COP",
            "EOG",
            "SLB",
            "PXD",
            "KMI",
            "OKE",
            "WMB",
            "MPC",
            "VLO",
            "PSX",
            "HES",
            "FANG",
            "DVN",
            "BKR",
            "HAL",
            "CTRA",
            "OXY",
            "APA",
        ],
        "industrials": [
            "BA",
            "CAT",
            "HON",
            "UPS",
            "RTX",
            "LMT",
            "GE",
            "MMM",
            "DE",
            "UNP",
            "FDX",
            "NOC",
            "GD",
            "ETN",
            "EMR",
            "ITW",
            "PH",
            "CMI",
            "ROK",
            "DOV",
        ],
    }

    async def get_symbols_to_scan(self, config: ScanConfig) -> list[str]:
        """Récupère tous les symboles disponibles"""
        symbols = []

        # Ajouter les symboles par secteur
        for sector_symbols in self.SECTOR_SYMBOLS.values():
            symbols.extend(sector_symbols)

        # Ajouter les indices majeurs
        symbols.extend(
            ["SPY", "QQQ", "IWM", "DIA", "VTI", "VEA", "VWO", "AGG", "BND", "GLD"]
        )

        # Retirer les doublons et les symboles exclus
        symbols = list(set(symbols) - config.exclude_symbols)

        logger.info(f"Scanning {len(symbols)} symbols with full market strategy")
        return symbols[: config.max_symbols]

    def should_include_symbol(self, symbol: str, data: dict) -> bool:
        """Inclure tous les symboles valides"""
        return True


class SectorStrategy(MarketScannerStrategy):
    """Stratégie de scan par secteur"""

    def __init__(self, target_sectors: list[str]):
        self.target_sectors = target_sectors

    async def get_symbols_to_scan(self, config: ScanConfig) -> list[str]:
        """Récupère les symboles des secteurs ciblés"""
        symbols = []
        strategy = FullMarketStrategy()

        for sector in self.target_sectors:
            if sector.lower() in strategy.SECTOR_SYMBOLS:
                symbols.extend(strategy.SECTOR_SYMBOLS[sector.lower()])

        symbols = list(set(symbols) - config.exclude_symbols)
        logger.info(
            f"Scanning {len(symbols)} symbols for sectors: {self.target_sectors}"
        )
        return symbols[: config.max_symbols]

    def should_include_symbol(self, symbol: str, data: dict) -> bool:
        """Inclure si le secteur correspond"""
        sector = data.get("sector", "").lower()
        return any(target.lower() in sector for target in self.target_sectors)


class TechnicalAnalyzer:
    """Analyseur technique pour les données de marché"""

    @staticmethod
    def calculate_rsi(prices: list[float], period: int = 14) -> float:
        """Calcule le RSI"""
        if not YF_AVAILABLE or len(prices) < period + 1:
            return 50.0

        try:
            prices_series = pd.Series(prices)
            delta = prices_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except Exception:
            return 50.0

    @staticmethod
    def calculate_macd_signal(prices: list[float]) -> str:
        """Calcule le signal MACD"""
        if not YF_AVAILABLE or len(prices) < 26:
            return "NEUTRAL"

        try:
            prices_series = pd.Series(prices)
            ema_12 = prices_series.ewm(span=12).mean()
            ema_26 = prices_series.ewm(span=26).mean()
            macd = ema_12 - ema_26
            signal = macd.ewm(span=9).mean()

            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
                return "BUY"
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
                return "SELL"
            else:
                return "NEUTRAL"
        except Exception:
            return "NEUTRAL"

    @staticmethod
    def calculate_technical_score(
        rsi: float, macd_signal: str, price: float, sma_50: float, sma_200: float
    ) -> float:
        """Calcule un score technique global"""
        score = 50.0

        # Score RSI (pondération: 30%)
        if 30 <= rsi <= 70:
            rsi_score = 50 + (50 - rsi) * 0.5
        elif rsi < 30:
            rsi_score = 70 + (30 - rsi) * 1.5
        else:
            rsi_score = 30 - (rsi - 70) * 1.5

        score += (rsi_score - 50) * 0.3

        # Score MACD (pondération: 25%)
        macd_scores = {"BUY": 75, "NEUTRAL": 50, "SELL": 25}
        score += (macd_scores[macd_signal] - 50) * 0.25

        # Score tendance (pondération: 45%)
        if price > sma_50 > sma_200:
            trend_score = 80
        elif price > sma_50:
            trend_score = 65
        elif price < sma_50 < sma_200:
            trend_score = 30
        else:
            trend_score = 50

        score += (trend_score - 50) * 0.45

        return max(0, min(100, score))


class FundamentalAnalyzer:
    """Analyseur fondamental pour les données de marché"""

    @staticmethod
    def _score_pe_ratio(pe_ratio: float | None) -> float:
        """Score P/E ratio"""
        if pe_ratio is None or pe_ratio <= 0:
            return 50.0
        if 10 <= pe_ratio <= 20:
            return 80.0
        elif pe_ratio < 10:
            return 90.0
        elif pe_ratio <= 30:
            return 60.0
        else:
            return 30.0

    @staticmethod
    def _score_pb_ratio(pb_ratio: float | None) -> float:
        """Score P/B ratio"""
        if pb_ratio is None or pb_ratio <= 0:
            return 50.0
        if pb_ratio < 1:
            return 85.0
        elif pb_ratio <= 2:
            return 65.0
        else:
            return 35.0

    @staticmethod
    def _score_roe(roe: float | None) -> float:
        """Score ROE"""
        if roe is None:
            return 50.0
        if roe >= 20:
            return 90.0
        elif roe >= 15:
            return 75.0
        elif roe >= 10:
            return 60.0
        else:
            return 30.0

    @staticmethod
    def _score_debt_to_equity(debt_to_equity: float | None) -> float:
        """Score Debt/Equity"""
        if debt_to_equity is None:
            return 50.0
        if debt_to_equity < 0.3:
            return 85.0
        elif debt_to_equity < 0.6:
            return 70.0
        elif debt_to_equity < 1.0:
            return 45.0
        else:
            return 20.0

    @staticmethod
    def _score_dividend_yield(dividend_yield: float | None) -> float:
        """Score dividend yield"""
        if dividend_yield is None:
            return 50.0
        if dividend_yield >= 3:
            return 75.0
        elif dividend_yield >= 1:
            return 60.0
        else:
            return 50.0

    @classmethod
    def calculate_fundamental_score(
        cls,
        pe_ratio: float | None,
        pb_ratio: float | None,
        roe: float | None,
        debt_to_equity: float | None,
        dividend_yield: float | None,
    ) -> float:
        """Calcule un score fondamental global"""
        # Calculer chaque score composant
        pe_score = cls._score_pe_ratio(pe_ratio)
        pb_score = cls._score_pb_ratio(pb_ratio)
        roe_score = cls._score_roe(roe)
        de_score = cls._score_debt_to_equity(debt_to_equity)
        div_score = cls._score_dividend_yield(dividend_yield)

        # Pondération des scores
        weighted_score = (
            pe_score * 0.25
            + pb_score * 0.15
            + roe_score * 0.30
            + de_score * 0.20
            + div_score * 0.10
        )

        # Vérifier combien de métriques on a
        metrics_count = sum(
            1
            for x in [pe_ratio, pb_ratio, roe, debt_to_equity, dividend_yield]
            if x is not None
        )

        # Si on a peu de données, on est plus conservateur
        if metrics_count < 3:
            weighted_score = weighted_score * 0.8 + 50 * 0.2

        return max(0, min(100, weighted_score))


class MarketScannerService:
    """Service principal de scan du marché"""

    def __init__(self, yfinance_client: Any | None = None):
        self.yfinance_client = yfinance_client
        self.observers: list[ScanResultObserver] = []
        self.technical_analyzer = TechnicalAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=50)

    def add_observer(self, observer: ScanResultObserver) -> None:
        """Ajoute un observer"""
        self.observers.append(observer)

    def remove_observer(self, observer: ScanResultObserver) -> None:
        """Supprime un observer"""
        if observer in self.observers:
            self.observers.remove(observer)

    async def _notify_result(self, result: ScanResult) -> None:
        """Notifie les observers d'un nouveau résultat"""
        for observer in self.observers:
            try:
                await observer.on_scan_result(result)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")

    async def _notify_completion(self, results: list[ScanResult]) -> None:
        """Notifie les observers de la fin du scan"""
        for observer in self.observers:
            try:
                await observer.on_scan_completed(results)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")

    def _create_strategy(self, config: ScanConfig) -> MarketScannerStrategy:
        """Factory pour créer la stratégie appropriée"""
        if config.strategy == ScanStrategy.FULL_MARKET:
            return FullMarketStrategy()
        elif config.strategy == ScanStrategy.BY_SECTOR and config.sectors:
            return SectorStrategy(config.sectors)
        else:
            return FullMarketStrategy()  # Stratégie par défaut

    async def scan_market(self, config: ScanConfig) -> list[ScanResult]:
        """Lance un scan complet du marché"""
        logger.info(f"Starting market scan with strategy: {config.strategy}")
        start_time = datetime.now(UTC)

        # Créer la stratégie
        strategy = self._create_strategy(config)

        # Récupérer les symboles à scanner
        symbols = await strategy.get_symbols_to_scan(config)

        # Scanner les symboles en parallèle
        results = []
        semaphore = asyncio.Semaphore(config.parallel_requests)

        async def scan_symbol(symbol: str) -> ScanResult | None:
            async with semaphore:
                return self._scan_single_symbol(symbol, config, strategy)

        # Lancer tous les scans en parallèle
        tasks = [scan_symbol(symbol) for symbol in symbols]
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Traiter les résultats
        for result in completed_results:
            if isinstance(result, ScanResult):
                results.append(result)
                await self._notify_result(result)
            elif isinstance(result, Exception):
                logger.error(f"Error scanning symbol: {result}")

        # Trier par score global décroissant
        results.sort(key=lambda x: x.overall_score, reverse=True)

        # Notifier la fin
        await self._notify_completion(results)

        scan_time = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"Market scan completed: {len(results)} symbols scanned in {scan_time:.2f}s"
        )

        return results

    def _scan_single_symbol(
        self, symbol: str, config: ScanConfig, strategy: MarketScannerStrategy
    ) -> ScanResult | None:
        """Scanne un symbole individuel"""
        if not YF_AVAILABLE or yf is None:
            logger.warning("YFinance not available")
            return None

        try:
            # Récupérer les données de base
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Vérifier si on doit inclure ce symbole
            if not strategy.should_include_symbol(symbol, info):
                return None

            # Récupérer l'historique des prix
            hist = ticker.history(period="6mo", interval="1d")
            if hist.empty:
                return None

            # Extraire les données essentielles
            return self._extract_scan_data(symbol, info, hist, config)

        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return None

    def _extract_scan_data(
        self, symbol: str, info: dict[str, Any], hist: Any, config: ScanConfig
    ) -> ScanResult | None:
        """Extrait les données pour le scan"""
        try:
            current_price = float(hist["Close"].iloc[-1])

            # Données de base
            name = info.get("longName", symbol)
            sector = info.get("sector")
            market_cap = info.get("marketCap")
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0

            # Changement de prix
            change_percent = 0.0
            if len(hist) >= 2:
                change_percent = (
                    (current_price - hist["Close"].iloc[-2]) / hist["Close"].iloc[-2]
                ) * 100

            # Filtrer par critères de base
            if (
                market_cap and market_cap < config.min_market_cap
            ) or volume < config.min_volume:
                return None

            # Calculer les métriques et scores
            fundamental_data = self._extract_fundamental_data(info)
            technical_data = (
                self._extract_technical_data(hist) if config.include_technicals else {}
            )

            # Scores
            technical_score = technical_data.get("score", 50.0)
            fundamental_score = self.fundamental_analyzer.calculate_fundamental_score(
                **fundamental_data
            )
            overall_score = fundamental_score * 0.6 + technical_score * 0.4

            return ScanResult(
                symbol=symbol,
                name=name,
                sector=sector,
                market_cap=market_cap,
                price=current_price,
                change_percent=change_percent,
                volume=volume,
                pe_ratio=fundamental_data.get("pe_ratio"),
                pb_ratio=fundamental_data.get("pb_ratio"),
                roe=fundamental_data.get("roe"),
                debt_to_equity=fundamental_data.get("debt_to_equity"),
                dividend_yield=fundamental_data.get("dividend_yield"),
                rsi=technical_data.get("rsi"),
                macd_signal=technical_data.get("macd_signal", "NEUTRAL"),
                technical_score=technical_score,
                fundamental_score=fundamental_score,
                overall_score=overall_score,
            )

        except Exception as e:
            logger.error(f"Error extracting data for {symbol}: {e}")
            return None

    def _extract_fundamental_data(self, info: dict[str, Any]) -> dict[str, Any]:
        """Extrait les données fondamentales"""
        roe = info.get("returnOnEquity")
        if roe:
            roe = roe * 100

        dividend_yield = info.get("dividendYield")
        if dividend_yield:
            dividend_yield = dividend_yield * 100

        return {
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": roe,
            "debt_to_equity": info.get("debtToEquity"),
            "dividend_yield": dividend_yield,
        }

    def _extract_technical_data(self, hist: Any) -> dict[str, Any]:
        """Extrait les données techniques"""
        try:
            prices = hist["Close"].tolist()
            current_price = prices[-1]

            # Calculer les indicateurs
            rsi = self.technical_analyzer.calculate_rsi(prices)
            macd_signal = self.technical_analyzer.calculate_macd_signal(prices)

            # Moyennes mobiles
            sma_50 = (
                sum(prices[-50:]) / min(50, len(prices)) if prices else current_price
            )
            sma_200 = (
                sum(prices[-200:]) / min(200, len(prices)) if prices else current_price
            )

            # Score technique
            technical_score = self.technical_analyzer.calculate_technical_score(
                rsi, macd_signal, current_price, sma_50, sma_200
            )

            return {"rsi": rsi, "macd_signal": macd_signal, "score": technical_score}
        except Exception as e:
            logger.error(f"Error extracting technical data: {e}")
            return {"rsi": None, "macd_signal": "NEUTRAL", "score": 50.0}

    def get_top_opportunities(
        self, results: list[ScanResult], limit: int = 50
    ) -> list[ScanResult]:
        """Récupère les meilleures opportunités d'achat"""
        # Filtrer les résultats avec un score global élevé
        opportunities = [r for r in results if r.overall_score >= 70]

        # Trier par score global puis par score fondamental
        opportunities.sort(
            key=lambda x: (x.overall_score, x.fundamental_score), reverse=True
        )

        return opportunities[:limit]

    def get_sector_leaders(
        self, results: list[ScanResult]
    ) -> dict[str, list[ScanResult]]:
        """Récupère les leaders par secteur"""
        sector_results = {}

        for result in results:
            if result.sector:
                if result.sector not in sector_results:
                    sector_results[result.sector] = []
                sector_results[result.sector].append(result)

        # Trier chaque secteur par score et prendre les 10 premiers
        for sector in sector_results:
            sector_results[sector].sort(key=lambda x: x.overall_score, reverse=True)
            sector_results[sector] = sector_results[sector][:10]

        return sector_results

    def close(self):
        """Ferme les ressources"""
        self.executor.shutdown(wait=True)
