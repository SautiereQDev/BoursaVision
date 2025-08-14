#!"""FastAPI application with real YFinance data and advanced investment analysis."""

from datetime import datetime
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
class RecommendationRequestModel(BaseModel):
    """Request model for investment recommendations."""
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to analyze (if None, analyzes all indices)")
    max_recommendations: int = Field(10, ge=1, le=50, description="Maximum number of recommendations")
    risk_tolerance: str = Field("MODERATE", description="Risk tolerance: LOW, MODERATE, HIGH")
    investment_horizon: str = Field("MEDIUM", description="Investment horizon: SHORT, MEDIUM, LONG")
    exclude_sectors: List[str] = Field(default_factory=list, description="Sectors to exclude")
    min_score: float = Field(60.0, ge=0, le=100, description="Minimum investment score")
    max_risk_level: str = Field("HIGH", description="Maximum risk level: VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH")


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
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation service
if ADVANCED_ANALYSIS_AVAILABLE:
    recommendation_service = InvestmentRecommendationService()

# Financial indices registry
FINANCIAL_INDICES = {
    "cac40": [
        'MC.PA', 'ASML.AS', 'OR.PA', 'SAP', 'TTE.PA', 'RMS.PA', 'INGA.AS',
        'SAN.PA', 'BNP.PA', 'AIR.PA', 'SU.PA', 'BN.PA', 'DG.PA', 'EL.PA',
        'CAP.PA', 'ML.PA', 'ORA.PA', 'AI.PA', 'GLE.PA', 'LR.PA',
        'VIV.PA', 'KER.PA', 'PUB.PA', 'URW.AS', 'STM.PA', 'TEP.PA',
        'WLN.PA', 'EN.PA', 'ACA.PA', 'CS.PA', 'BIO.PA', 'SGO.PA',
        'SW.PA', 'ALO.PA', 'HO.PA', 'ATO.PA', 'RCO.PA', 'DBG.PA', 'STLA.PA', 'EDF.PA'
    ],
    "nasdaq100": [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA',
        'AVGO', 'COST', 'NFLX', 'TMUS', 'ASML', 'ADBE', 'PEP', 'CSCO',
        'LIN', 'TXN', 'QCOM', 'CMCSA', 'AMAT', 'AMD', 'AMGN', 'HON',
        'INTU', 'ISRG', 'BKNG', 'VRTX', 'ADP', 'SBUX', 'GILD', 'ADI',
        'MU', 'INTC', 'PYPL', 'REGN', 'MELI', 'LRCX', 'KLAC', 'SNPS',
        'CDNS', 'MRVL', 'ORLY', 'CSX', 'FTNT', 'ADSK', 'NXPI', 'WDAY',
        'ABNB', 'CHTR', 'TEAM', 'PCAR', 'CPRT', 'MNST', 'AEP', 'ROST',
        'FAST', 'KDP', 'EA', 'VRSK', 'ODFL', 'EXC', 'LULU', 'GEHC',
        'CTSH', 'XEL', 'FANG', 'CCEP', 'KHC', 'CSGP', 'DDOG', 'ZS',
        'BKR', 'DLTR', 'CRWD', 'ANSS', 'IDXX', 'ON', 'ILMN', 'BIIB',
        'GFS', 'CDW', 'MDB', 'WBD', 'ARM', 'MRNA', 'SMCI'
    ],
    "ftse100": [
        'SHEL.L', 'AZN.L', 'LSEG.L', 'UU.L', 'ULVR.L', 'BP.L', 'GSK.L',
        'VOD.L', 'LLOY.L', 'TSCO.L', 'PRU.L', 'BT-A.L', 'RIO.L',
        'BARC.L', 'DGE.L', 'NG.L', 'NWG.L', 'CRH.L', 'REL.L', 'GLEN.L'
    ],
    "dax40": [
        'SAP', 'ASML.AS', 'INGA.AS', 'URW.AS', 'SIE.DE', 'DTE.DE',
        'MBG.DE', 'ALV.DE', 'MUV2.DE', 'BAS.DE', 'BMW.DE', 'DB1.DE',
        'VOW3.DE', 'HEN3.DE', 'BEI.DE', 'ADS.DE', 'SHL.DE', 'VNA.DE',
        'DBK.DE', 'CON.DE', 'IFX.DE', 'MTX.DE', 'ENR.DE', 'HEI.DE',
        'RWE.DE', 'EON.DE', 'QIA.DE', 'ZAL.DE', 'SAR.DE', 'PUM.DE',
        'WCH.DE', 'PFV.DE', 'HAB.DE', 'FME.DE', 'FRE.DE', 'SRT.DE',
        'AIX.DE', 'BNR.DE', 'P911.DE', 'MRK.DE'
    ]
}


def test_real_data_connection() -> Dict[str, Any]:
    """Test real data connection with sample symbols."""
    test_symbols = ['SHEL.L', 'AMGN', 'NVDA']  # UK, US, US tech
    test_results = {}
    
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                currency = info.get('currency', 'USD')
                test_results[symbol] = {
                    "success": True,
                    "price": round(current_price, 2),
                    "currency": currency
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
        "timestamp": datetime.utcnow().isoformat(),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "configuration": {
            "enabled_indices": list(FINANCIAL_INDICES.keys()),
            "total_symbols": sum(len(symbols) for symbols in FINANCIAL_INDICES.values()),
            "advanced_analysis_available": ADVANCED_ANALYSIS_AVAILABLE
        },
        "endpoints": {
            "health": "/health",
            "ticker_info": "/ticker/{symbol}/info",
            "ticker_history": "/ticker/{symbol}/history",
            "indices": "/indices",
            "best_investments": "/recommendations/best-investments" if ADVANCED_ANALYSIS_AVAILABLE else "Not available"
        }
    }


@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    """Comprehensive health check with real data tests."""
    test_results = test_real_data_connection()
    
    # Check if all tests passed
    all_tests_passed = all(result.get("success", False) for result in test_results.values())
    
    return HealthCheckResponse(
        status="healthy" if all_tests_passed else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        real_data_tests=test_results,
        summary={
            "all_tests_passed": all_tests_passed,
            "enabled_indices": list(FINANCIAL_INDICES.keys()),
            "total_available_symbols": sum(len(symbols) for symbols in FINANCIAL_INDICES.values()),
            "advanced_analysis_available": ADVANCED_ANALYSIS_AVAILABLE
        }
    )


@app.get("/ticker/{symbol}/info", response_model=TickerInfoResponse)
def get_ticker_info(symbol: str):
    """Get detailed information for a specific ticker."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
        
        # Get current price from recent history
        hist = ticker.history(period="1d")
        current_price = None
        if not hist.empty:
            current_price = float(hist['Close'].iloc[-1])
        
        return TickerInfoResponse(
            symbol=symbol,
            info=info,
            current_price=current_price,
            currency=info.get('currency'),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data for {symbol}: {str(e)}")


@app.get("/ticker/{symbol}/history")
def get_ticker_history(
    symbol: str,
    period: str = Query("1mo", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query("1d", description="Interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo")
):
    """Get historical data for a specific ticker."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for symbol: {symbol}")
        
        # Convert to JSON-serializable format
        history_data = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": hist.reset_index().to_dict('records'),
            "metadata": {
                "total_records": len(hist),
                "start_date": hist.index[0].isoformat() if not hist.empty else None,
                "end_date": hist.index[-1].isoformat() if not hist.empty else None,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        return history_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history for {symbol}: {str(e)}")


@app.get("/indices")
def get_available_indices():
    """Get all available financial indices and their symbols."""
    indices_info = {}
    
    for index_name, symbols in FINANCIAL_INDICES.items():
        indices_info[index_name] = {
            "name": index_name.upper(),
            "symbol_count": len(symbols),
            "symbols": symbols,
            "sample_symbols": symbols[:5]  # Show first 5 as sample
        }
    
    return {
        "total_indices": len(FINANCIAL_INDICES),
        "total_symbols": sum(len(symbols) for symbols in FINANCIAL_INDICES.values()),
        "indices": indices_info,
        "last_updated": datetime.utcnow().isoformat()
    }


if ADVANCED_ANALYSIS_AVAILABLE:
    @app.post("/recommendations/best-investments")
    def get_best_investment_recommendations(request: RecommendationRequestModel) -> Dict[str, Any]:
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
            # Convert Pydantic model to our service model
            service_request = RecommendationRequest(
                symbols=request.symbols,
                max_recommendations=request.max_recommendations,
                risk_tolerance=request.risk_tolerance,
                investment_horizon=request.investment_horizon,
                exclude_sectors=request.exclude_sectors,
                min_score=request.min_score,
                max_risk_level=request.max_risk_level
            )
            
            # Generate recommendations
            portfolio_recommendation = recommendation_service.get_investment_recommendations(service_request)
            
            # Convert to API response format
            response = {
                "status": "success",
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "request_parameters": request.dict(),
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
                            "momentum": round(rec.momentum_score, 2)
                        },
                        "price_targets": {
                            "current": rec.current_price,
                            "target": rec.target_price,
                            "stop_loss": rec.stop_loss,
                            "upside_potential_pct": round(rec.upside_potential, 2) if rec.upside_potential else None
                        },
                        "analysis": {
                            "strengths": rec.strengths,
                            "weaknesses": rec.weaknesses,
                            "key_insights": rec.key_insights,
                            "data_quality": rec.data_quality
                        }
                    }
                    for idx, rec in enumerate(portfolio_recommendation.recommendations)
                ],
                "portfolio_analysis": {
                    "metrics": portfolio_recommendation.portfolio_metrics,
                    "risk_assessment": portfolio_recommendation.risk_assessment,
                    "sector_allocation": portfolio_recommendation.sector_allocation,
                    "summary": portfolio_recommendation.analysis_summary
                },
                "methodology": {
                    "technical_indicators": ["RSI", "MACD", "Moving Averages", "Bollinger Bands", "Volume Analysis"],
                    "fundamental_metrics": ["P/E Ratio", "ROE", "Revenue Growth", "Debt Ratios", "Profit Margins", "Dividend Yield"],
                    "risk_factors": ["Volatility", "Beta", "Debt Levels", "Market Cap", "Sector Risk"],
                    "data_sources": ["Yahoo Finance", "Real-time Market Data"],
                    "analysis_weights": {
                        "technical": "25%",
                        "fundamental": "30%",
                        "momentum": "15%",
                        "value": "15%",
                        "growth": "10%",
                        "quality": "5%"
                    }
                }
            }
            
            return response
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error generating investment recommendations: {str(e)}"
            )

    @app.get("/recommendations/quick-analysis/{symbol}")
    def get_quick_symbol_analysis(symbol: str) -> Dict[str, Any]:
        """Get quick analysis for a single symbol."""
        try:
            # Use the recommendation service to analyze single symbol
            service_request = RecommendationRequest(
                symbols=[symbol],
                max_recommendations=1,
                min_score=0.0  # Accept any score for single symbol analysis
            )
            
            portfolio_recommendation = recommendation_service.get_investment_recommendations(service_request)
            
            if not portfolio_recommendation.recommendations:
                raise HTTPException(status_code=404, detail=f"No analysis available for symbol: {symbol}")
            
            rec = portfolio_recommendation.recommendations[0]
            
            return {
                "symbol": symbol,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "recommendation": rec.recommendation,
                "overall_score": round(rec.overall_score, 2),
                "confidence": round(rec.confidence, 3),
                "risk_level": rec.risk_level,
                "detailed_scores": {
                    "technical": round(rec.technical_score, 2),
                    "fundamental": round(rec.fundamental_score, 2),
                    "momentum": round(rec.momentum_score, 2)
                },
                "insights": {
                    "strengths": rec.strengths,
                    "weaknesses": rec.weaknesses,
                    "key_insights": rec.key_insights
                },
                "price_analysis": {
                    "current_price": rec.current_price,
                    "target_price": rec.target_price,
                    "stop_loss": rec.stop_loss,
                    "upside_potential_pct": round(rec.upside_potential, 2) if rec.upside_potential else None
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error analyzing symbol {symbol}: {str(e)}"
            )

else:
    @app.get("/recommendations/best-investments")
    def best_investments_not_available():
        """Placeholder when advanced analysis is not available."""
        return {
            "error": "Advanced investment analysis not available",
            "reason": "Required dependencies not installed",
            "basic_data_available": True,
            "message": "Use /ticker/{symbol}/info and /ticker/{symbol}/history for basic data"
        }r/bin/env python3
"""
FastAPI Simple avec YFinance - Alternative à production_api_with_real_data.py
Documentation automatique avec FastAPI /docs
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION DES INDICES FINANCIERS
# =============================================================================

class FinancialIndicesRegistry:
    """Registre des indices financiers supportés"""
    
    INDICES = {
        "cac40": {
            "name": "CAC 40",
            "symbols": ["MC.PA", "OR.PA", "BNP.PA", "AI.PA", "SAN.PA", "AIR.PA", "SU.PA", 
                       "TTE.PA", "BN.PA", "CAP.PA", "KER.PA", "LR.PA", "RMS.PA", "DSY.PA",
                       "EL.PA", "CS.PA", "SGO.PA", "DG.PA", "VIE.PA", "VIV.PA", "WLN.PA", 
                       "ALO.PA", "MT.AS", "STLA.PA", "ST.PA", "UG.PA", "ORA.PA"],
            "currency": "EUR"
        },
        "nasdaq100": {
            "name": "NASDAQ 100", 
            "symbols": ["AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", 
                       "AVGO", "COST", "NFLX", "TMUS", "CSCO", "ADBE", "PEP", "AMD", "LIN",
                       "TXN", "QCOM", "INTU", "AMAT", "ISRG", "CMCSA", "BKNG", "HON", "AMGN",
                       "VRTX", "ADP", "PANW", "GILD", "ADI", "SBUX", "MU", "INTC", "PYPL",
                       "REGN", "LRCX", "KLAC", "SNPS", "CDNS", "MRVL", "CSX", "ORLY", "CTAS", "FTNT", "NXPI"],
            "currency": "USD"
        },
        "ftse100": {
            "name": "FTSE 100",
            "symbols": ["SHEL.L", "AZN.L", "LSEG.L", "UU.L", "ULVR.L", "BP.L", "RIO.L", 
                       "HSBA.L", "VODJ.L", "GLEN.L", "BT-A.L", "LLOY.L", "BARC.L", "GSK.L",
                       "TSCO.L", "NG.L", "PRU.L", "NWG.L"],
            "currency": "GBP"
        },
        "dax40": {
            "name": "DAX 40",
            "symbols": ["SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "MUV2.DE", "BAS.DE", "BAYN.DE",
                       "BMW.DE", "DAI.DE", "VOW3.DE", "FRE.DE", "HEI.DE", "LIN.DE", "MRK.DE",
                       "RWE.DE", "CON.DE", "VNA.DE", "IFX.DE"],
            "currency": "EUR"
        }
    }
    
    def __init__(self):
        self.enabled_indices = self._load_enabled_indices()
    
    def _load_enabled_indices(self) -> List[str]:
        enabled_env = os.getenv("ENABLED_MARKET_INDICES", "cac40,nasdaq100,ftse100,dax40")
        enabled = [idx.strip().lower() for idx in enabled_env.split(",")]
        valid_indices = [idx for idx in enabled if idx in self.INDICES]
        
        if not valid_indices:
            return ["cac40", "nasdaq100"]
        
        logger.info(f"Enabled indices: {valid_indices}")
        return valid_indices
    
    def get_all_symbols(self) -> List[str]:
        all_symbols = []
        for index_key in self.enabled_indices:
            all_symbols.extend(self.INDICES[index_key]["symbols"])
        return list(set(all_symbols))

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Initialisation du registre
indices_registry = FinancialIndicesRegistry()

# Création de l'application FastAPI
app = FastAPI(
    title="Boursa Vision - Financial Data API",
    description="Production API with real YFinance data and automatic documentation",
    version="1.0.0",
    docs_url="/docs",  # Documentation Swagger
    redoc_url="/redoc"  # Documentation ReDoc alternative
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", tags=["Documentation"])
async def root():
    """API Information and endpoints overview"""
    return {
        "service": "Boursa Vision - FastAPI Production API",
        "version": "1.0.0",
        "description": "Real financial data using YFinance with FastAPI automatic documentation",
        "timestamp": datetime.now().isoformat(),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "configuration": {
            "enabled_indices": indices_registry.enabled_indices,
            "total_symbols": len(indices_registry.get_all_symbols()),
            "data_source": "YFinance Real Data"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check with real market data test"""
    test_symbols = indices_registry.get_all_symbols()[:3]
    test_results = {}
    
    for symbol in test_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('regularMarketPrice', 0)
            
            test_results[symbol] = {
                "success": current_price > 0,
                "price": current_price,
                "currency": info.get('currency', 'USD')
            }
        except Exception as e:
            test_results[symbol] = {
                "success": False,
                "error": str(e)
            }
    
    all_success = all(r["success"] for r in test_results.values())
    
    return {
        "status": "healthy" if all_success else "degraded",
        "timestamp": datetime.now().isoformat(),
        "real_data_tests": test_results,
        "summary": {
            "all_tests_passed": all_success,
            "enabled_indices": indices_registry.enabled_indices,
            "total_symbols": len(indices_registry.get_all_symbols())
        },
        "data_source": "YFinance Real API"
    }

@app.get("/indices", tags=["Market Data"])
async def get_indices():
    """Get available market indices information"""
    result = {}
    for index_key in indices_registry.enabled_indices:
        config = indices_registry.INDICES[index_key]
        result[index_key] = {
            "name": config["name"], 
            "currency": config["currency"],
            "symbols_count": len(config["symbols"]),
            "sample_symbols": config["symbols"][:5]
        }
    return {"enabled_indices": result}

@app.get("/symbols", tags=["Market Data"])
async def get_symbols():
    """Get all supported financial symbols"""
    return {
        "symbols": indices_registry.get_all_symbols(),
        "total_count": len(indices_registry.get_all_symbols()),
        "grouped_by_index": {
            index_key: indices_registry.INDICES[index_key]["symbols"]
            for index_key in indices_registry.enabled_indices
        }
    }

@app.get("/ticker/{symbol}/info", tags=["Market Data"])
async def get_ticker_info(symbol: str):
    """Get real-time information for a specific ticker symbol"""
    if symbol not in indices_registry.get_all_symbols():
        raise HTTPException(
            status_code=404, 
            detail=f"Symbol {symbol} not supported in enabled indices"
        )
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="2d")
        
        if not info or hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        current_price = info.get('regularMarketPrice') or hist['Close'].iloc[-1]
        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        change = current_price - previous_price
        change_percent = (change / previous_price * 100) if previous_price > 0 else 0
        
        return {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "price": float(current_price),
            "currency": info.get('currency', 'USD'),
            "exchange": info.get('exchange', 'Unknown'),
            "sector": info.get('sector', 'Unknown'),
            "market_cap": info.get('marketCap'),
            "pe_ratio": info.get('forwardPE', info.get('trailingPE')),
            "change": float(change),
            "change_percent": float(change_percent),
            "last_update": datetime.now().isoformat(),
            "data_source": "yfinance_real"
        }
        
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        raise HTTPException(status_code=503, detail=f"Error fetching data for {symbol}")

@app.get("/tickers/info", tags=["Market Data"])
async def get_multiple_tickers(symbols: str):
    """Get information for multiple ticker symbols (comma-separated)"""
    symbol_list = [s.strip() for s in symbols.split(',')]
    
    # Validate symbols
    supported_symbols = [s for s in symbol_list if s in indices_registry.get_all_symbols()]
    unsupported = [s for s in symbol_list if s not in supported_symbols]
    
    results = {}
    
    # Fetch data for supported symbols
    for symbol in supported_symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = info.get('regularMarketPrice', 0)
            
            results[symbol] = {
                "symbol": symbol,
                "name": info.get('longName', symbol),
                "price": float(current_price) if current_price else None,
                "currency": info.get('currency', 'USD'),
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            results[symbol] = {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }
    
    return {
        "results": results,
        "summary": {
            "requested": len(symbol_list),
            "supported": len(supported_symbols),
            "unsupported": unsupported,
            "successful": len([r for r in results.values() if "error" not in r])
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('API_PORT', '8000'))
    uvicorn.run(app, host="0.0.0.0", port=port)
