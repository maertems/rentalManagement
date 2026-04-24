#!/bin/bash
# Démarre tous les containers du projet (MySQL + API + Frontend).
# À lancer depuis la racine du projet.
#
# Usage :
#   ./docker-start.sh          — démarre tout (MySQL inclus)
#   ./docker-start.sh --no-db  — démarre API + Frontend uniquement (MySQL externe)

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
NO_DB=false

for arg in "$@"; do
  case $arg in
    --no-db) NO_DB=true ;;
  esac
done

# Créer le réseau si inexistant
if ! docker network inspect rental &>/dev/null; then
  echo "Création du réseau Docker 'rental'..."
  docker network create rental
fi

# MySQL
if [ "$NO_DB" = false ]; then
  echo ""
  echo "=== MySQL ==="
  bash "$PROJECT_ROOT/build/mysql/docker.sh"
  echo "Attente de la disponibilité de MySQL..."
  sleep 8
fi

# API
echo ""
echo "=== API ==="
bash "$PROJECT_ROOT/build/api/docker.sh"

# Frontend
echo ""
echo "=== Frontend ==="
bash "$PROJECT_ROOT/build/front/docker.sh"

echo ""
echo "Tous les services sont démarrés :"
echo "  Frontend : http://localhost:5173"
echo "  API      : http://localhost:8000"
echo "  Swagger  : http://localhost:8000/docs"
