#!/bin/bash

# Script pour tester l'endpoint recommendations facilement

API_URL="http://localhost:8005"

echo "🎯 Test de l'endpoint /api/v1/investment/recommendations"
echo "======================================================="

echo "📊 Test GET avec paramètres par défaut..."
curl -s "${API_URL}/api/v1/investment/recommendations" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Total recommandations: {data['analysis_summary']['total_recommendations']}\")
print(f\"STRONG BUY: {data['analysis_summary']['strong_buy_count']}\")
for rec in data['strong_buy_recommendations'][:2]:
    print(f\"📈 {rec['symbol']} - Score: {rec['confidence_score']}, Return: {rec['potential_return']}%\")
    print(f\"   Prix: \${rec['current_price']:.2f} → \${rec['target_price']:.2f}\")
"

echo -e "\n\n🔥 Test GET avec score de confiance élevé (85%)..."
curl -s "${API_URL}/api/v1/investment/recommendations?min_confidence_score=85&max_recommendations=3&min_market_cap=5000000000" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Total recommandations: {data['analysis_summary']['total_recommendations']}\")
for rec in data['strong_buy_recommendations']:
    print(f\"📈 {rec['symbol']} - {rec['name']}\")
    print(f\"   Prix: \${rec['current_price']:.2f} → \${rec['target_price']:.2f} (+{rec['potential_return']}%)\")
    print(f\"   Secteur: {rec['sector']}, Risque: {rec['risk_level']}\")
"

echo -e "\n\n💰 Test POST avec paramètres JSON..."
curl -X POST "${API_URL}/api/v1/investment/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "min_confidence_score": 80.0,
    "max_recommendations": 2,
    "min_market_cap": 10000000000,
    "max_risk_level": "LOW",
    "preferred_horizon": "LONG_TERM"
  }' | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Total recommandations: {data['analysis_summary']['total_recommendations']}\")
for rec in data['strong_buy_recommendations']:
    print(f\"📈 {rec['symbol']} - Confiance: {rec['confidence_score']}%\")
    print(f\"   Raisons: {', '.join(rec['reasons'])}\")
"

echo -e "\n✅ Tests terminés !"
echo "📖 Utilisations possibles :"
echo "   GET: curl \"${API_URL}/api/v1/investment/recommendations?min_confidence_score=75&max_recommendations=5\""
echo "   POST: curl -X POST \"${API_URL}/api/v1/investment/recommendations\" -H \"Content-Type: application/json\" -d '{...}'"
