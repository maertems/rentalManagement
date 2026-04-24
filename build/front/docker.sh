#!/bin/bash
# Build et lance le container Frontend (Vite dev server avec HMR).
# Lancer depuis n'importe où — le script calcule les chemins automatiquement.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Build de l'image rental_front..."
docker build -t rental_front "$SCRIPT_DIR"

docker run -d \
  --name rental_front \
  --restart unless-stopped \
  -p 5173:5173 \
  -v "$SCRIPT_DIR:/app" \
  -v /app/node_modules \
  -e CHOKIDAR_USEPOLLING=true \
  -e VITE_API_BASE_URL="http://localhost:8000" \
  rental_front

echo "Frontend démarré sur http://localhost:5173"
