#!/bin/bash
# Build et lance le container API.
# Lancer depuis n'importe où — le script calcule les chemins automatiquement.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Build de l'image rental_api..."
docker build -t rental_api "$SCRIPT_DIR"

docker run -d \
  --name rental_api \
  --network rental \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file "$PROJECT_ROOT/data/api/.env" \
  -v "$PROJECT_ROOT/data/api/files:/app/files" \
  rental_api

echo "API démarrée sur http://localhost:8000"
echo "Swagger : http://localhost:8000/docs"
