#!/usr/bin/env python3
"""
Boursa Vision Enhanced API - Avec utilisation complète de la base de données
Démontre les possibilités d'utilisation de la BDD pour stocker et enrichir les données
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import uvicorn
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MODÈLES PYDANTIC
# ============================================================================

class MarketDataEntry(BaseModel):
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    source: str = "yfinance"

class EnhancedMarketScanRequest(BaseModel):
    strategy: str = Field(default="FULL_MARKET", description="Stratégie de scan")
    max_symbols: int = Field(default=50, description="Nombre maximum de symboles")
    cache_duration: int = Field(default=300, description="Durée de cache en secondes")
    store_in_db: bool = Field(default=True, description="Stocker les données en BDD")

class UserPortfolioRequest(BaseModel):
    user_id: str = Field(description="ID de l'utilisateur")
    portfolio_name: str = Field(description="Nom du portefeuille")
    base_currency: str = Field(default="USD", description="Devise de base")
    initial_cash: float = Field(default=100000.0, description="Capital initial")

class PositionRequest(BaseModel):
    portfolio_id: int = Field(description="ID du portefeuille")
    symbol: str = Field(description="Symbole de l'action")
    quantity: float = Field(description="Quantité")
    purchase_price: float = Field(description="Prix d'achat")

class SignalRequest(BaseModel):
    symbol: str = Field(description="Symbole")
    signal_type: str = Field(description="Type de signal: BUY, SELL, HOLD")
    confidence: float = Field(description="Score de confiance 0-100")
    rationale: str = Field(description="Justification du signal")

# ============================================================================
# SERVICES BASE DE DONNÉES
# ============================================================================

class DatabaseService:
    """Service pour les opérations de base de données"""
    
    @staticmethod
    def init_database():
        """Initialise les tables de la base de données"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                # Table pour les données de marché avec cache
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        volume INTEGER,
                        source TEXT DEFAULT 'yfinance',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timestamp)
                    )
                ''')
                
                # Table pour les signaux d'investissement
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        target_price REAL,
                        stop_loss REAL,
                        rationale TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Table pour les portfolios utilisateur
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_portfolios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        base_currency TEXT DEFAULT 'USD',
                        initial_cash REAL DEFAULT 0,
                        current_cash REAL DEFAULT 0,
                        total_value REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Table pour les positions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER NOT NULL,
                        symbol TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        average_price REAL NOT NULL,
                        current_price REAL,
                        market_value REAL,
                        unrealized_pnl REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (portfolio_id) REFERENCES user_portfolios (id),
                        UNIQUE(portfolio_id, symbol)
                    )
                ''')
                
                # Table pour l'audit/historique
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT,
                        action TEXT NOT NULL,
                        old_values TEXT,
                        new_values TEXT,
                        user_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Index pour les performances
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data_cache(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data_cache(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol ON investment_signals(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_active ON investment_signals(is_active)')
                
                conn.commit()
                logger.info("Base de données initialisée avec succès")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la BDD: {e}")
            raise

    @staticmethod
    def cache_market_data(market_data_list: List[MarketDataEntry]) -> int:
        """Cache les données de marché en base"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                inserted = 0
                for data in market_data_list:
                    try:
                        cursor.execute('''
                            INSERT OR REPLACE INTO market_data_cache 
                            (symbol, timestamp, open_price, high_price, low_price, 
                             close_price, volume, source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            data.symbol, data.timestamp, data.open_price,
                            data.high_price, data.low_price, data.close_price,
                            data.volume, data.source
                        ))
                        inserted += 1
                    except Exception as e:
                        logger.warning(f"Erreur insertion {data.symbol}: {e}")
                
                conn.commit()
                logger.info(f"Cached {inserted} market data entries")
                return inserted
                
        except Exception as e:
            logger.error(f"Erreur cache market data: {e}")
            return 0

    @staticmethod
    def get_cached_market_data(symbol: str, hours_back: int = 24) -> List[Dict]:
        """Récupère les données de marché en cache"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                cursor.execute('''
                    SELECT symbol, timestamp, close_price, volume, created_at
                    FROM market_data_cache 
                    WHERE symbol = ? AND created_at >= ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                ''', (symbol, cutoff_time))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'symbol': row[0],
                        'timestamp': row[1],
                        'close_price': row[2],
                        'volume': row[3],
                        'cached_at': row[4]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Erreur récupération cache: {e}")
            return []

    @staticmethod
    def save_investment_signal(signal: SignalRequest) -> int:
        """Sauvegarde un signal d'investissement"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                # Calculer prix cible basique
                latest_price = DatabaseService.get_latest_price(signal.symbol)
                target_price = latest_price * (1 + signal.confidence / 200) if latest_price else None
                stop_loss = latest_price * 0.95 if latest_price else None
                
                cursor.execute('''
                    INSERT INTO investment_signals 
                    (symbol, signal_type, confidence, target_price, stop_loss, rationale, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.symbol,
                    signal.signal_type,
                    signal.confidence,
                    target_price,
                    stop_loss,
                    signal.rationale,
                    datetime.now() + timedelta(days=30)  # Expire dans 30 jours
                ))
                
                signal_id = cursor.lastrowid
                conn.commit()
                
                # Log d'audit
                DatabaseService.log_audit("investment_signal", str(signal_id), "CREATE", None, signal.dict())
                
                return signal_id
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde signal: {e}")
            return 0

    @staticmethod
    def get_latest_price(symbol: str) -> Optional[float]:
        """Récupère le dernier prix en cache"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT close_price FROM market_data_cache 
                    WHERE symbol = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (symbol,))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Erreur récupération prix: {e}")
            return None

    @staticmethod
    def create_user_portfolio(portfolio: UserPortfolioRequest) -> int:
        """Crée un nouveau portefeuille utilisateur"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_portfolios 
                    (user_id, name, base_currency, initial_cash, current_cash, total_value)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    portfolio.user_id,
                    portfolio.portfolio_name,
                    portfolio.base_currency,
                    portfolio.initial_cash,
                    portfolio.initial_cash,  # current_cash = initial_cash
                    portfolio.initial_cash   # total_value = initial_cash initialement
                ))
                
                portfolio_id = cursor.lastrowid
                conn.commit()
                
                # Log d'audit
                DatabaseService.log_audit("user_portfolio", str(portfolio_id), "CREATE", None, portfolio.dict())
                
                return portfolio_id
                
        except Exception as e:
            logger.error(f"Erreur création portefeuille: {e}")
            return 0

    @staticmethod
    def add_position_to_portfolio(position: PositionRequest) -> int:
        """Ajoute une position à un portefeuille"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                # Vérifier que le portefeuille existe
                cursor.execute('SELECT id FROM user_portfolios WHERE id = ?', (position.portfolio_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Portfolio {position.portfolio_id} non trouvé")
                
                # Calculer la valeur de marché
                current_price = DatabaseService.get_latest_price(position.symbol) or position.purchase_price
                market_value = position.quantity * current_price
                unrealized_pnl = position.quantity * (current_price - position.purchase_price)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolio_positions 
                    (portfolio_id, symbol, quantity, average_price, current_price, 
                     market_value, unrealized_pnl, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    position.portfolio_id,
                    position.symbol,
                    position.quantity,
                    position.purchase_price,
                    current_price,
                    market_value,
                    unrealized_pnl
                ))
                
                position_id = cursor.lastrowid
                
                # Mettre à jour la valeur totale du portefeuille
                DatabaseService.update_portfolio_value(position.portfolio_id)
                
                conn.commit()
                
                # Log d'audit
                DatabaseService.log_audit("portfolio_position", str(position_id), "CREATE", None, position.dict())
                
                return position_id
                
        except Exception as e:
            logger.error(f"Erreur ajout position: {e}")
            return 0

    @staticmethod
    def update_portfolio_value(portfolio_id: int):
        """Met à jour la valeur totale d'un portefeuille"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                # Calculer la valeur totale des positions
                cursor.execute('''
                    SELECT SUM(market_value) as total_positions_value
                    FROM portfolio_positions 
                    WHERE portfolio_id = ?
                ''', (portfolio_id,))
                
                result = cursor.fetchone()
                total_positions_value = result[0] if result and result[0] else 0
                
                # Récupérer le cash actuel
                cursor.execute('SELECT current_cash FROM user_portfolios WHERE id = ?', (portfolio_id,))
                result = cursor.fetchone()
                current_cash = result[0] if result else 0
                
                # Mettre à jour la valeur totale
                total_value = current_cash + total_positions_value
                
                cursor.execute('''
                    UPDATE user_portfolios 
                    SET total_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (total_value, portfolio_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erreur mise à jour valeur portefeuille: {e}")

    @staticmethod
    def log_audit(entity_type: str, entity_id: str, action: str, old_values: Dict = None, new_values: Dict = None, user_id: str = None):
        """Log une action dans l'audit trail"""
        try:
            with sqlite3.connect('boursa_vision.db') as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_log 
                    (entity_type, entity_id, action, old_values, new_values, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entity_type,
                    entity_id,
                    action,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    user_id
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erreur log audit: {e}")

class EnhancedMarketDataService:
    """Service enrichi pour les données de marché avec cache"""
    
    @staticmethod
    def get_stock_data_with_cache(symbol: str, use_cache: bool = True) -> Optional[Dict]:
        """Récupère les données d'une action avec cache intelligent"""
        try:
            # Vérifier le cache en premier
            if use_cache:
                cached_data = DatabaseService.get_cached_market_data(symbol, hours_back=1)
                if cached_data:
                    latest = cached_data[0]
                    cache_age = datetime.now() - datetime.fromisoformat(latest['cached_at'])
                    
                    # Si les données ont moins de 5 minutes, utiliser le cache
                    if cache_age.total_seconds() < 300:
                        logger.info(f"Utilisation cache pour {symbol} (âge: {cache_age.total_seconds()}s)")
                        return {
                            "symbol": symbol,
                            "current_price": latest['close_price'],
                            "volume": latest['volume'],
                            "cached": True,
                            "cache_age_seconds": cache_age.total_seconds()
                        }
            
            # Sinon, récupérer depuis yfinance
            logger.info(f"Récupération données fraîches pour {symbol}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            info = ticker.info
            
            if hist.empty:
                return None
            
            current_price = hist["Close"].iloc[-1]
            volume = hist["Volume"].iloc[-1]
            
            # Stocker en cache
            market_data_entries = []
            for i, (date, row) in enumerate(hist.iterrows()):
                if pd.notna(row['Close']):
                    entry = MarketDataEntry(
                        symbol=symbol,
                        timestamp=date.to_pydatetime(),
                        open_price=float(row['Open']),
                        high_price=float(row['High']),
                        low_price=float(row['Low']),
                        close_price=float(row['Close']),
                        volume=int(row['Volume'])
                    )
                    market_data_entries.append(entry)
            
            if market_data_entries:
                DatabaseService.cache_market_data(market_data_entries)
            
            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "volume": int(volume),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "sector": info.get("sector", "Unknown"),
                "name": info.get("longName", symbol),
                "cached": False,
                "data_points_cached": len(market_data_entries)
            }
            
        except Exception as e:
            logger.warning(f"Erreur pour {symbol}: {e}")
            return None

# ============================================================================
# APPLICATION FASTAPI
# ============================================================================

app = FastAPI(
    title="🎯 Boursa Vision Enhanced API - Avec Base de Données",
    description="API enrichie démontrant l'utilisation complète de la base de données",
    version="2.1.0",
)

# Initialisation de la base de données au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialise la base de données au démarrage"""
    logger.info("Initialisation de la base de données...")
    DatabaseService.init_database()
    logger.info("✅ Base de données initialisée")

# ============================================================================
# ROUTES DE L'API
# ============================================================================

@app.get("/")
async def root():
    """Page d'accueil de l'API enrichie"""
    # Statistiques de la base de données
    try:
        with sqlite3.connect('boursa_vision.db') as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM market_data_cache")
            market_data_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM investment_signals WHERE is_active = 1")
            active_signals_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_portfolios")
            portfolios_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM portfolio_positions")
            positions_count = cursor.fetchone()[0]
            
    except Exception as e:
        logger.error(f"Erreur stats BDD: {e}")
        market_data_count = active_signals_count = portfolios_count = positions_count = 0
    
    return {
        "service": "Boursa Vision Enhanced API",
        "version": "2.1.0",
        "description": "API enrichie avec utilisation complète de la base de données",
        "database_stats": {
            "market_data_entries": market_data_count,
            "active_signals": active_signals_count,
            "user_portfolios": portfolios_count,
            "portfolio_positions": positions_count
        },
        "features": [
            "🗄️ Cache intelligent des données de marché",
            "💾 Portfolios utilisateur persistants",
            "📊 Signaux d'investissement stockés",
            "🔍 Audit trail complet",
            "⚡ Optimisations de performance"
        ],
        "new_endpoints": {
            "cached_market_data": "/api/v1/market/cached/{symbol}",
            "investment_signals": "/api/v1/signals",
            "user_portfolios": "/api/v1/portfolios",
            "database_admin": "/api/v1/admin/database"
        }
    }

@app.get("/api/v1/market/cached/{symbol}")
async def get_cached_market_data(symbol: str, use_cache: bool = Query(default=True, description="Utiliser le cache")):
    """Récupère les données de marché avec cache intelligent"""
    try:
        data = EnhancedMarketDataService.get_stock_data_with_cache(symbol, use_cache)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Données non trouvées pour {symbol}")
        
        # Ajouter l'historique du cache
        cached_history = DatabaseService.get_cached_market_data(symbol, hours_back=24)
        
        return {
            "current_data": data,
            "cache_history": cached_history[:10],  # Les 10 dernières entrées
            "cache_performance": {
                "cache_hit": data.get("cached", False),
                "historical_entries": len(cached_history)
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur cached market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/database")
async def database_admin():
    """Interface d'administration de la base de données"""
    try:
        with sqlite3.connect('boursa_vision.db') as conn:
            cursor = conn.cursor()
            
            # Statistiques des tables
            tables_stats = {}
            
            tables = ['market_data_cache', 'investment_signals', 'user_portfolios', 'portfolio_positions', 'audit_log']
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    # Récupérer quelques exemples
                    cursor.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 3")
                    samples = cursor.fetchall()
                    
                    # Récupérer la structure de la table
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    tables_stats[table] = {
                        "count": count,
                        "columns": columns,
                        "sample_data": samples
                    }
                except Exception as table_error:
                    tables_stats[table] = {"error": str(table_error)}
            
            return {
                "database_health": "✅ Healthy",
                "tables_statistics": tables_stats,
                "recommendations": [
                    "✅ Base de données SQLite fonctionnelle",
                    "✅ Structure des tables enrichie créée", 
                    "💡 Lancer /api/v1/admin/populate-demo-data pour créer des données de test",
                    "💡 Utiliser les endpoints pour tester les fonctionnalités"
                ]
            }
            
    except Exception as e:
        logger.error(f"Erreur admin database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/populate-demo-data")
async def populate_demo_data():
    """Peuple la base avec des données de démonstration"""
    try:
        demo_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
        
        # Récupérer et cacher des données pour quelques symboles
        cached_count = 0
        for symbol in demo_symbols:
            data = EnhancedMarketDataService.get_stock_data_with_cache(symbol, use_cache=False)
            if data:
                cached_count += data.get("data_points_cached", 0)
        
        # Créer quelques signaux de démonstration
        demo_signals = [
            SignalRequest(
                symbol="AAPL",
                signal_type="BUY",
                confidence=85.0,
                rationale="Strong fundamentals and positive momentum"
            ),
            SignalRequest(
                symbol="TSLA",
                signal_type="HOLD",
                confidence=72.5,
                rationale="Waiting for earnings report clarity"
            ),
            SignalRequest(
                symbol="MSFT",
                signal_type="BUY",
                confidence=90.0,
                rationale="Cloud business growth and AI integration"
            )
        ]
        
        signal_ids = []
        for signal in demo_signals:
            signal_id = DatabaseService.save_investment_signal(signal)
            if signal_id > 0:
                signal_ids.append(signal_id)
        
        # Créer un portefeuille de démonstration
        demo_portfolio = UserPortfolioRequest(
            user_id="demo_user_1",
            portfolio_name="Demo Portfolio",
            base_currency="USD",
            initial_cash=100000.0
        )
        
        portfolio_id = DatabaseService.create_user_portfolio(demo_portfolio)
        
        # Ajouter quelques positions
        position_ids = []
        if portfolio_id > 0:
            demo_positions = [
                PositionRequest(
                    portfolio_id=portfolio_id,
                    symbol="AAPL",
                    quantity=50,
                    purchase_price=150.0
                ),
                PositionRequest(
                    portfolio_id=portfolio_id,
                    symbol="MSFT",
                    quantity=30,
                    purchase_price=300.0
                )
            ]
            
            for position in demo_positions:
                pos_id = DatabaseService.add_position_to_portfolio(position)
                if pos_id > 0:
                    position_ids.append(pos_id)
        
        return {
            "demo_data_created": "✅ Success",
            "market_data_points": cached_count,
            "signals_created": len(signal_ids),
            "portfolio_id": portfolio_id,
            "positions_created": len(position_ids),
            "summary": {
                "symbols_cached": demo_symbols,
                "signals": [s.dict() for s in demo_signals],
                "portfolio": demo_portfolio.dict()
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur populate demo data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Lancement de l'application
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎯 BOURSA VISION ENHANCED - Avec Base de Données          ║
║                                                              ║
║   🗄️ Cache intelligent des données de marché                ║
║   💾 Portfolios utilisateur persistants                     ║
║   📊 Signaux d'investissement stockés                       ║
║   🔍 Audit trail complet                                    ║
║                                                              ║
║   🌐 http://localhost:8006                                   ║
║   📚 http://localhost:8006/docs                              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run("api_with_database:app", host="0.0.0.0", port=8006, reload=True, log_level="info")

