#!/usr/bin/env python3
"""
Remet la base MySQL à zéro : TRUNCATE toutes les tables et réinitialise
les AUTO_INCREMENT à 1.

Prérequis:
    pip install pymysql

Usage:
    python reset_database.py [options]

    Options:
      --host HOST       Hôte MySQL (défaut: 127.0.0.1)
      --port PORT       Port MySQL (défaut: 3306)
      --user USER       Utilisateur MySQL (défaut: rental)
      --password PASS   Mot de passe MySQL (défaut: rental)
      --db DATABASE     Nom de la base (défaut: rental)
      --force           Ne pas demander de confirmation

Notes:
  - TRUNCATE supprime toutes les lignes ET remet l'AUTO_INCREMENT à 1.
  - L'admin sera recréé automatiquement au prochain démarrage de l'API.
  - La base n'a pas de FK : TRUNCATE peut se faire dans n'importe quel ordre.
"""

import argparse
import sys

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("Erreur : pymysql non installé. Lancez : pip install pymysql")
    sys.exit(1)


# Toutes les tables dans un ordre logique (des plus dépendantes aux parents)
# L'ordre n'est pas obligatoire sans FK, mais reste lisible.
TABLES = [
    "rentReceiptsDetail",
    "rentsFees",
    "rents",
    "rentReceipts",
    "tenants",
    "placesUnitsRooms",
    "placesUnits",
    "places",
    "owners",
    "users",
]


def main():
    parser = argparse.ArgumentParser(
        description="Remet la base MySQL à zéro (TRUNCATE + AUTO_INCREMENT reset)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="rental")
    parser.add_argument("--password", default="rental")
    parser.add_argument("--db", default="rental")
    parser.add_argument("--force", action="store_true",
                        help="Passer la confirmation interactive")
    args = parser.parse_args()

    print("=" * 60)
    print("Reset base de données MySQL")
    print("=" * 60)
    print(f"Base    : {args.db}  sur  {args.host}:{args.port}")
    print(f"Tables  : {', '.join(TABLES)}")
    print()

    if not args.force:
        answer = input("⚠️  Cette opération est IRRÉVERSIBLE. Continuer ? [oui/N] : ").strip().lower()
        if answer not in ("oui", "o", "yes", "y"):
            print("Annulé.")
            sys.exit(0)

    try:
        conn = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.db,
            charset="utf8mb4",
            autocommit=True,
        )
        cursor = conn.cursor()
        print(f"\nConnecté à MySQL {args.host}:{args.port}/{args.db}\n")
    except Exception as e:
        print(f"Erreur de connexion MySQL : {e}")
        sys.exit(1)

    try:
        # Désactiver temporairement les checks de FK (sécurité, même si on n'en a pas)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        for table in TABLES:
            cursor.execute(f"TRUNCATE TABLE `{table}`")
            print(f"  ✓ TRUNCATE {table}")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        print(f"\n✓ {len(TABLES)} table(s) vidée(s). AUTO_INCREMENT remis à 1.")
        print("\nL'admin sera recréé automatiquement au prochain démarrage de l'API.")

    except Exception as e:
        print(f"\n✗ Erreur : {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
