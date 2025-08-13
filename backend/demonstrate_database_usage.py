#!/usr/bin/env python3
"""
Script de démonstration des possibilités d'utilisation de la base de données
pour BoursaVision Enhanced API
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8006"

def demo_header():
    print("═" * 80)
    print("🎯 DÉMONSTRATION: Utilisation enrichie de la base de données BoursaVision")
    print("═" * 80)
    print(f"⏰ Démarré à: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def test_endpoint(name: str, endpoint: str, method: str = "GET", data: dict = None):
    """Test un endpoint et affiche le résultat"""
    print(f"🔍 Test: {name}")
    print(f"   Endpoint: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Succès (Code: {response.status_code})")
            return result
        else:
            print(f"   ❌ Erreur (Code: {response.status_code})")
            print(f"   Message: {response.text}")
            return None
    except Exception as e:
        print(f"   💥 Exception: {e}")
        return None

def demonstrate_database_features():
    """Démontre les nouvelles fonctionnalités de base de données"""
    
    demo_header()
    
    # 1. Vérifier l'état de la base de données
    print("1️⃣  VÉRIFICATION DE L'ÉTAT DE LA BASE DE DONNÉES")
    print("-" * 50)
    
    # API Home avec stats BDD
    result = test_endpoint("Statistiques de la base de données", "/")
    if result and "database_stats" in result:
        stats = result["database_stats"]
        print(f"   📊 Données de marché en cache: {stats['market_data_entries']}")
        print(f"   📊 Signaux d'investissement actifs: {stats['active_signals']}")
        print(f"   📊 Portefeuilles utilisateur: {stats['user_portfolios']}")
        print(f"   📊 Positions en portefeuille: {stats['portfolio_positions']}")
    print()
    
    # Admin database
    result = test_endpoint("Interface d'administration BDD", "/api/v1/admin/database")
    if result:
        print(f"   🏥 Santé de la BDD: {result['database_health']}")
        if "tables_statistics" in result:
            tables = result["tables_statistics"]
            print(f"   📋 Tables créées: {len(tables)} tables")
            for table_name, info in tables.items():
                if isinstance(info, dict) and "count" in info:
                    print(f"      - {table_name}: {info['count']} enregistrements")
    print()
    
    # 2. Test du cache intelligent des données de marché
    print("2️⃣  CACHE INTELLIGENT DES DONNÉES DE MARCHÉ")
    print("-" * 50)
    
    # Premier appel (création du cache)
    symbols_to_test = ["AAPL", "MSFT", "GOOGL"]
    for symbol in symbols_to_test:
        print(f"   🔄 Test cache pour {symbol}...")
        result = test_endpoint(
            f"Données de marché avec cache - {symbol}", 
            f"/api/v1/market/cached/{symbol}?use_cache=true"
        )
        if result and "current_data" in result:
            data = result["current_data"]
            cache_info = result.get("cache_performance", {})
            print(f"      💰 Prix actuel: ${data.get('current_price', 0):.2f}")
            print(f"      📊 Volume: {data.get('volume', 0):,}")
            print(f"      🗄️ Cache hit: {cache_info.get('cache_hit', False)}")
            print(f"      📈 Points de données: {data.get('data_points_cached', 0)}")
        time.sleep(1)  # Éviter de surcharger l'API
    print()
    
    # 3. Test du système de signaux d'investissement
    print("3️⃣  SYSTÈME DE SIGNAUX D'INVESTISSEMENT")
    print("-" * 50)
    
    # Récupérer les signaux existants
    result = test_endpoint("Récupération des signaux", "/api/v1/signals")
    if result and "signals" in result:
        signals = result["signals"]
        print(f"   📊 Signaux trouvés: {len(signals)}")
        for signal in signals[:3]:  # Afficher les 3 premiers
            print(f"      📈 {signal['symbol']}: {signal['signal_type']} "
                  f"(Confiance: {signal['confidence']}%)")
            print(f"         Rationale: {signal['rationale']}")
    
    # Créer un nouveau signal
    new_signal = {
        "symbol": "NVDA",
        "signal_type": "BUY",
        "confidence": 88.5,
        "rationale": "Strong AI growth prospects and technological leadership"
    }
    result = test_endpoint(
        "Création d'un nouveau signal", 
        "/api/v1/signals",
        method="POST",
        data=new_signal
    )
    if result:
        print(f"   ✨ Nouveau signal créé avec ID: {result.get('signal_id')}")
    print()
    
    # 4. Test du système de portfolios persistants
    print("4️⃣  PORTFOLIOS UTILISATEUR PERSISTANTS")
    print("-" * 50)
    
    # Récupérer les portfolios existants
    result = test_endpoint("Liste des portefeuilles", "/api/v1/portfolios")
    if result and "portfolios" in result:
        portfolios = result["portfolios"]
        print(f"   💼 Portefeuilles trouvés: {len(portfolios)}")
        for portfolio in portfolios:
            print(f"      📁 {portfolio['name']} (ID: {portfolio['id']})")
            print(f"         💰 Valeur totale: ${portfolio['total_value']:,.2f}")
            print(f"         📊 Positions: {portfolio['positions_count']}")
            
            # Afficher les positions
            for position in portfolio.get('positions', []):
                pnl = position.get('unrealized_pnl', 0)
                pnl_sign = "📈" if pnl >= 0 else "📉"
                print(f"         {pnl_sign} {position['symbol']}: "
                      f"{position['quantity']} @ ${position['average_price']} "
                      f"(P&L: ${pnl:.2f})")
    print()
    
    # 5. Test de l'audit trail
    print("5️⃣  AUDIT TRAIL ET TRAÇABILITÉ")
    print("-" * 50)
    
    result = test_endpoint("Administration avancée", "/api/v1/admin/database")
    if result and "recent_activity" in result:
        activities = result["recent_activity"]
        print(f"   📝 Activités récentes: {len(activities)}")
        for activity in activities:
            print(f"      🔍 {activity['entity_type']}: {activity['action']} "
                  f"({activity['count']} fois)")
    print()
    
    # 6. Recommandations pour l'expansion
    print("6️⃣  RECOMMANDATIONS POUR L'EXPANSION")
    print("-" * 50)
    
    recommendations = [
        "🚀 Implémenter des alertes en temps réel basées sur les signaux",
        "📊 Ajouter des tableaux de bord utilisateur avec données persistantes",
        "🔄 Créer des tâches de fond pour la mise à jour automatique des données",
        "📈 Développer un système de backtesting avec données historiques",
        "👥 Implémenter la gestion multi-utilisateur avec authentification",
        "📧 Ajouter un système de notifications par email/SMS",
        "🧮 Créer des rapports PDF automatisés des performances",
        "🔐 Implémenter un système de permissions granulaires",
        "📱 Développer une API mobile avec synchronisation offline",
        "🤖 Ajouter l'intelligence artificielle pour l'analyse prédictive"
    ]
    
    for rec in recommendations:
        print(f"   {rec}")
    print()
    
    # Conclusion
    print("✨ CONCLUSION")
    print("-" * 50)
    print("🎯 Démonstration complète des possibilités d'utilisation de la base de données")
    print("📈 La base de données est maintenant utilisée pour:")
    print("   • Cache intelligent des données de marché")
    print("   • Stockage persistant des portfolios utilisateur")
    print("   • Système de signaux d'investissement")
    print("   • Audit trail complet des actions")
    print("   • Interface d'administration avancée")
    print()
    print("🚀 Prêt pour l'expansion vers une plateforme de trading complète!")
    print("═" * 80)

if __name__ == "__main__":
    demonstrate_database_features()