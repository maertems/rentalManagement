#!/bin/bash
# Build et lance le container Frontend (Vite dev server avec HMR).
# Lancer depuis n'importe où — le script calcule les chemins automatiquement.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/data/api/.env"

VITE_API_BASE_URL="http://localhost:8000"
if [ -f "$ENV_FILE" ]; then
  VITE_API_BASE_URL=$(grep -E "^VITE_API_BASE_URL=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

echo "Arrêt et suppression du container existant..."
docker stop rental_front 2>/dev/null || true
docker rm rental_front 2>/dev/null || true

echo "Build de l'image rental_front..."
docker build -t rental_front "$SCRIPT_DIR"

docker run -d \
  --name rental_front \
  --restart unless-stopped \
  -p 5173:5173 \
  -v "$SCRIPT_DIR:/app" \
  -v /app/node_modules \
  -e CHOKIDAR_USEPOLLING=true \
  -e VITE_API_BASE_URL="$VITE_API_BASE_URL" \
  rental_front

echo "Frontend démarré sur http://localhost:5173"
