"""FastAPI application with real YFinance data and advanced investment analysis."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our advanced analysis services
try:
    from src.application.services.investment_recommendation_service import (
        InvestmentRecommendationService,
        PortfolioRecommendation,
        RecommendationRequest,
    )

    ADVANCED_ANALYSIS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced analysis not available: {e}")
    ADVANCED_ANALYSIS_AVAILABLE = False


# Pydantic models for API
class HealthCheckResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    real_data_tests: Dict[str, Any]
    summary: Dict[str, Any]


class TickerInfoResponse(BaseModel):
    """Ticker information response model."""

    symbol: str
    info: Dict[str, Any]
    current_price: Optional[float] = None
    currency: Optional[str] = None
    last_updated: str


# Initialize FastAPI app
app = FastAPI(
    title="Boursa Vision - Advanced Investment Analysis API",
    description="Real financial data with comprehensive analysis using YFinance and advanced algorithms",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
    ],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize recommendation service
if ADVANCED_ANALYSIS_AVAILABLE:
    recommendation_service = InvestmentRecommendationService()

# Financial indices registry
FINANCIAL_INDICES = {
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
        "EON.DE",
        "QIA.DE",
        "ZAL.DE",
        "SAR.DE",
        "PUM.DE",
        "WCH.DE",
        "PFV.DE",
        "HAB.DE",
        "FME.DE",
        "FRE.DE",
        "SRT.DE",
        "AIX.DE",
        "BNR.DE",
        "P911.DE",
        "MRK.DE",
    ],
}


def test_real_data_connection() -> Dict[str, Any]:
    """Test real data connection with sample symbols."""
    test_symbols = ["SHEL.L", "AMGN", "NVDA"]  # UK, US, US tech
    test_results = {}

    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")

            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                currency = info.get("currency", "USD")
                test_results[symbol] = {
                    "success": True,
                    "price": round(current_price, 2),
                    "currency": currency,
                }
            else:
                test_results[symbol] = {"success": False, "error": "No historical data"}

        except Exception as e:
            test_results[symbol] = {"success": False, "error": str(e)}

    return test_results


@app.get("/", response_model=Dict[str, Any])
def get_api_info():
    """Get API information and status."""
    return {
        "service": "Boursa Vision - Advanced Investment Analysis API",
        "version": "2.0.0",
        "description": "Real financial data with comprehensive analysis using YFinance and advanced algorithms",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "configuration": {
            "enabled_indices": list(FINANCIAL_INDICES.keys()),
            "total_symbols": sum(
                len(symbols) for symbols in FINANCIAL_INDICES.values()
            ),
            "advanced_analysis_available": ADVANCED_ANALYSIS_AVAILABLE,
        },
        "endpoints": {
            "health": "/health",
            "ticker_info": "/ticker/{symbol}/info",
            "ticker_history": "/ticker/{symbol}/history",
            "indices": "/indices",
            "best_investments": "/recommendations/best-investments"
            if ADVANCED_ANALYSIS_AVAILABLE
            else "Not available",
        },
    }


@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    """Comprehensive health check with real data tests."""
    test_results = test_real_data_connection()

    # Check if all tests passed
    all_tests_passed = all(
        result.get("success", False) for result in test_results.values()
    )

    return HealthCheckResponse(
        status="healthy" if all_tests_passed else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        real_data_tests=test_results,
        summary={
            "all_tests_passed": all_tests_passed,
            "enabled_indices": list(FINANCIAL_INDICES.keys()),
            "total_available_symbols": sum(
                len(symbols) for symbols in FINANCIAL_INDICES.values()
            ),
            "advanced_analysis_available": ADVANCED_ANALYSIS_AVAILABLE,
        },
    )


@app.get("/ticker/{symbol}/info", response_model=TickerInfoResponse)
def get_ticker_info(symbol: str):
    """Get detailed information for a specific ticker."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        if not info:
            raise HTTPException(
                status_code=404, detail=f"No data found for symbol: {symbol}"
            )

        # Get current price from recent history
        hist = ticker.history(period="1d")
        current_price = None
        if not hist.empty:
            current_price = float(hist["Close"].iloc[-1])

        return TickerInfoResponse(
            symbol=symbol,
            info=info,
            current_price=current_price,
            currency=info.get("currency"),
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching data for {symbol}: {str(e)}"
        )


@app.get("/ticker/{symbol}/history")
def get_ticker_history(
    symbol: str,
    period: str = Query(
        "1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    ),
    interval: str = Query(
        "1d",
        description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo",
    ),
):
    """Get historical data for a specific ticker."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            raise HTTPException(
                status_code=404, detail=f"No historical data found for symbol: {symbol}"
            )

        # Convert to JSON-serializable format
        history_data = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": hist.reset_index().to_dict("records"),
            "metadata": {
                "total_records": len(hist),
                "start_date": hist.index[0].isoformat() if not hist.empty else None,
                "end_date": hist.index[-1].isoformat() if not hist.empty else None,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        }

        return history_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching history for {symbol}: {str(e)}"
        )


@app.get("/indices")
def get_available_indices():
    """Get all available financial indices and their symbols."""
    indices_info = {}

    for index_name, symbols in FINANCIAL_INDICES.items():
        indices_info[index_name] = {
            "name": index_name.upper(),
            "symbol_count": len(symbols),
            "symbols": symbols,
            "sample_symbols": symbols[:5],  # Show first 5 as sample
        }

    return {
        "total_indices": len(FINANCIAL_INDICES),
        "total_symbols": sum(len(symbols) for symbols in FINANCIAL_INDICES.values()),
        "indices": indices_info,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


if ADVANCED_ANALYSIS_AVAILABLE:

    @app.get("/recommendations/best-investments")
    def get_best_investment_recommendations(
        symbols: Optional[str] = Query(
            None,
            description="Comma-separated symbols to analyze (if None, analyzes all indices)",
        ),
        max_recommendations: int = Query(
            10, ge=1, le=50, description="Maximum number of recommendations"
        ),
        risk_tolerance: str = Query(
            "MODERATE", description="Risk tolerance: LOW, MODERATE, HIGH"
        ),
        investment_horizon: str = Query(
            "MEDIUM", description="Investment horizon: SHORT, MEDIUM, LONG"
        ),
        exclude_sectors: Optional[str] = Query(
            None, description="Comma-separated sectors to exclude"
        ),
        min_score: float = Query(
            60.0, ge=0, le=100, description="Minimum investment score"
        ),
        max_risk_level: str = Query(
            "HIGH",
            description="Maximum risk level: VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH",
        ),
    ) -> Dict[str, Any]:
        """
        🎯 Get the best investment recommendations based on comprehensive analysis.

        This endpoint performs advanced financial analysis using:
        - Technical Analysis (RSI, MACD, Moving Averages, Bollinger Bands, Volume)
        - Fundamental Analysis (P/E, ROE, Growth, Debt ratios, Margins, Dividends)
        - Momentum Analysis (Price trends, Volatility, Trend consistency)
        - Risk Assessment and Portfolio Optimization

        Returns ranked investment recommendations with detailed insights.
        """
        try:
            # Parse symbols from comma-separated string
            symbols_list = None
            if symbols:
                symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]

            # Parse exclude_sectors from comma-separated string
            exclude_sectors_list = []
            if exclude_sectors:
                exclude_sectors_list = [
                    s.strip() for s in exclude_sectors.split(",") if s.strip()
                ]

            # Convert Query parameters to our service model
            service_request = RecommendationRequest(
                symbols=symbols_list,
                max_recommendations=max_recommendations,
                risk_tolerance=risk_tolerance,
                investment_horizon=investment_horizon,
                exclude_sectors=exclude_sectors_list,
                min_score=min_score,
                max_risk_level=max_risk_level,
            )

            # Generate recommendations
            portfolio_recommendation = (
                recommendation_service.get_investment_recommendations(service_request)
            )

            # Convert to API response format
            response = {
                "status": "success",
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "request_parameters": {
                    "symbols": symbols_list,
                    "max_recommendations": max_recommendations,
                    "risk_tolerance": risk_tolerance,
                    "investment_horizon": investment_horizon,
                    "exclude_sectors": exclude_sectors_list,
                    "min_score": min_score,
                    "max_risk_level": max_risk_level,
                },
                "recommendations": [
                    {
                        "rank": idx + 1,
                        "symbol": rec.symbol,
                        "recommendation": rec.recommendation,
                        "overall_score": round(rec.overall_score, 2),
                        "confidence": round(rec.confidence, 3),
                        "risk_level": rec.risk_level,
                        "scores": {
                            "technical": round(rec.technical_score, 2),
                            "fundamental": round(rec.fundamental_score, 2),
                            "momentum": round(rec.momentum_score, 2),
                        },
                        "price_targets": {
                            "current": rec.current_price,
                            "target": rec.target_price,
                            "stop_loss": rec.stop_loss,
                            "upside_potential_pct": round(rec.upside_potential, 2)
                            if rec.upside_potential
                            else None,
                        },
                        "analysis": {
                            "strengths": rec.strengths,
                            "weaknesses": rec.weaknesses,
                            "key_insights": rec.key_insights,
                            "data_quality": rec.data_quality,
                        },
                    }
                    for idx, rec in enumerate(portfolio_recommendation.recommendations)
                ],
                "portfolio_analysis": {
                    "metrics": portfolio_recommendation.portfolio_metrics,
                    "risk_assessment": portfolio_recommendation.risk_assessment,
                    "sector_allocation": portfolio_recommendation.sector_allocation,
                    "summary": portfolio_recommendation.analysis_summary,
                },
                "methodology": {
                    "technical_indicators": [
                        "RSI",
                        "MACD",
                        "Moving Averages",
                        "Bollinger Bands",
                        "Volume Analysis",
                    ],
                    "fundamental_metrics": [
                        "P/E Ratio",
                        "ROE",
                        "Revenue Growth",
                        "Debt Ratios",
                        "Profit Margins",
                        "Dividend Yield",
                    ],
                    "risk_factors": [
                        "Volatility",
                        "Beta",
                        "Debt Levels",
                        "Market Cap",
                        "Sector Risk",
                    ],
                    "data_sources": ["Yahoo Finance", "Real-time Market Data"],
                    "analysis_weights": {
                        "technical": "25%",
                        "fundamental": "30%",
                        "momentum": "15%",
                        "value": "15%",
                        "growth": "10%",
                        "quality": "5%",
                    },
                },
            }

            return response

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating investment recommendations: {str(e)}",
            )

    @app.get("/recommendations/quick-analysis/{symbol}")
    def get_quick_symbol_analysis(symbol: str) -> Dict[str, Any]:
        """Get quick analysis for a single symbol."""
        try:
            # Use the recommendation service to analyze single symbol
            service_request = RecommendationRequest(
                symbols=[symbol],
                max_recommendations=1,
                min_score=0.0,  # Accept any score for single symbol analysis
            )

            portfolio_recommendation = (
                recommendation_service.get_investment_recommendations(service_request)
            )

            if not portfolio_recommendation.recommendations:
                raise HTTPException(
                    status_code=404,
                    detail=f"No analysis available for symbol: {symbol}",
                )

            rec = portfolio_recommendation.recommendations[0]

            return {
                "symbol": symbol,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendation": rec.recommendation,
                "overall_score": round(rec.overall_score, 2),
                "confidence": round(rec.confidence, 3),
                "risk_level": rec.risk_level,
                "detailed_scores": {
                    "technical": round(rec.technical_score, 2),
                    "fundamental": round(rec.fundamental_score, 2),
                    "momentum": round(rec.momentum_score, 2),
                },
                "insights": {
                    "strengths": rec.strengths,
                    "weaknesses": rec.weaknesses,
                    "key_insights": rec.key_insights,
                },
                "price_analysis": {
                    "current_price": rec.current_price,
                    "target_price": rec.target_price,
                    "stop_loss": rec.stop_loss,
                    "upside_potential_pct": round(rec.upside_potential, 2)
                    if rec.upside_potential
                    else None,
                },
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error analyzing symbol {symbol}: {str(e)}"
            )

else:

    @app.get("/recommendations/best-investments")
    def best_investments_not_available():
        """Placeholder when advanced analysis is not available."""
        return {
            "error": "Advanced investment analysis not available",
            "reason": "Required dependencies not installed",
            "basic_data_available": True,
            "message": "Use /ticker/{symbol}/info and /ticker/{symbol}/history for basic data",
        }
