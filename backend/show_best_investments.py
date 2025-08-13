#!/usr/bin/env python3
"""
Boursa Vision Advanced - Affichage des Meilleurs Placements
Script pour identifier et afficher les meilleures opportunités d'investissement
"""

import json
import time
from datetime import datetime
from typing import Dict, List

import requests


class BestInvestmentsFinder:
    """Classe pour identifier les meilleures opportunités d'investissement"""

    def __init__(self, api_url: str = "http://localhost:8005"):
        self.api_url = api_url
        self.session = requests.Session()

    def check_api_status(self) -> bool:
        """Vérifie que l'API est accessible"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_market_scan(self, max_symbols: int = 50) -> Dict:
        """Lance un scan massif du marché"""
        print(f"🔍 Lancement du scan de marché sur {max_symbols} symboles...")

        scan_request = {
            "strategy": "FULL_MARKET",
            "max_symbols": max_symbols,
            "min_market_cap": 1000000000,  # 1 milliard minimum
            "min_volume": 100000,
            "parallel_requests": 20,
        }

        response = self.session.post(
            f"{self.api_url}/api/v1/market/scan", json=scan_request, timeout=120
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erreur scan: {response.status_code}")

    def get_investment_recommendations(self, min_confidence: float = 75.0) -> Dict:
        """Obtient les recommandations d'investissement IA"""
        print(
            f"🤖 Génération des recommandations IA (confiance min: {min_confidence}%)..."
        )

        analysis_request = {
            "min_confidence_score": min_confidence,
            "max_recommendations": 30,
            "min_market_cap": 5000000000,  # 5 milliards pour plus de stabilité
            "max_risk_level": "HIGH",
            "preferred_horizon": "MEDIUM_TERM",
        }

        response = self.session.post(
            f"{self.api_url}/api/v1/investment/recommendations",
            json=analysis_request,
            timeout=120,
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erreur recommandations: {response.status_code}")

    def get_portfolio_suggestions(self, portfolio_size: float = 100000.0) -> Dict:
        """Obtient des suggestions de portefeuille optimisé"""
        print(f"💼 Optimisation de portefeuille pour ${portfolio_size:,.0f}...")

        portfolio_request = {
            "portfolio_size": portfolio_size,
            "max_positions": 8,
            "risk_tolerance": "MODERATE",
        }

        response = self.session.post(
            f"{self.api_url}/api/v1/portfolio/suggestions",
            json=portfolio_request,
            timeout=60,
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erreur portefeuille: {response.status_code}")

    def get_sector_analysis(self) -> Dict:
        """Obtient l'analyse sectorielle"""
        print("🏭 Analyse des secteurs du marché...")

        response = self.session.get(f"{self.api_url}/api/v1/market/sectors", timeout=60)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Erreur secteurs: {response.status_code}")

    def display_banner(self):
        """Affiche la bannière de démarrage"""
        banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║         🎯 BOURSA VISION ADVANCED - MEILLEURS PLACEMENTS                    ║
║                                                                              ║
║    📊 Analyse Massive du Marché • 🤖 IA de Recommandations                 ║
║    💰 Identification des Meilleures Opportunités d'Investissement           ║
║                                                                              ║
║    📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}                                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def display_top_opportunities(self, scan_results: Dict, limit: int = 10):
        """Affiche les meilleures opportunités du scan"""
        print("\n" + "=" * 80)
        print("🔥 TOP OPPORTUNITÉS IDENTIFIÉES PAR LE SCAN MASSIF")
        print("=" * 80)

        opportunities = scan_results.get("top_opportunities", [])[:limit]

        if not opportunities:
            print("❌ Aucune opportunité trouvée dans le scan")
            return

        print(
            f"📈 {len(opportunities)} meilleures opportunités sur {scan_results['scan_summary']['total_analyzed']} actions analysées\n"
        )

        # En-tête du tableau
        print(
            f"{'Rang':<4} {'Symbole':<8} {'Nom':<25} {'Prix':<10} {'Score':<8} {'P/E':<8} {'RSI':<8} {'Secteur':<15}"
        )
        print("-" * 95)

        for i, opp in enumerate(opportunities, 1):
            prix = f"${opp['current_price']:.2f}"
            score = f"{opp['overall_score']:.1f}/100"
            pe = f"{opp['pe_ratio']:.1f}" if opp["pe_ratio"] > 0 else "N/A"
            rsi = f"{opp['rsi']:.1f}"

            # Couleur selon le score
            if opp["overall_score"] >= 85:
                indicator = "🟢"
            elif opp["overall_score"] >= 75:
                indicator = "🟡"
            else:
                indicator = "🔵"

            print(
                f"{indicator}{i:<3} {opp['symbol']:<8} {opp['name'][:24]:<25} {prix:<10} {score:<8} {pe:<8} {rsi:<8} {opp['sector'][:14]:<15}"
            )

    def display_strong_buy_recommendations(self, recommendations: Dict):
        """Affiche les recommandations STRONG_BUY"""
        print("\n" + "=" * 80)
        print("⭐ RECOMMANDATIONS STRONG_BUY - ACHATS PRIORITAIRES")
        print("=" * 80)

        strong_buys = recommendations.get("strong_buy_recommendations", [])

        if not strong_buys:
            print("❌ Aucune recommandation STRONG_BUY trouvée")
            return

        print(f"💎 {len(strong_buys)} actions recommandées en STRONG_BUY\n")

        for i, rec in enumerate(strong_buys, 1):
            print(f"{i}. 🎯 {rec['symbol']} - {rec['name']}")
            print(f"   💰 Prix actuel: ${rec['current_price']:.2f}")
            print(f"   🎯 Prix cible: ${rec['target_price']:.2f}")
            print(f"   📈 Potentiel: +{rec['potential_return']:.1f}%")
            print(f"   🎲 Confiance: {rec['confidence_score']:.1f}%")
            print(f"   ⚠️  Risque: {rec['risk_level']}")
            print(f"   🏭 Secteur: {rec['sector']}")
            print(f"   💡 Raisons: {', '.join(rec['reasons'][:2])}")
            print()

    def display_buy_recommendations(self, recommendations: Dict, limit: int = 5):
        """Affiche les recommandations BUY"""
        print("\n" + "=" * 80)
        print("✅ RECOMMANDATIONS BUY - BONNES OPPORTUNITÉS")
        print("=" * 80)

        buys = recommendations.get("buy_recommendations", [])[:limit]

        if not buys:
            print("❌ Aucune recommandation BUY trouvée")
            return

        print(f"✨ Top {len(buys)} recommandations BUY\n")

        for i, rec in enumerate(buys, 1):
            print(f"{i}. ✅ {rec['symbol']} - {rec['name']}")
            print(
                f"   💰 ${rec['current_price']:.2f} → ${rec['target_price']:.2f} (+{rec['potential_return']:.1f}%)"
            )
            print(
                f"   📊 Confiance: {rec['confidence_score']:.1f}% | Risque: {rec['risk_level']}"
            )
            print()

    def display_portfolio_suggestion(self, portfolio: Dict):
        """Affiche la suggestion de portefeuille optimisé"""
        print("\n" + "=" * 80)
        print("💼 PORTEFEUILLE OPTIMISÉ SUGGÉRÉ")
        print("=" * 80)

        summary = portfolio.get("portfolio_summary", {})
        allocations = portfolio.get("portfolio_allocations", [])

        print(f"💰 Valeur totale: ${summary.get('total_portfolio_value', 0):,.0f}")
        print(f"📊 Positions: {summary.get('number_of_positions', 0)}")
        print(
            f"📈 Rendement attendu: {summary.get('expected_annual_return', 0):.1f}% par an"
        )
        print(
            f"🎯 Score diversification: {summary.get('diversification_score', 0):.0f}/100"
        )
        print(f"⚠️  Tolérance risque: {summary.get('risk_level', 'N/A')}")
        print()

        if allocations:
            print("📋 Allocation suggérée:")
            print(
                f"{'Symbole':<8} {'Nom':<20} {'Poids':<8} {'Montant':<12} {'Actions':<8} {'Secteur':<15}"
            )
            print("-" * 75)

            for alloc in allocations:
                poids = f"{alloc['weight']*100:.1f}%"
                montant = f"${alloc['suggested_amount']:,.0f}"
                actions = f"{alloc['shares']}"

                print(
                    f"{alloc['symbol']:<8} {alloc['name'][:19]:<20} {poids:<8} {montant:<12} {actions:<8} {alloc['sector'][:14]:<15}"
                )

    def display_sector_analysis(self, sectors: Dict, limit: int = 5):
        """Affiche l'analyse sectorielle"""
        print("\n" + "=" * 80)
        print("🏭 ANALYSE SECTORIELLE - MEILLEURS SECTEURS")
        print("=" * 80)

        rankings = sectors.get("sector_rankings", [])[:limit]

        if not rankings:
            print("❌ Aucune donnée sectorielle trouvée")
            return

        print(f"🎯 Top {len(rankings)} secteurs les plus prometteurs\n")

        for ranking in rankings:
            print(f"{ranking['rank']}. 🏭 {ranking['sector']}")
            print(f"   📊 Confiance moyenne: {ranking['average_confidence']:.1f}%")
            print(f"   📈 Potentiel moyen: {ranking['average_potential_return']:.1f}%")
            print(
                f"   🎯 Meilleur choix: {ranking['top_pick']} (Score: {ranking['top_pick_score']:.1f})"
            )
            print(f"   📊 Actions analysées: {ranking['stock_count']}")
            print()

    def display_summary_and_advice(self, scan_results: Dict, recommendations: Dict):
        """Affiche un résumé et des conseils d'investissement"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ EXÉCUTIF ET CONSEILS D'INVESTISSEMENT")
        print("=" * 80)

        # Statistiques du scan
        scan_summary = scan_results.get("scan_summary", {})
        analysis_summary = recommendations.get("analysis_summary", {})

        print("📈 STATISTIQUES DE L'ANALYSE:")
        print(f"   • Actions analysées: {scan_summary.get('total_analyzed', 0)}")
        print(
            f"   • Opportunités trouvées: {scan_summary.get('top_opportunities_found', 0)}"
        )
        print(
            f"   • Score moyen du marché: {scan_summary.get('average_score', 0):.1f}/100"
        )
        print(
            f"   • Recommandations STRONG_BUY: {analysis_summary.get('strong_buy_count', 0)}"
        )
        print(f"   • Recommandations BUY: {analysis_summary.get('buy_count', 0)}")
        print()

        print("💡 CONSEILS D'INVESTISSEMENT:")

        strong_buy_count = analysis_summary.get("strong_buy_count", 0)
        avg_confidence = analysis_summary.get("average_confidence", 0)

        if strong_buy_count >= 5:
            print("   🟢 MARCHÉ FAVORABLE: Nombreuses opportunités STRONG_BUY détectées")
            print("   💰 Action recommandée: Investir dans les top recommandations")
        elif strong_buy_count >= 2:
            print("   🟡 MARCHÉ MODÉRÉ: Quelques bonnes opportunités disponibles")
            print("   💰 Action recommandée: Sélectionner les meilleures opportunités")
        else:
            print("   🔴 MARCHÉ DIFFICILE: Peu d'opportunités STRONG_BUY")
            print("   💰 Action recommandée: Attendre ou diversifier davantage")

        if avg_confidence >= 80:
            print("   📊 Confiance élevée dans les analyses")
        elif avg_confidence >= 70:
            print("   📊 Confiance modérée dans les analyses")
        else:
            print("   📊 Confiance faible - Prudence recommandée")

        print()
        print(
            "⚠️  AVERTISSEMENT: Ces analyses sont automatisées et à des fins éducatives."
        )
        print("   Consultez un conseiller financier professionnel avant d'investir.")

    def run_complete_analysis(self, portfolio_size: float = 100000.0):
        """Lance une analyse complète pour identifier les meilleurs placements"""

        self.display_banner()

        # Vérification de l'API
        print("🔍 Vérification de l'accès à l'API...")
        if not self.check_api_status():
            print(
                "❌ ERREUR: L'API n'est pas accessible. Assurez-vous qu'elle est lancée."
            )
            print("   Commande: cd backend && ./launch_api.sh")
            return

        print("✅ API accessible - Démarrage de l'analyse\n")

        try:
            # 1. Scan massif du marché
            scan_results = self.get_market_scan(max_symbols=50)
            time.sleep(1)

            # 2. Recommandations IA
            recommendations = self.get_investment_recommendations(min_confidence=70.0)
            time.sleep(1)

            # 3. Analyse sectorielle
            sectors = self.get_sector_analysis()
            time.sleep(1)

            # 4. Portefeuille optimisé
            portfolio = self.get_portfolio_suggestions(portfolio_size)

            # Affichage des résultats
            self.display_top_opportunities(scan_results)
            self.display_strong_buy_recommendations(recommendations)
            self.display_buy_recommendations(recommendations)
            self.display_sector_analysis(sectors)
            self.display_portfolio_suggestion(portfolio)
            self.display_summary_and_advice(scan_results, recommendations)

            print("\n" + "=" * 80)
            print("✨ ANALYSE TERMINÉE - MEILLEURS PLACEMENTS IDENTIFIÉS")
            print("=" * 80)
            print("🌐 Documentation complète: http://localhost:8005/docs")
            print("📊 API Status: http://localhost:8005/health")

        except Exception as e:
            print(f"\n❌ ERREUR lors de l'analyse: {e}")
            print(
                "🔧 Vérifiez que l'API est bien lancée avec: cd backend && ./launch_api.sh"
            )


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Identifier les meilleurs placements avec Boursa Vision"
    )
    parser.add_argument(
        "--portfolio",
        type=float,
        default=100000.0,
        help="Taille du portefeuille en USD (défaut: 100000)",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8005",
        help="URL de l'API (défaut: http://localhost:8005)",
    )

    args = parser.parse_args()

    finder = BestInvestmentsFinder(api_url=args.api_url)
    finder.run_complete_analysis(portfolio_size=args.portfolio)


if __name__ == "__main__":
    main()
