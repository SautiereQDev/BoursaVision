"""
Service d'archivage continu des données de marché.

Ce service collecte et archive automatiquement les données de marché
de tous les instruments financiers configurés.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
    import yfinance as yf

    YF_AVAILABLE = True
except ImportError:
    yf = None
    pd = None
    YF_AVAILABLE = False

try:
    from sqlalchemy.ext.asyncio import AsyncSession

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    AsyncSession = None
    SQLALCHEMY_AVAILABLE = False

from ...core.config import get_settings
from ...domain.entities.market_data import (
    DataSource,
    MarketData,
    MarketDataArgs,
    Timeframe,
)
from ...domain.value_objects.money import Currency
from ...infrastructure.persistence import get_db_session, get_market_data_repository
from ...infrastructure.persistence.mappers import MarketDataMapper

logger = logging.getLogger(__name__)
settings = get_settings()


class MarketDataArchiver:
    """
    Service d'archivage des données de marché.

    Responsabilités:
    - Collecter les données de YFinance
    - Transformer les données au format domaine
    - Persister en base de données TimescaleDB
    - Gérer les erreurs et la résilience
    """

    def __init__(self):
        self.settings = settings
        self.financial_indices = self._load_financial_indices()
        self.request_delay = 0.2  # Délai entre requêtes YFinance

    def _load_financial_indices(self) -> Dict[str, List[str]]:
        """Charge les indices financiers depuis la configuration."""
        return {
            "cac40": [
                "MC.PA",
                "ASML.AS",
                "OR.PA",
                "SAP",
                "TTE.PA",
                "RMS.PA",
                "INGA.AS",
                "SAN.PA",
                "BNP.PA",
                "AIR.PA",
                "SU.PA",
                "BN.PA",
                "DG.PA",
                "EL.PA",
                "CAP.PA",
                "ML.PA",
                "ORA.PA",
                "AI.PA",
                "GLE.PA",
                "LR.PA",
                "VIV.PA",
                "KER.PA",
                "PUB.PA",
                "URW.AS",
                "STM.PA",
                "TEP.PA",
                "WLN.PA",
                "EN.PA",
                "ACA.PA",
                "CS.PA",
                "BIO.PA",
                "SGO.PA",
                "SW.PA",
                "ALO.PA",
                "HO.PA",
                "ATO.PA",
                "RCO.PA",
                "DBG.PA",
                "STLA.PA",
                "EDF.PA",
            ],
            "nasdaq100": [
                "AAPL",
                "MSFT",
                "AMZN",
                "NVDA",
                "GOOGL",
                "GOOG",
                "META",
                "TSLA",
                "AVGO",
                "COST",
                "NFLX",
                "TMUS",
                "ASML",
                "ADBE",
                "PEP",
                "CSCO",
                "LIN",
                "TXN",
                "QCOM",
                "CMCSA",
                "AMAT",
                "AMD",
                "AMGN",
                "HON",
                "INTU",
                "ISRG",
                "BKNG",
                "VRTX",
                "ADP",
                "SBUX",
                "GILD",
                "ADI",
                "MU",
                "INTC",
                "PYPL",
                "REGN",
                "MELI",
                "LRCX",
                "KLAC",
                "SNPS",
                "CDNS",
                "MRVL",
                "ORLY",
                "CSX",
                "FTNT",
                "ADSK",
                "NXPI",
                "WDAY",
                "ABNB",
                "CHTR",
                "TEAM",
                "PCAR",
                "CPRT",
                "MNST",
                "AEP",
                "ROST",
                "FAST",
                "KDP",
                "EA",
                "VRSK",
                "ODFL",
                "EXC",
                "LULU",
                "GEHC",
                "CTSH",
                "XEL",
                "FANG",
                "CCEP",
                "KHC",
                "CSGP",
                "DDOG",
                "ZS",
                "BKR",
                "DLTR",
                "CRWD",
                "ANSS",
                "IDXX",
                "ON",
                "ILMN",
                "BIIB",
                "GFS",
                "CDW",
                "MDB",
                "WBD",
                "ARM",
                "MRNA",
                "SMCI",
            ],
            "ftse100": [
                "SHEL.L",
                "AZN.L",
                "LSEG.L",
                "UU.L",
                "ULVR.L",
                "BP.L",
                "GSK.L",
                "VOD.L",
                "LLOY.L",
                "TSCO.L",
                "PRU.L",
                "BT-A.L",
                "RIO.L",
                "BARC.L",
                "DGE.L",
                "NG.L",
                "NWG.L",
                "CRH.L",
                "REL.L",
                "GLEN.L",
            ],
            "dax40": [
                "SAP",
                "ASML.AS",
                "INGA.AS",
                "URW.AS",
                "SIE.DE",
                "DTE.DE",
                "MBG.DE",
                "ALV.DE",
                "MUV2.DE",
                "BAS.DE",
                "BMW.DE",
                "DB1.DE",
                "VOW3.DE",
                "HEN3.DE",
                "BEI.DE",
                "ADS.DE",
                "SHL.DE",
                "VNA.DE",
                "DBK.DE",
                "CON.DE",
                "IFX.DE",
                "MTX.DE",
                "ENR.DE",
                "HEI.DE",
                "RWE.DE",
            ],
        }

    async def archive_all_symbols(self, interval: str = "1d") -> Dict[str, any]:
        """
        Archive les données de tous les symboles financiers.

        Args:
            interval: Intervalle temporel (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1M)

        Returns:
            Rapport d'archivage avec statistiques
        """
        logger.info(f"Starting market data archival for interval: {interval}")

        total_symbols = 0
        successful_archives = 0
        failed_archives = 0
        errors = []

        # Traitement par indice
        for index_name, symbols in self.financial_indices.items():
            logger.info(f"Processing {index_name} with {len(symbols)} symbols")

            for symbol in symbols:
                total_symbols += 1
                try:
                    await self._archive_symbol_data(symbol, interval)
                    successful_archives += 1
                    logger.debug(f"Successfully archived {symbol}")

                    # Délai pour respecter les limites de YFinance
                    await asyncio.sleep(self.request_delay)

                except Exception as e:
                    failed_archives += 1
                    error_msg = f"Failed to archive {symbol}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

        # Statistiques finales
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval": interval,
            "total_symbols": total_symbols,
            "successful_archives": successful_archives,
            "failed_archives": failed_archives,
            "success_rate": successful_archives / total_symbols * 100
            if total_symbols > 0
            else 0,
            "errors": errors[:10],  # Limiter à 10 erreurs dans le rapport
            "total_errors": len(errors),
        }

        logger.info(
            f"Archival completed: {successful_archives}/{total_symbols} successful"
        )
        return report

    async def _archive_symbol_data(
        self, symbol: str, interval: str, period: str = "1d"
    ) -> None:
        """
        Archive les données d'un symbole spécifique.

        Args:
            symbol: Symbole financier (ex: AAPL, MC.PA)
            interval: Intervalle temporel
            period: Période de données à récupérer
        """
        try:
            # Récupération des données YFinance
            data_points = await self._fetch_yfinance_data(symbol, period, interval)

            if not data_points:
                logger.warning(f"No data retrieved for {symbol}")
                return

            # Persistance en base de données
            async with get_db_session() as session:
                market_data_repo = get_market_data_repository()

                for data_point in data_points:
                    # Vérifier si la donnée existe déjà
                    existing = await market_data_repo.find_by_symbol_and_timestamp(
                        symbol, data_point.timestamp
                    )

                    if not existing:
                        await market_data_repo.save(data_point)

                await session.commit()

            logger.debug(f"Archived {len(data_points)} data points for {symbol}")

        except Exception as e:
            logger.error(f"Error archiving {symbol}: {str(e)}")
            raise

    async def _fetch_yfinance_data(
        self, symbol: str, period: str, interval: str
    ) -> List[MarketData]:
        """
        Récupère les données depuis YFinance.

        Args:
            symbol: Symbole financier
            period: Période (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalle (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            Liste des entités MarketData
        """
        try:
            # Configuration pour éviter les timeouts
            ticker = yf.Ticker(symbol)

            # Récupération des données historiques
            hist_data = ticker.history(
                period=period,
                interval=interval,
                auto_adjust=True,
                prepost=True,
                threads=True,
            )

            if hist_data.empty:
                return []

            # Conversion vers les entités domaine
            market_data_list = []
            timeframe = self._convert_interval_to_timeframe(interval)
            currency = self._get_currency_for_symbol(symbol)

            for index, row in hist_data.iterrows():
                if all(
                    pd.notna(val)
                    for val in [row["Open"], row["High"], row["Low"], row["Close"]]
                ):
                    args = MarketDataArgs(
                        symbol=symbol,
                        timestamp=index.to_pydatetime().replace(tzinfo=timezone.utc),
                        open_price=Decimal(str(row["Open"])),
                        high_price=Decimal(str(row["High"])),
                        low_price=Decimal(str(row["Low"])),
                        close_price=Decimal(str(row["Close"])),
                        volume=int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                        timeframe=timeframe,
                        source=DataSource.YAHOO_FINANCE,
                        currency=currency,
                        adjusted_close=Decimal(
                            str(row["Close"])
                        ),  # YFinance auto-adjust est activé
                    )

                    market_data = MarketData.create(args)
                    market_data_list.append(market_data)

            return market_data_list

        except Exception as e:
            logger.error(f"YFinance fetch error for {symbol}: {str(e)}")
            raise

    def _convert_interval_to_timeframe(self, interval: str) -> Timeframe:
        """Convertit l'intervalle YFinance vers l'enum Timeframe."""
        mapping = {
            "1m": Timeframe.MINUTE_1,
            "2m": Timeframe.MINUTE_1,  # Approximation
            "5m": Timeframe.MINUTE_5,
            "15m": Timeframe.MINUTE_15,
            "30m": Timeframe.MINUTE_30,
            "60m": Timeframe.HOUR_1,
            "90m": Timeframe.HOUR_1,  # Approximation
            "1h": Timeframe.HOUR_1,
            "1d": Timeframe.DAY_1,
            "5d": Timeframe.DAY_1,  # Approximation
            "1wk": Timeframe.WEEK_1,
            "1mo": Timeframe.MONTH_1,
            "3mo": Timeframe.MONTH_1,  # Approximation
        }
        return mapping.get(interval, Timeframe.DAY_1)

    def _get_currency_for_symbol(self, symbol: str) -> Currency:
        """Détermine la devise d'un symbole basé sur son suffixe."""
        if symbol.endswith(".PA"):  # Paris
            return Currency.EUR
        elif symbol.endswith(".L"):  # London
            return Currency.GBP
        elif symbol.endswith(".DE"):  # Allemagne
            return Currency.EUR
        elif symbol.endswith(".AS"):  # Amsterdam
            return Currency.EUR
        else:  # US par défaut
            return Currency.USD

    async def get_archival_status(self) -> Dict[str, any]:
        """
        Récupère le statut de l'archivage.

        Returns:
            Statut détaillé de l'archivage
        """
        try:
            async with get_db_session() as session:
                market_data_repo = get_market_data_repository()

                # Statistiques générales
                total_records = await market_data_repo.count_all_records()
                latest_timestamp = await market_data_repo.get_latest_timestamp()
                oldest_timestamp = await market_data_repo.get_oldest_timestamp()

                # Statistiques par indice
                index_stats = {}
                for index_name, symbols in self.financial_indices.items():
                    index_stats[index_name] = {
                        "symbols": len(symbols),
                        "sample_symbols": symbols[:5],  # Échantillon
                    }

                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_records": total_records,
                    "latest_data": latest_timestamp.isoformat()
                    if latest_timestamp
                    else None,
                    "oldest_data": oldest_timestamp.isoformat()
                    if oldest_timestamp
                    else None,
                    "coverage_days": (latest_timestamp - oldest_timestamp).days
                    if latest_timestamp and oldest_timestamp
                    else 0,
                    "indices": index_stats,
                    "status": "active",
                }

        except Exception as e:
            logger.error(f"Error getting archival status: {str(e)}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "error": str(e),
            }


# Instance globale pour les tâches Celery
market_data_archiver = MarketDataArchiver()
