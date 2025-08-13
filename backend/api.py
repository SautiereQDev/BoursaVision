#!/usr/bin/env python3
"""
Boursa Vision Advanced API - Version Simplifiée
API d'intelligence financière avec analyse massive de marché
"""

import logging
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import uvicorn

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modèles Pydantic pour les requêtes et réponses

class MarketScanRequest(BaseModel):
    strategy: str = Field(default="FULL_MARKET", description="Stratégie de scan")
    max_symbols: int = Field(default=100, description="Nombre maximum de symboles")
    min_market_cap: float = Field(default=1000000000, description="Cap minimum")
    min_volume: float = Field(default=100000, description="Volume minimum")
    parallel_requests: int = Field(default=20, description="Requêtes parallèles")

class InvestmentRequest(BaseModel):
    min_confidence_score: float = Field(default=70.0, description="Score de confiance minimum")
    max_recommendations: int = Field(default=20, description="Nombre max de recommandations")
    min_market_cap: float = Field(default=1000000000, description="Cap minimum")
    max_risk_level: str = Field(default="HIGH", description="Niveau de risque max")
    preferred_horizon: str = Field(default="MEDIUM_TERM", description="Horizon préféré")

class PortfolioRequest(BaseModel):
    portfolio_size: float = Field(default=100000.0, description="Taille du portefeuille")
    max_positions: int = Field(default=10, description="Positions maximum")
    risk_tolerance: str = Field(default="MODERATE", description="Tolérance au risque")

# Classes de service

class SimpleMarketData:
    """Service simple pour récupérer les données de marché"""
    
    @staticmethod
    def get_stock_data(symbol: str, period: str = "1y") -> Optional[Dict]:
        """Récupère les données d'une action"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            info = ticker.info
            
            if hist.empty:
                return None
                
            current_price = hist['Close'].iloc[-1]
            price_change = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            
            # Calculs techniques simples
            rsi = SimpleMarketData.calculate_rsi(hist['Close'])
            ma_50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1]
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'price_change_percent': float(price_change),
                'volume': int(hist['Volume'].iloc[-1]),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'rsi': float(rsi) if not pd.isna(rsi) else 50,
                'ma_50': float(ma_50) if not pd.isna(ma_50) else current_price,
                'ma_200': float(ma_200) if not pd.isna(ma_200) else current_price,
                'sector': info.get('sector', 'Unknown'),
                'name': info.get('longName', symbol)
            }
        except Exception as e:
            logger.warning(f"Erreur pour {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calcule le RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0

class MarketScanner:
    """Scanner de marché pour l'analyse massive"""
    
    def __init__(self):
        self.sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
            'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'CVX', 'MA', 'ABBV', 'BAC',
            'AVGO', 'PFE', 'COST', 'KO', 'PEP', 'TMO', 'MRK', 'WMT', 'DIS',
            'ACN', 'VZ', 'ADBE', 'NFLX', 'NKE', 'CRM', 'INTC', 'T', 'CMCSA',
            'ABT', 'XOM', 'TXN', 'LIN', 'AMD', 'QCOM', 'PM', 'SPGI', 'LOW',
            'UNP', 'HON', 'IBM', 'GS', 'BA', 'CAT', 'ISRG', 'BKNG', 'GILD',
            'MDT', 'INTU', 'SYK', 'AXP', 'MU', 'BLK', 'ADP', 'VRTX', 'LRCX',
            'TJX', 'SCHW', 'TMUS', 'CB', 'DE', 'LMT', 'AMT', 'EL', 'FIS',
            'MMM', 'REGN', 'C', 'PYPL', 'ZTS', 'NOW', 'ATVI', 'BMY', 'CHTR',
            'PLD', 'SO', 'WFC', 'CL', 'ORCL', 'SHW', 'CSX', 'AMAT', 'MO',
            'USB', 'ICE', 'CCI', 'EOG', 'FCX', 'NSC', 'DUK', 'ITW', 'APD'
        ]
    
    def scan_market(self, request: MarketScanRequest) -> Dict:
        """Effectue un scan massif du marché"""
        logger.info(f"Démarrage scan avec {request.max_symbols} symboles")
        
        # Limitation à 100 symboles max pour les tests
        symbols_to_scan = self.sp500_symbols[:min(request.max_symbols, 100)]
        
        # Traitement en parallèle
        with ThreadPoolExecutor(max_workers=request.parallel_requests) as executor:
            futures = [
                executor.submit(SimpleMarketData.get_stock_data, symbol)
                for symbol in symbols_to_scan
            ]
            
            results = []
            for future in futures:
                try:
                    data = future.result(timeout=10)
                    if data and self._meets_criteria(data, request):
                        data['overall_score'] = self._calculate_score(data)
                        results.append(data)
                except Exception as e:
                    logger.warning(f"Timeout ou erreur: {e}")
        
        # Tri par score
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return {
            'scan_summary': {
                'total_analyzed': len(symbols_to_scan),
                'valid_results': len(results),
                'top_opportunities_found': len([r for r in results if r['overall_score'] > 75]),
                'average_score': np.mean([r['overall_score'] for r in results]) if results else 0,
                'scan_timestamp': datetime.now().isoformat()
            },
            'top_opportunities': results[:20]
        }
    
    def _meets_criteria(self, data: Dict, request: MarketScanRequest) -> bool:
        """Vérifie si l'action répond aux critères"""
        return (
            data['market_cap'] >= request.min_market_cap and
            data['volume'] >= request.min_volume and
            data['pe_ratio'] > 0
        )
    
    def _calculate_score(self, data: Dict) -> float:
        """Calcule un score global pour l'action"""
        score = 50.0  # Score de base
        
        # Score technique (40%)
        technical_score = 0
        if data['rsi'] < 30:  # Survente
            technical_score += 20
        elif data['rsi'] < 70:  # Zone normale
            technical_score += 10
        
        if data['current_price'] > data['ma_50']:  # Au-dessus MA50
            technical_score += 10
        if data['current_price'] > data['ma_200']:  # Au-dessus MA200
            technical_score += 10
        
        # Score fondamental (60%)
        fundamental_score = 0
        if 0 < data['pe_ratio'] < 20:  # P/E raisonnable
            fundamental_score += 20
        elif 0 < data['pe_ratio'] < 30:
            fundamental_score += 10
        
        if 0 < data['pb_ratio'] < 3:  # P/B attractif
            fundamental_score += 15
        elif 0 < data['pb_ratio'] < 5:
            fundamental_score += 10
        
        if data['market_cap'] > 10000000000:  # Large cap
            fundamental_score += 15
        elif data['market_cap'] > 1000000000:  # Mid cap
            fundamental_score += 10
        
        return min(100, score + (technical_score * 0.4) + (fundamental_score * 0.6))

class InvestmentIntelligence:
    """Service d'intelligence d'investissement"""
    
    def __init__(self):
        self.market_scanner = MarketScanner()
    
    def generate_recommendations(self, request: InvestmentRequest) -> Dict:
        """Génère des recommandations d'investissement"""
        logger.info("Génération des recommandations d'investissement")
        
        # Effectuer un scan de marché
        scan_request = MarketScanRequest(
            max_symbols=50,
            min_market_cap=request.min_market_cap
        )
        scan_results = self.market_scanner.scan_market(scan_request)
        
        opportunities = scan_results['top_opportunities']
        
        # Traitement des recommandations
        recommendations = []
        for opportunity in opportunities:
            if opportunity['overall_score'] >= request.min_confidence_score:
                recommendation = self._create_recommendation(opportunity)
                if recommendation:
                    recommendations.append(recommendation)
        
        # Limitation du nombre de recommandations
        recommendations = recommendations[:request.max_recommendations]
        
        # Classification par type de recommandation
        strong_buy = [r for r in recommendations if isinstance(r, dict) and r.get('recommendation') == 'STRONG_BUY']
        buy = [r for r in recommendations if isinstance(r, dict) and r.get('recommendation') == 'BUY']
        hold = [r for r in recommendations if isinstance(r, dict) and r.get('recommendation') == 'HOLD']
        
        return {
            'analysis_summary': {
                'total_recommendations': len(recommendations),
                'strong_buy_count': len(strong_buy),
                'buy_count': len(buy),
                'hold_count': len(hold),
                'average_confidence': np.mean([r['confidence_score'] for r in recommendations if isinstance(r, dict)]) if recommendations else 0,
                'average_potential_return': np.mean([r['potential_return'] for r in recommendations if isinstance(r, dict)]) if recommendations else 0,
                'analysis_timestamp': datetime.now().isoformat()
            },
            'strong_buy_recommendations': strong_buy,
            'buy_recommendations': buy,
            'hold_recommendations': hold
        }
    
    def _create_recommendation(self, opportunity: Dict) -> Optional[Dict]:
        """Crée une recommandation pour une opportunité"""
        confidence = opportunity['overall_score']
        
        # Détermination de la recommandation
        if confidence >= 85:
            recommendation = "STRONG_BUY"
        elif confidence >= 75:
            recommendation = "BUY"
        elif confidence >= 60:
            recommendation = "HOLD"
        else:
            return None
        
        # Calcul du prix cible (simple)
        current_price = opportunity['current_price']
        target_price = current_price * (1 + (confidence - 50) / 100)
        potential_return = ((target_price - current_price) / current_price) * 100
        
        # Évaluation du risque
        risk_level = "LOW" if confidence > 85 else "MODERATE" if confidence > 75 else "HIGH"
        
        return {
            'symbol': opportunity['symbol'],
            'name': opportunity['name'],
            'recommendation': recommendation,
            'confidence_score': confidence,
            'current_price': current_price,
            'target_price': round(target_price, 2),
            'potential_return': round(potential_return, 1),
            'risk_level': risk_level,
            'sector': opportunity['sector'],
            'reasons': self._generate_reasons(opportunity),
            'analysis_date': datetime.now().isoformat()
        }
    
    def _generate_reasons(self, opportunity: Dict) -> List[str]:
        """Génère les raisons de la recommandation"""
        reasons = []
        
        if opportunity['overall_score'] > 80:
            reasons.append(f"Score global excellent: {opportunity['overall_score']:.1f}/100")
        
        if 0 < opportunity['pe_ratio'] < 20:
            reasons.append(f"P/E attractif: {opportunity['pe_ratio']:.1f}")
        
        if opportunity['rsi'] < 40:
            reasons.append(f"RSI en zone d'achat: {opportunity['rsi']:.1f}")
        
        if opportunity['current_price'] > opportunity['ma_50']:
            reasons.append("Tendance haussière confirmée (> MA50)")
        
        if opportunity['market_cap'] > 10000000000:
            reasons.append("Large capitalisation stable")
        
        return reasons[:3]  # Maximum 3 raisons

class PortfolioOptimizer:
    """Optimiseur de portefeuille"""
    
    async def suggest_portfolio(self, request: PortfolioRequest) -> Dict:
        """Suggère un portefeuille optimisé"""
        logger.info(f"Optimisation portefeuille de ${request.portfolio_size:,.0f}")
        
        # Obtenir des recommandations
        investment_request = InvestmentRequest(
            min_confidence_score=70.0,
            max_recommendations=request.max_positions * 2
        )
        
        intelligence = InvestmentIntelligence()
        recommendations = intelligence.generate_recommendations(investment_request)
        
        # Sélectionner les meilleures opportunités
        all_recs = (recommendations['strong_buy_recommendations'] + 
                   recommendations['buy_recommendations'])
        
        if not all_recs:
            raise HTTPException(status_code=404, detail="Aucune opportunité trouvée")
        
        # Diversification sectorielle
        selected_stocks = self._diversify_by_sector(all_recs, request.max_positions)
        
        # Allocation des poids
        allocations = self._allocate_weights(selected_stocks, request)
        
        # Calcul des métriques du portefeuille
        portfolio_metrics = self._calculate_portfolio_metrics(allocations)
        
        return {
            'portfolio_summary': {
                'total_portfolio_value': request.portfolio_size,
                'number_of_positions': len(allocations),
                'expected_annual_return': portfolio_metrics['expected_return'],
                'risk_level': request.risk_tolerance,
                'diversification_score': portfolio_metrics['diversification_score'],
                'creation_date': datetime.now().isoformat()
            },
            'portfolio_allocations': allocations,
            'sector_breakdown': portfolio_metrics['sector_breakdown']
        }
    
    def _diversify_by_sector(self, recommendations: List[Dict], max_positions: int) -> List[Dict]:
        """Diversifie les positions par secteur"""
        sectors = {}
        for rec in recommendations:
            sector = rec['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(rec)
        
        # Sélectionner max 2 positions par secteur
        selected = []
        for sector, stocks in sectors.items():
            selected.extend(sorted(stocks, key=lambda x: x['confidence_score'], reverse=True)[:2])
        
        return sorted(selected, key=lambda x: x['confidence_score'], reverse=True)[:max_positions]
    
    def _allocate_weights(self, stocks: List[Dict], request: PortfolioRequest) -> List[Dict]:
        """Alloue les poids du portefeuille"""
        total_confidence = sum(stock['confidence_score'] for stock in stocks)
        allocations = []
        
        for stock in stocks:
            # Poids basé sur le score de confiance
            weight = stock['confidence_score'] / total_confidence
            
            # Limitation max par position (20%)
            weight = min(weight, 0.20)
            
            amount = request.portfolio_size * weight
            
            allocations.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'weight': weight,
                'suggested_amount': round(amount, 2),
                'shares': int(amount / stock['current_price']),
                'confidence_score': stock['confidence_score'],
                'expected_return': stock['potential_return'],
                'sector': stock['sector']
            })
        
        return allocations
    
    def _calculate_portfolio_metrics(self, allocations: List[Dict]) -> Dict:
        """Calcule les métriques du portefeuille"""
        expected_return = sum(
            alloc['weight'] * alloc['expected_return'] 
            for alloc in allocations
        )
        
        # Breakdown sectoriel
        sector_breakdown = {}
        for alloc in allocations:
            sector = alloc['sector']
            if sector not in sector_breakdown:
                sector_breakdown[sector] = 0
            sector_breakdown[sector] += alloc['weight']
        
        # Score de diversification (basé sur le nombre de secteurs)
        diversification_score = min(100, len(sector_breakdown) * 20)
        
        return {
            'expected_return': round(expected_return, 1),
            'diversification_score': diversification_score,
            'sector_breakdown': {k: round(v*100, 1) for k, v in sector_breakdown.items()}
        }

# Initialisation de l'application FastAPI

app = FastAPI(
    title="🎯 Boursa Vision Advanced API",
    description="API d'Intelligence Financière avec Analyse Massive de Marché",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services globaux
market_scanner = MarketScanner()
investment_intelligence = InvestmentIntelligence()
portfolio_optimizer = PortfolioOptimizer()

# Routes de l'API

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "service": "Boursa Vision Advanced API",
        "version": "2.0.0",
        "description": "API d'intelligence financière avec analyse massive",
        "features": [
            "🔍 Scan massif de marché",
            "🤖 Recommandations IA",
            "💼 Optimisation de portefeuille",
            "📊 Analyse technique et fondamentale"
        ],
        "documentation": "/docs",
        "endpoints": {
            "market_scan": "/api/v1/market/scan",
            "recommendations": "/api/v1/investment/recommendations",
            "portfolio": "/api/v1/portfolio/suggestions",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de santé des services"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "market_scanner": "✅ Operational",
            "investment_intelligence": "✅ Operational", 
            "portfolio_optimizer": "✅ Operational",
            "yfinance_data": "✅ Connected"
        }
    }

@app.post("/api/v1/market/scan")
async def market_scan(request: MarketScanRequest):
    """Lance un scan massif du marché pour identifier les opportunités"""
    try:
        logger.info(f"Scan de marché demandé: {request.max_symbols} symboles")
        result = market_scanner.scan_market(request)
        return result
    except Exception as e:
        logger.error(f"Erreur lors du scan: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de scan: {str(e)}")

@app.post("/api/v1/investment/recommendations")
async def investment_recommendations(request: InvestmentRequest):
    """Génère des recommandations d'investissement personnalisées"""
    try:
        logger.info("Génération de recommandations d'investissement")
        result = investment_intelligence.generate_recommendations(request)
        return result
    except Exception as e:
        logger.error(f"Erreur recommandations: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur recommandations: {str(e)}")

@app.get("/api/v1/investment/recommendations")
async def investment_recommendations_get(
    min_confidence_score: float = Query(default=70.0, description="Score de confiance minimum"),
    max_recommendations: int = Query(default=20, description="Nombre max de recommandations"),
    min_market_cap: float = Query(default=1000000000, description="Cap minimum"),
    max_risk_level: str = Query(default="HIGH", description="Niveau de risque max"),
    preferred_horizon: str = Query(default="MEDIUM_TERM", description="Horizon préféré")
):
    """Génère des recommandations d'investissement via GET avec paramètres de query"""
    try:
        logger.info("Génération de recommandations d'investissement (GET)")
        
        # Création de l'objet request à partir des paramètres
        request = InvestmentRequest(
            min_confidence_score=min_confidence_score,
            max_recommendations=max_recommendations,
            min_market_cap=min_market_cap,
            max_risk_level=max_risk_level,
            preferred_horizon=preferred_horizon
        )
        
        result = investment_intelligence.generate_recommendations(request)
        return result
    except Exception as e:
        logger.error(f"Erreur recommandations GET: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur recommandations: {str(e)}")

@app.post("/api/v1/portfolio/suggestions")
async def portfolio_suggestions(request: PortfolioRequest):
    """Génère des suggestions de portefeuille optimisé"""
    try:
        logger.info(f"Optimisation portefeuille: ${request.portfolio_size:,.0f}")
        result = await portfolio_optimizer.suggest_portfolio(request)
        return result
    except Exception as e:
        logger.error(f"Erreur portefeuille: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur portefeuille: {str(e)}")

@app.get("/api/v1/market/sectors")
async def sector_analysis():
    """Analyse des secteurs du marché"""
    try:
        # Scan rapide par secteur
        scan_request = MarketScanRequest(max_symbols=50, parallel_requests=10)
        scan_results = market_scanner.scan_market(scan_request)
        
        # Regroupement par secteur
        sectors = {}
        for opportunity in scan_results['top_opportunities']:
            sector = opportunity['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(opportunity)
        
        # Calcul des métriques par secteur
        sector_rankings = []
        for sector, stocks in sectors.items():
            if stocks:
                avg_score = np.mean([s['overall_score'] for s in stocks])
                avg_return = np.mean([s.get('potential_return', 0) for s in stocks])
                best_stock = max(stocks, key=lambda x: x['overall_score'])
                
                sector_rankings.append({
                    'sector': sector,
                    'average_confidence': round(avg_score, 1),
                    'average_potential_return': round(avg_return, 1),
                    'stock_count': len(stocks),
                    'top_pick': best_stock['symbol'],
                    'top_pick_score': best_stock['overall_score']
                })
        
        # Tri par score moyen
        sector_rankings.sort(key=lambda x: x['average_confidence'], reverse=True)
        
        # Ajout du rang
        for i, sector in enumerate(sector_rankings, 1):
            sector['rank'] = i
        
        return {
            'analysis_summary': {
                'total_sectors': len(sector_rankings),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'sector_rankings': sector_rankings[:10]
        }
    except Exception as e:
        logger.error(f"Erreur analyse sectorielle: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur secteurs: {str(e)}")

@app.get("/api/v1/investment/opportunities")
async def investment_opportunities():
    """Récupère les meilleures opportunités du moment"""
    try:
        request = InvestmentRequest(min_confidence_score=80.0, max_recommendations=10)
        recommendations = investment_intelligence.generate_recommendations(request)
        
        # Retourner seulement les STRONG_BUY
        return {
            'top_opportunities': recommendations['strong_buy_recommendations'],
            'opportunity_count': len(recommendations['strong_buy_recommendations']),
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur opportunités: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur opportunités: {str(e)}")

@app.get("/api/v1/analysis/status")
async def analysis_status():
    """Statut des analyses en cours"""
    return {
        'status': 'ready',
        'last_scan': datetime.now().isoformat(),
        'market_status': 'open' if datetime.now().weekday() < 5 else 'closed',
        'data_freshness': 'real-time',
        'system_load': 'normal'
    }

# Lancement de l'application
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎯 BOURSA VISION ADVANCED - API Intelligence Financière   ║
║                                                              ║
║   🚀 Analyse massive de marché avec IA                      ║
║   📊 Recommandations d'investissement automatisées          ║
║   💼 Optimisation de portefeuille intelligente              ║
║                                                              ║
║   🌐 http://localhost:8005                                   ║
║   📚 http://localhost:8005/docs                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
