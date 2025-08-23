"""
Tests End-to-End pour BoursaVision
=================================

Tests de scénarios complets utilisateur à travers l'API REST.
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from boursa_vision.domain.entities.investment import (
    InvestmentSector,
    InvestmentType,
    MarketCap,
)
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.mark.e2e
@pytest.mark.asyncio
class TestInvestmentManagementScenario:
    """Scénario E2E complet : Gestion des investissements."""

    async def test_complete_investment_lifecycle(
        self, test_client: AsyncClient, authenticated_user
    ):
        """
        Scénario complet : Créer, rechercher, modifier et supprimer un investissement.

        Étapes :
        1. Créer un nouvel investissement via API
        2. Rechercher l'investissement
        3. Mettre à jour le prix
        4. Supprimer l'investissement
        """
        # Arrange
        investment_data = {
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "investment_type": "STOCK",
            "sector": "TECHNOLOGY",
            "market_cap": "LARGE",
            "exchange": "NASDAQ",
            "currency": "USD",
            "current_price": {"amount": "250.75", "currency": "USD"},
            "description": "Electric vehicle and clean energy company",
        }

        # Act & Assert - Étape 1 : Créer l'investissement
        create_response = await test_client.post(
            "/api/v1/investments",
            json=investment_data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert create_response.status_code == 201
        created_investment = create_response.json()
        assert created_investment["symbol"] == "TSLA"
        assert created_investment["name"] == "Tesla Inc."

        # Act & Assert - Étape 2 : Rechercher l'investissement
        search_response = await test_client.get(
            "/api/v1/investments/TSLA",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert search_response.status_code == 200
        found_investment = search_response.json()
        assert found_investment["symbol"] == "TSLA"
        assert found_investment["current_price"]["amount"] == "250.75"

        # Act & Assert - Étape 3 : Mettre à jour le prix
        update_data = {"current_price": {"amount": "275.50", "currency": "USD"}}

        update_response = await test_client.patch(
            f"/api/v1/investments/{created_investment['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert update_response.status_code == 200
        updated_investment = update_response.json()
        assert updated_investment["current_price"]["amount"] == "275.50"

        # Act & Assert - Étape 4 : Supprimer l'investissement
        delete_response = await test_client.delete(
            f"/api/v1/investments/{created_investment['id']}",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert delete_response.status_code == 204

        # Vérifier que l'investissement n'existe plus
        not_found_response = await test_client.get(
            "/api/v1/investments/TSLA",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )
        assert not_found_response.status_code == 404


@pytest.mark.e2e
@pytest.mark.asyncio
class TestPortfolioManagementScenario:
    """Scénario E2E complet : Gestion de portefeuille."""

    async def test_complete_portfolio_scenario(
        self, test_client: AsyncClient, authenticated_user
    ):
        """
        Scénario complet : Créer un portefeuille et gérer ses investissements.

        Étapes :
        1. Créer des investissements
        2. Créer un portefeuille
        3. Ajouter des investissements au portefeuille
        4. Consulter la valeur du portefeuille
        5. Modifier les quantités
        6. Supprimer un investissement du portefeuille
        """
        # Arrange - Créer des investissements
        investments_data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "LARGE",
                "exchange": "NASDAQ",
                "currency": "USD",
                "current_price": {"amount": "150.00", "currency": "USD"},
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "LARGE",
                "exchange": "NASDAQ",
                "currency": "USD",
                "current_price": {"amount": "300.00", "currency": "USD"},
            },
        ]

        created_investments = []

        # Créer les investissements
        for inv_data in investments_data:
            response = await test_client.post(
                "/api/v1/investments",
                json=inv_data,
                headers={"Authorization": f"Bearer {authenticated_user.token}"},
            )
            assert response.status_code == 201
            created_investments.append(response.json())

        # Act & Assert - Étape 2 : Créer un portefeuille
        portfolio_data = {
            "name": "My Tech Portfolio",
            "description": "Portfolio focused on technology stocks",
            "currency": "USD",
        }

        portfolio_response = await test_client.post(
            "/api/v1/portfolios",
            json=portfolio_data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert portfolio_response.status_code == 201
        created_portfolio = portfolio_response.json()
        assert created_portfolio["name"] == "My Tech Portfolio"

        # Act & Assert - Étape 3 : Ajouter des investissements au portefeuille
        positions_data = [
            {
                "investment_id": created_investments[0]["id"],
                "quantity": 10,
                "purchase_price": {"amount": "145.00", "currency": "USD"},
            },
            {
                "investment_id": created_investments[1]["id"],
                "quantity": 5,
                "purchase_price": {"amount": "295.00", "currency": "USD"},
            },
        ]

        for position_data in positions_data:
            add_response = await test_client.post(
                f"/api/v1/portfolios/{created_portfolio['id']}/positions",
                json=position_data,
                headers={"Authorization": f"Bearer {authenticated_user.token}"},
            )
            assert add_response.status_code == 201

        # Act & Assert - Étape 4 : Consulter la valeur du portefeuille
        portfolio_value_response = await test_client.get(
            f"/api/v1/portfolios/{created_portfolio['id']}/value",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert portfolio_value_response.status_code == 200
        portfolio_value = portfolio_value_response.json()

        # Valeur attendue : (10 * 150) + (5 * 300) = 1500 + 1500 = 3000 USD
        assert float(portfolio_value["current_value"]["amount"]) == 3000.00
        assert portfolio_value["current_value"]["currency"] == "USD"

        # Vérifier la performance
        # Coût total : (10 * 145) + (5 * 295) = 1450 + 1475 = 2925 USD
        # Gain : 3000 - 2925 = 75 USD
        assert float(portfolio_value["total_gain"]["amount"]) == 75.00

        # Act & Assert - Étape 5 : Modifier une position
        position_id = portfolio_value["positions"][0]["id"]

        update_position_data = {"quantity": 15}  # Augmenter la quantité

        update_position_response = await test_client.patch(
            f"/api/v1/portfolios/{created_portfolio['id']}/positions/{position_id}",
            json=update_position_data,
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert update_position_response.status_code == 200

        # Vérifier la nouvelle valeur du portefeuille
        updated_portfolio_response = await test_client.get(
            f"/api/v1/portfolios/{created_portfolio['id']}/value",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        updated_portfolio_value = updated_portfolio_response.json()
        # Nouvelle valeur : (15 * 150) + (5 * 300) = 2250 + 1500 = 3750 USD
        assert float(updated_portfolio_value["current_value"]["amount"]) == 3750.00

        # Act & Assert - Étape 6 : Supprimer une position
        delete_position_response = await test_client.delete(
            f"/api/v1/portfolios/{created_portfolio['id']}/positions/{position_id}",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert delete_position_response.status_code == 204

        # Vérifier que la position a été supprimée
        final_portfolio_response = await test_client.get(
            f"/api/v1/portfolios/{created_portfolio['id']}/value",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        final_portfolio_value = final_portfolio_response.json()
        # Seule la position MSFT reste : 5 * 300 = 1500 USD
        assert float(final_portfolio_value["current_value"]["amount"]) == 1500.00
        assert len(final_portfolio_value["positions"]) == 1


@pytest.mark.e2e
@pytest.mark.asyncio
class TestInvestmentSearchScenario:
    """Scénario E2E : Recherche et filtrage d'investissements."""

    async def test_comprehensive_investment_search(
        self, test_client: AsyncClient, authenticated_user
    ):
        """
        Scénario de recherche complète d'investissements.

        Étapes :
        1. Créer plusieurs investissements de différents secteurs
        2. Rechercher par symbole
        3. Filtrer par secteur
        4. Filtrer par capitalisation
        5. Rechercher par nom
        6. Combinaisons de filtres
        """
        # Arrange - Créer une variété d'investissements
        investments_data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "LARGE",
                "current_price": {"amount": "150.00", "currency": "USD"},
            },
            {
                "symbol": "JNJ",
                "name": "Johnson & Johnson",
                "investment_type": "STOCK",
                "sector": "HEALTHCARE",
                "market_cap": "LARGE",
                "current_price": {"amount": "160.00", "currency": "USD"},
            },
            {
                "symbol": "XOM",
                "name": "Exxon Mobil Corporation",
                "investment_type": "STOCK",
                "sector": "ENERGY",
                "market_cap": "LARGE",
                "current_price": {"amount": "90.00", "currency": "USD"},
            },
            {
                "symbol": "SMALLTECH",
                "name": "Small Tech Company",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "SMALL",
                "current_price": {"amount": "25.00", "currency": "USD"},
            },
        ]

        # Créer tous les investissements
        for inv_data in investments_data:
            response = await test_client.post(
                "/api/v1/investments",
                json=inv_data,
                headers={"Authorization": f"Bearer {authenticated_user.token}"},
            )
            assert response.status_code == 201

        # Act & Assert - Étape 2 : Recherche par symbole
        symbol_response = await test_client.get(
            "/api/v1/investments?symbol=AAPL",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert symbol_response.status_code == 200
        symbol_results = symbol_response.json()
        assert len(symbol_results["investments"]) == 1
        assert symbol_results["investments"][0]["symbol"] == "AAPL"

        # Act & Assert - Étape 3 : Filtrage par secteur
        tech_response = await test_client.get(
            "/api/v1/investments?sector=TECHNOLOGY",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert tech_response.status_code == 200
        tech_results = tech_response.json()
        assert len(tech_results["investments"]) >= 2  # AAPL et SMALLTECH
        tech_symbols = [inv["symbol"] for inv in tech_results["investments"]]
        assert "AAPL" in tech_symbols
        assert "SMALLTECH" in tech_symbols

        # Act & Assert - Étape 4 : Filtrage par capitalisation
        large_cap_response = await test_client.get(
            "/api/v1/investments?market_cap=LARGE",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert large_cap_response.status_code == 200
        large_cap_results = large_cap_response.json()
        assert len(large_cap_results["investments"]) >= 3  # AAPL, JNJ, XOM
        large_cap_symbols = [inv["symbol"] for inv in large_cap_results["investments"]]
        assert "AAPL" in large_cap_symbols
        assert "JNJ" in large_cap_symbols
        assert "XOM" in large_cap_symbols
        assert "SMALLTECH" not in large_cap_symbols

        # Act & Assert - Étape 5 : Recherche par nom
        search_response = await test_client.get(
            "/api/v1/investments/search?q=Johnson",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results["investments"]) >= 1
        johnson_found = any(
            "Johnson" in inv["name"] for inv in search_results["investments"]
        )
        assert johnson_found

        # Act & Assert - Étape 6 : Combinaison de filtres
        combo_response = await test_client.get(
            "/api/v1/investments?sector=TECHNOLOGY&market_cap=LARGE",
            headers={"Authorization": f"Bearer {authenticated_user.token}"},
        )

        assert combo_response.status_code == 200
        combo_results = combo_response.json()

        # Devrait trouver seulement AAPL (Technology + Large Cap)
        combo_symbols = [inv["symbol"] for inv in combo_results["investments"]]
        assert "AAPL" in combo_symbols
        assert "SMALLTECH" not in combo_symbols  # Small cap
        assert "JNJ" not in combo_symbols  # Healthcare, pas Technology


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestUserJourneyScenario:
    """Scénario E2E complet : Parcours utilisateur de bout en bout."""

    async def test_complete_user_journey(self, test_client: AsyncClient):
        """
        Scénario complet d'un nouvel utilisateur qui :
        1. S'inscrit
        2. Se connecte
        3. Crée des investissements
        4. Crée un portefeuille
        5. Ajoute des positions
        6. Consulte ses performances
        7. Met à jour ses investissements
        8. Supprime son portefeuille
        """
        # Étape 1 : Inscription utilisateur
        signup_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "John",
            "last_name": "Doe",
        }

        signup_response = await test_client.post(
            "/api/v1/auth/signup", json=signup_data
        )
        assert signup_response.status_code == 201

        # Étape 2 : Connexion
        login_data = {"email": "newuser@example.com", "password": "SecurePassword123!"}

        login_response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200

        auth_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Étape 3 : Créer des investissements favoris
        favorite_investments = [
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "LARGE",
                "current_price": {"amount": "800.00", "currency": "USD"},
            },
            {
                "symbol": "AMD",
                "name": "Advanced Micro Devices",
                "investment_type": "STOCK",
                "sector": "TECHNOLOGY",
                "market_cap": "LARGE",
                "current_price": {"amount": "120.00", "currency": "USD"},
            },
        ]

        created_investments = []
        for inv_data in favorite_investments:
            response = await test_client.post(
                "/api/v1/investments", json=inv_data, headers=headers
            )
            assert response.status_code == 201
            created_investments.append(response.json())

        # Étape 4 : Créer un portefeuille long-terme
        portfolio_data = {
            "name": "Long Term Tech Growth",
            "description": "Portfolio for long-term technology growth investments",
            "currency": "USD",
        }

        portfolio_response = await test_client.post(
            "/api/v1/portfolios", json=portfolio_data, headers=headers
        )
        assert portfolio_response.status_code == 201
        portfolio = portfolio_response.json()

        # Étape 5 : Ajouter des positions initiales
        initial_positions = [
            {
                "investment_id": created_investments[0]["id"],
                "quantity": 2,
                "purchase_price": {"amount": "750.00", "currency": "USD"},
            },
            {
                "investment_id": created_investments[1]["id"],
                "quantity": 10,
                "purchase_price": {"amount": "110.00", "currency": "USD"},
            },
        ]

        for position_data in initial_positions:
            pos_response = await test_client.post(
                f"/api/v1/portfolios/{portfolio['id']}/positions",
                json=position_data,
                headers=headers,
            )
            assert pos_response.status_code == 201

        # Étape 6 : Consulter les performances initiales
        perf_response = await test_client.get(
            f"/api/v1/portfolios/{portfolio['id']}/value", headers=headers
        )
        assert perf_response.status_code == 200

        initial_performance = perf_response.json()
        # Valeur actuelle : (2 * 800) + (10 * 120) = 1600 + 1200 = 2800 USD
        # Coût d'achat : (2 * 750) + (10 * 110) = 1500 + 1100 = 2600 USD
        # Gain : 2800 - 2600 = 200 USD

        assert float(initial_performance["current_value"]["amount"]) == 2800.00
        assert float(initial_performance["total_cost"]["amount"]) == 2600.00
        assert float(initial_performance["total_gain"]["amount"]) == 200.00

        # Étape 7 : Mettre à jour les prix et voir l'impact
        price_updates = [
            {
                "investment_id": created_investments[0]["id"],
                "new_price": {"amount": "850.00", "currency": "USD"},
            },
            {
                "investment_id": created_investments[1]["id"],
                "new_price": {"amount": "130.00", "currency": "USD"},
            },
        ]

        for update in price_updates:
            update_response = await test_client.patch(
                f"/api/v1/investments/{update['investment_id']}",
                json={"current_price": update["new_price"]},
                headers=headers,
            )
            assert update_response.status_code == 200

        # Consulter les nouvelles performances
        updated_perf_response = await test_client.get(
            f"/api/v1/portfolios/{portfolio['id']}/value", headers=headers
        )
        assert updated_perf_response.status_code == 200

        updated_performance = updated_perf_response.json()
        # Nouvelle valeur : (2 * 850) + (10 * 130) = 1700 + 1300 = 3000 USD
        # Nouveau gain : 3000 - 2600 = 400 USD

        assert float(updated_performance["current_value"]["amount"]) == 3000.00
        assert float(updated_performance["total_gain"]["amount"]) == 400.00

        # Étape 8 : Supprimer le portefeuille (nettoyage)
        delete_response = await test_client.delete(
            f"/api/v1/portfolios/{portfolio['id']}", headers=headers
        )
        assert delete_response.status_code == 204

        # Vérifier que le portefeuille n'existe plus
        get_deleted_response = await test_client.get(
            f"/api/v1/portfolios/{portfolio['id']}", headers=headers
        )
        assert get_deleted_response.status_code == 404
