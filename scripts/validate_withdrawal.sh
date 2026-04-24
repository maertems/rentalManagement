#!/bin/bash
# Usage: ./validate_withdrawal.sh "NOM DU LOCATAIRE" 800.00

set -e

NAME="$1"
RENT="$2"

if [ -z "$NAME" ] || [ -z "$RENT" ]; then
    echo "Usage: $0 \"NOM DU LOCATAIRE\" MONTANT"
    echo "  ex: $0 \"DUPONT\" 800.00"
    exit 1
fi

API_URL="${API_URL:-http://localhost:8000}"

if [ -z "$API_EMAIL" ] || [ -z "$API_PASSWORD" ]; then
    echo "Erreur : les variables d'environnement API_EMAIL et API_PASSWORD sont requises."
    echo "  ex: API_EMAIL=admin@example.com API_PASSWORD=secret $0 \"DUPONT\" 800.00"
    exit 1
fi

# 1. Authentification
COOKIE_FILE=$(mktemp)
curl -s -c "$COOKIE_FILE" -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$API_EMAIL\",\"password\":\"$API_PASSWORD\"}" > /dev/null

# 2. Validation du virement
curl -s -b "$COOKIE_FILE" -X POST "$API_URL/api/v1/withdraw/validate" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$NAME\",\"rent\":\"$RENT\"}" | python3 -m json.tool

rm -f "$COOKIE_FILE"
