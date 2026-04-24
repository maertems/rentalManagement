#!/bin/bash
# Lance le container MySQL.
# Peut être ignoré si vous utilisez un serveur MySQL externe.
# Lancer depuis n'importe où — le script calcule les chemins automatiquement.

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

docker run -d \
  --name rental_mysql \
  --network rental \
  --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=rental \
  -e MYSQL_USER=rental \
  -e MYSQL_PASSWORD=rental \
  -p 3306:3306 \
  -v "$PROJECT_ROOT/data/mysql:/var/lib/mysql" \
  -v "$PROJECT_ROOT/build/mysql/001_schema.sql:/docker-entrypoint-initdb.d/001_schema.sql:ro" \
  mysql:8.0

echo "MySQL démarré — attendre quelques secondes le temps de l'initialisation."
