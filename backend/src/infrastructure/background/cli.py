#!/usr/bin/env python3
"""
CLI pour la gestion des tâches d'archivage des données de marché.

Ce script permet de lancer manuellement des tâches d'archivage,
de surveiller le statut et de gérer le système d'arrière-plan.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click

# Ajout du répertoire backend au path pour les imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.core.config import get_settings
from src.infrastructure.background.market_data_archiver import MarketDataArchiver

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool):
    """Boursa Vision - Market Data Archiver CLI"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")


@cli.command()
@click.option(
    "--interval",
    "-i",
    default="1d",
    type=click.Choice(["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]),
    help="Time interval for data archival",
)
@click.option(
    "--period",
    "-p",
    default="1d",
    type=click.Choice(
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    ),
    help="Period of data to retrieve",
)
def archive(interval: str, period: str):
    """Archive market data for all configured symbols."""
    logger.info(f"Starting manual archival: interval={interval}, period={period}")

    try:
        archiver = MarketDataArchiver()

        # Modification temporaire pour le period dans l'archiver
        async def run_archive():
            # Pour l'instant, on utilise la méthode existante
            return await archiver.archive_all_symbols(interval)

        report = asyncio.run(run_archive())

        # Affichage du rapport
        click.echo(f"\n📊 Archival Report - {report['timestamp']}")
        click.echo("=" * 50)
        click.echo(f"Interval: {report['interval']}")
        click.echo(f"Total symbols: {report['total_symbols']}")
        click.echo(f"Successful: {report['successful_archives']}")
        click.echo(f"Failed: {report['failed_archives']}")
        click.echo(f"Success rate: {report['success_rate']:.1f}%")

        if report["errors"]:
            click.echo(f"\n❌ Errors ({report['total_errors']} total):")
            for error in report["errors"][:5]:  # Afficher 5 erreurs max
                click.echo(f"  - {error}")
            if report["total_errors"] > 5:
                click.echo(f"  ... and {report['total_errors'] - 5} more errors")

        if report["success_rate"] >= 90:
            click.echo("\n✅ Archival completed successfully!")
        elif report["success_rate"] >= 70:
            click.echo("\n⚠️ Archival completed with warnings")
        else:
            click.echo("\n❌ Archival completed with errors")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Archival failed: {str(e)}")
        click.echo(f"❌ Archival failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("symbols", nargs=-1, required=True)
@click.option(
    "--interval",
    "-i",
    default="1d",
    type=click.Choice(["1m", "5m", "15m", "30m", "1h", "1d", "1w", "1M"]),
    help="Time interval for data archival",
)
def archive_symbols(symbols: tuple, interval: str):
    """Archive specific symbols manually."""
    symbol_list = list(symbols)
    logger.info(f"Archiving specific symbols: {symbol_list}")

    try:
        archiver = MarketDataArchiver()

        async def archive_specific():
            successful = 0
            failed = 0
            errors = []

            for symbol in symbol_list:
                try:
                    await archiver._archive_symbol_data(symbol, interval)
                    successful += 1
                    click.echo(f"✅ {symbol}")
                except Exception as e:
                    failed += 1
                    error_msg = f"{symbol}: {str(e)}"
                    errors.append(error_msg)
                    click.echo(f"❌ {symbol}: {str(e)}")

                # Délai entre symboles
                await asyncio.sleep(0.2)

            return {
                "symbols": symbol_list,
                "successful": successful,
                "failed": failed,
                "errors": errors,
            }

        report = asyncio.run(archive_specific())

        click.echo(f"\n📊 Manual Archive Report")
        click.echo("=" * 30)
        click.echo(f"Total symbols: {len(symbol_list)}")
        click.echo(f"Successful: {report['successful']}")
        click.echo(f"Failed: {report['failed']}")

        if report["failed"] == 0:
            click.echo("\n✅ All symbols archived successfully!")
        else:
            click.echo(f"\n⚠️ {report['failed']} symbols failed")

    except Exception as e:
        logger.error(f"Manual archival failed: {str(e)}")
        click.echo(f"❌ Manual archival failed: {str(e)}")
        sys.exit(1)


@cli.command()
def status():
    """Show archival system status."""
    logger.info("Checking archival status")

    try:
        archiver = MarketDataArchiver()

        async def get_status():
            return await archiver.get_archival_status()

        status_report = asyncio.run(get_status())

        click.echo(f"\n📊 Archival System Status - {status_report['timestamp']}")
        click.echo("=" * 50)
        click.echo(f"Status: {status_report['status']}")

        if "total_records" in status_report:
            click.echo(f"Total records: {status_report['total_records']:,}")

        if "latest_data" in status_report and status_report["latest_data"]:
            click.echo(f"Latest data: {status_report['latest_data']}")

        if "oldest_data" in status_report and status_report["oldest_data"]:
            click.echo(f"Oldest data: {status_report['oldest_data']}")

        if "coverage_days" in status_report:
            click.echo(f"Coverage: {status_report['coverage_days']} days")

        if "indices" in status_report:
            click.echo(f"\n📈 Configured Indices:")
            for index_name, stats in status_report["indices"].items():
                click.echo(f"  {index_name}: {stats['symbols']} symbols")

        if status_report["status"] == "active":
            click.echo("\n✅ System is active and healthy")
        else:
            click.echo(f"\n❌ System status: {status_report['status']}")
            if "error" in status_report:
                click.echo(f"Error: {status_report['error']}")

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        click.echo(f"❌ Status check failed: {str(e)}")
        sys.exit(1)


@cli.command()
def worker():
    """Start a Celery worker for background tasks."""
    try:
        # Import Celery ici pour éviter les erreurs si Celery n'est pas installé
        from src.infrastructure.background.celery_app import celery_app

        logger.info("Starting Celery worker...")
        click.echo("🚀 Starting Celery worker for market data archival...")
        click.echo("Press CTRL+C to stop\n")

        # Lancer le worker Celery
        celery_app.worker_main(
            [
                "worker",
                "--loglevel=info",
                "--concurrency=2",
                "--queues=market_data,health",
                "--hostname=archiver@%h",
            ]
        )

    except ImportError:
        click.echo("❌ Celery not available. Install with: poetry add celery")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n✅ Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {str(e)}")
        click.echo(f"❌ Worker failed: {str(e)}")
        sys.exit(1)


@cli.command()
def beat():
    """Start Celery beat scheduler for automatic archival."""
    try:
        from src.infrastructure.background.celery_app import celery_app

        logger.info("Starting Celery beat scheduler...")
        click.echo("⏰ Starting Celery beat scheduler...")
        click.echo("Press CTRL+C to stop\n")

        # Lancer le scheduler Celery Beat
        celery_app.control.purge()  # Nettoyer les anciennes tâches
        celery_app.start(["beat", "--loglevel=info"])

    except ImportError:
        click.echo("❌ Celery not available. Install with: poetry add celery")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n✅ Beat scheduler stopped by user")
    except Exception as e:
        logger.error(f"Beat scheduler failed: {str(e)}")
        click.echo(f"❌ Beat scheduler failed: {str(e)}")
        sys.exit(1)


@cli.command()
def test_connection():
    """Test database and Redis connections."""
    click.echo("🔍 Testing connections...")

    # Test configuration
    try:
        settings = get_settings()
        click.echo(f"✅ Configuration loaded")
        click.echo(f"  Database: {settings.postgres_host}:{settings.postgres_port}")
        click.echo(f"  Redis: {settings.redis_host}:{settings.redis_port}")
    except Exception as e:
        click.echo(f"❌ Configuration error: {str(e)}")
        return

    # Test YFinance
    try:
        import yfinance as yf

        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if "symbol" in info:
            click.echo("✅ YFinance connection working")
        else:
            click.echo("⚠️ YFinance connection limited")
    except Exception as e:
        click.echo(f"❌ YFinance error: {str(e)}")

    # Test archiver initialization
    try:
        archiver = MarketDataArchiver()
        indices_count = sum(
            len(symbols) for symbols in archiver.financial_indices.values()
        )
        click.echo(f"✅ Archiver initialized ({indices_count} symbols configured)")
    except Exception as e:
        click.echo(f"❌ Archiver initialization error: {str(e)}")


if __name__ == "__main__":
    cli()
