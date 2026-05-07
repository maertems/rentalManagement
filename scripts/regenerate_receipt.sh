#!/bin/bash
# Regénère le PDF d'une quittance existante et envoie optionnellement l'email.
#
# Usage :
#   ./regenerate_receipt.sh --tenant-id 42 --month 2026-04
#   ./regenerate_receipt.sh --tenant-id 42 --month 2026-04 --force
#   ./regenerate_receipt.sh --tenant-id 42 --month 2026-04 --send-email
#   ./regenerate_receipt.sh --tenant-id 42 --month 2026-04 --dry-run
#
# Prérequis : curl, jq

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../data/api/.env"
COOKIE_FILE="/tmp/rental_session.txt"

# --- Valeurs par défaut depuis .env ---
load_env() {
    local key="$1" default="$2"
    if [ -f "$ENV_FILE" ]; then
        local val
        val=$(grep -E "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
        [ -n "$val" ] && echo "$val" && return
    fi
    echo "$default"
}

API_URL=$(load_env "VITE_API_BASE_URL" "http://localhost:8000")
API_EMAIL=$(load_env "ADMIN_EMAIL" "")
TENANT_ID=""
MONTH=""
FORCE=false
SEND_EMAIL=false
DRY_RUN=false

# --- Parsing des arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --tenant-id)   TENANT_ID="$2";  shift 2 ;;
        --month)       MONTH="$2";      shift 2 ;;
        --api-url)     API_URL="$2";    shift 2 ;;
        --api-email)   API_EMAIL="$2";  shift 2 ;;
        --force)       FORCE=true;      shift ;;
        --send-email)  SEND_EMAIL=true; shift ;;
        --dry-run)     DRY_RUN=true;    shift ;;
        *) echo "Option inconnue : $1"; exit 1 ;;
    esac
done

if [ -z "$TENANT_ID" ] || [ -z "$MONTH" ]; then
    echo "Usage : $0 --tenant-id ID --month YYYY-MM [--force] [--send-email] [--dry-run]"
    exit 1
fi

if ! echo "$MONTH" | grep -qE '^[0-9]{4}-[0-9]{2}$'; then
    echo "Erreur : format de mois invalide '$MONTH'. Attendu : YYYY-MM"
    exit 1
fi

# --- Auth : réutilise le cookie si le token est encore valide ---
auth_check() {
    [ -f "$COOKIE_FILE" ] || return 1
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_FILE" "$API_URL/api/v1/auth/me")
    [ "$code" = "200" ]
}

auth_login() {
    if [ -z "$API_EMAIL" ]; then
        read -r -p "Email API : " API_EMAIL
    fi
    read -r -s -p "Mot de passe : " API_PASSWORD
    echo ""

    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$API_EMAIL\",\"password\":\"$API_PASSWORD\"}" \
        -c "$COOKIE_FILE")

    if [ "$code" != "200" ]; then
        echo "Erreur d'authentification (HTTP $code)."
        exit 1
    fi
    echo "Authentifié."
}

echo "=== Regénération de quittance ==="
echo "Locataire : $TENANT_ID | Mois : $MONTH | Force PDF : $FORCE | Email : $SEND_EMAIL"
echo ""

if auth_check; then
    echo "Session existante réutilisée."
else
    auth_login
fi

# --- Calcul de la plage de dates du mois ---
PERIOD_BEGIN="${MONTH}-01"
PERIOD_END=$(date -d "${PERIOD_BEGIN} +1 month -1 day" +%Y-%m-%d)

# --- Recherche de la quittance ---
echo "Recherche de la quittance..."
RECEIPTS=$(curl -s -b "$COOKIE_FILE" \
    "$API_URL/api/v1/rentReceipts?tenantId=${TENANT_ID}&periodBeginGte=${PERIOD_BEGIN}T00:00:00&periodBeginLte=${PERIOD_END}T23:59:59")

RECEIPT_ID=$(echo "$RECEIPTS" | jq -r 'if type == "array" then .[0].id else empty end')
if [ -z "$RECEIPT_ID" ] || [ "$RECEIPT_ID" = "null" ]; then
    echo "Erreur : aucune quittance trouvée pour locataire=$TENANT_ID mois=$MONTH"
    echo "Réponse API : $RECEIPTS"
    exit 1
fi
echo "Quittance id=$RECEIPT_ID trouvée."

# --- Dry-run ---
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "[DRY-RUN] Aurait régénéré le PDF de la quittance id=$RECEIPT_ID."
    [ "$SEND_EMAIL" = true ] && echo "[DRY-RUN] Aurait envoyé l'email."
    exit 0
fi

# --- Régénération du PDF ---
echo "Génération du PDF..."
FORCE_PARAM=""
[ "$FORCE" = true ] && FORCE_PARAM="?force=true"
PDF_RESP=$(curl -s -X POST -b "$COOKIE_FILE" \
    "$API_URL/api/v1/rentReceipts/${RECEIPT_ID}/pdf${FORCE_PARAM}")
PDF_FILENAME=$(echo "$PDF_RESP" | jq -r '.filename // empty')
if [ -z "$PDF_FILENAME" ] || [ "$PDF_FILENAME" = "null" ]; then
    echo "Erreur génération PDF : $PDF_RESP"
    exit 1
fi
echo "  → $PDF_FILENAME"

# --- Envoi email ---
if [ "$SEND_EMAIL" = true ]; then
    echo "Envoi de l'email..."
    EMAIL_RESP=$(curl -s -X POST -b "$COOKIE_FILE" \
        "$API_URL/api/v1/rentReceipts/${RECEIPT_ID}/email?force=true")
    SENT=$(echo "$EMAIL_RESP" | jq -r '.sent // empty')
    if [ "$SENT" = "true" ]; then
        TO=$(echo "$EMAIL_RESP" | jq -r '.to // ""')
        echo "  → Email envoyé à $TO"
    else
        REASON=$(echo "$EMAIL_RESP" | jq -r '.reason // "erreur inconnue"')
        echo "  → Email non envoyé : $REASON"
    fi
fi

echo ""
echo "Done."
