#!/usr/bin/env python3
"""
Génère une quittance (rentReceipt + rentReceiptsDetails) pour un locataire et un mois donnés,
génère le PDF via l'API, et envoie le document par email si tenant.sendNoticeOfLeaseRental == 1.

Prérequis (dans l'image Docker) :
    pymysql, requests  (voir Dockerfile)

Usage :
    docker-compose run --rm generate-receipt --tenant-id 42 --month 2026-04
    docker-compose run --rm generate-receipt --tenant-id 42 --month 2026-04 --dry-run

Options :
    --tenant-id ID        ID du locataire (requis)
    --month YYYY-MM       Mois de la quittance (défaut: mois suivant — ex: lancé le 25/04 → 2026-05)
    --api-url URL         URL de l'API (défaut: http://localhost:8000)
    --api-email EMAIL     Email admin API (défaut: ADMIN_EMAIL dans .env)
    --api-password PASS   Mot de passe admin API (défaut: ADMIN_PASSWORD dans .env)
    --smtp-host HOST      Serveur SMTP (défaut: SMTP_HOST dans .env)
    --smtp-port PORT      Port SMTP (défaut: 25)
    --dry-run             Afficher ce qui serait fait sans rien écrire ni envoyer

Notes :
    - Les rents de type "Garantie" sont exclus (document séparé).
    - Si une quittance existe déjà pour ce locataire et ce mois → abandon.
    - PDF généré via POST /api/v1/rentReceipts/{id}/pdf (stocké dans /app/files/).
    - Email envoyé uniquement si tenant.sendNoticeOfLeaseRental == 1.
      From/CC : email du propriétaire. To : email du locataire.
"""

import argparse
import calendar
import smtplib
import sys
from datetime import date, datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("Erreur : pymysql non installé.")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Erreur : requests non installé.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_dotenv(env_path: str) -> dict:
    """Parseur .env minimal — pas de dépendance externe."""
    result = {}
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return result


def next_month(today: date) -> date:
    """Retourne le 1er jour du mois suivant."""
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def parse_month(month_str: str | None) -> tuple[date, date]:
    if month_str is None:
        first = next_month(date.today())
    else:
        try:
            year, month = map(int, month_str.split("-"))
            first = date(year, month, 1)
        except (ValueError, AttributeError):
            print(f"Erreur : format de mois invalide '{month_str}'. Attendu : YYYY-MM")
            sys.exit(1)
    last = date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
    return first, last


def fmt_price(amount: float) -> str:
    return f"{amount:,.2f} €".replace(",", " ")


RENT_TYPE_ORDER = {"Loyer": 1, "Charges": 2}

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


# ---------------------------------------------------------------------------
# API client (génération PDF)
# ---------------------------------------------------------------------------

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def login(self, email: str, password: str) -> None:
        r = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        if r.status_code != 200:
            print(f"Erreur auth API ({r.status_code}) : {r.text}")
            sys.exit(1)

    def generate_pdf(self, receipt_id: int) -> str:
        """POST /{id}/pdf → retourne le filename."""
        r = self.session.post(f"{self.base_url}/api/v1/rentReceipts/{receipt_id}/pdf")
        if r.status_code == 201:
            return r.json()["filename"]
        if r.status_code == 409:
            return r.json().get("detail", "").replace("PDF already exists: ", "")
        print(f"Erreur génération PDF ({r.status_code}) : {r.text}")
        sys.exit(1)

    def download_pdf(self, receipt_id: int) -> bytes:
        """GET /{id}/pdf → retourne les bytes du PDF."""
        r = self.session.get(f"{self.base_url}/api/v1/rentReceipts/{receipt_id}/pdf")
        if r.status_code == 200:
            return r.content
        print(f"Erreur téléchargement PDF ({r.status_code}) : {r.text}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(
    smtp_host: str,
    smtp_port: int,
    from_addr: str,
    from_name: str,
    to_addr: str,
    to_name: str,
    subject: str,
    body: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = f"{to_name} <{to_addr}>"
    msg["Cc"] = from_addr
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))
    attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename=pdf_filename)
    msg.attach(attachment)

    # Port 465 → SSL direct ; port 587 ou autre → STARTTLS ; port 25 → plain
    if smtp_port == 465:
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ctx) as smtp:
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.sendmail(from_addr, [to_addr, from_addr], msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            if smtp_port == 587:
                smtp.starttls()
            if smtp_user and smtp_password:
                smtp.login(smtp_user, smtp_password)
            smtp.sendmail(from_addr, [to_addr, from_addr], msg.as_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère une quittance + PDF + email pour un locataire et un mois donnés."
    )
    parser.add_argument("--tenant-id", type=int, required=True)
    parser.add_argument("--month", default=None, help="Format YYYY-MM (défaut: mois suivant)")
    parser.add_argument("--host", default="127.0.0.1", help="Hôte MySQL")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", default="rental")
    parser.add_argument("--password", default="rental")
    parser.add_argument("--db", default="rental")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--api-email", default=None)
    parser.add_argument("--api-password", default=None)
    parser.add_argument("--smtp-host", default=None)
    parser.add_argument("--smtp-port", type=int, default=None)
    parser.add_argument("--smtp-user", default=None)
    parser.add_argument("--smtp-password", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Lire .env pour les credentials API et SMTP
    env_path = Path(__file__).resolve().parent.parent / ".env"
    env = load_dotenv(str(env_path))
    api_email = args.api_email or env.get("ADMIN_EMAIL")
    api_password = args.api_password or env.get("ADMIN_PASSWORD")

    smtp_host = args.smtp_host or env.get("SMTP_HOST", "localhost")
    smtp_port = args.smtp_port or int(env.get("SMTP_PORT", "25"))
    smtp_user = args.smtp_user or env.get("SMTP_USER") or None
    smtp_password = args.smtp_password or env.get("SMTP_PASSWORD") or None

    if not api_email or not api_password:
        print("Erreur : credentials API manquants (ADMIN_EMAIL/ADMIN_PASSWORD dans .env ou --api-email/--api-password)")
        sys.exit(1)

    period_begin, period_end = parse_month(args.month)
    month_name = MONTHS_FR[period_begin.month - 1]
    year = period_begin.year

    # ------------------------------------------------------------------
    # DB
    # ------------------------------------------------------------------
    conn = pymysql.connect(
        host=args.host, port=args.port,
        user=args.user, password=args.password,
        database=args.db, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    with conn:
        with conn.cursor() as cur:

            # --- Tenant -----------------------------------------------
            cur.execute("SELECT * FROM tenants WHERE id = %s", (args.tenant_id,))
            tenant = cur.fetchone()
            if not tenant:
                print(f"Erreur : locataire id={args.tenant_id} introuvable.")
                sys.exit(1)

            tenant_name = " ".join(filter(None, [tenant.get("firstName"), tenant.get("name")]))
            print(f"Locataire : [{tenant['id']}] {tenant_name}")

            # --- Owner (via placeUnit → place → owner) ----------------
            owner = None
            unit = None
            if tenant.get("placeUnitId"):
                cur.execute("SELECT * FROM placesUnits WHERE id = %s", (tenant["placeUnitId"],))
                unit = cur.fetchone()
            if unit and unit.get("placeId"):
                cur.execute("SELECT * FROM places WHERE id = %s", (unit["placeId"],))
                place = cur.fetchone()
                if place and place.get("ownerId"):
                    cur.execute("SELECT * FROM owners WHERE id = %s", (place["ownerId"],))
                    owner = cur.fetchone()

            unit_friendly = (unit or {}).get("friendlyName") or (unit or {}).get("name") or ""
            owner_email = (owner or {}).get("email") or ""
            owner_name = (owner or {}).get("name") or ""
            tenant_email = tenant.get("email") or ""

            print(f"  Propriétaire : {owner_name} <{owner_email}>")
            print(f"  Email locataire : {tenant_email}")
            print(f"  sendNoticeOfLeaseRental : {tenant.get('sendNoticeOfLeaseRental')}")

            # --- Doublon ----------------------------------------------
            next_month_begin = (
                datetime(year, period_begin.month + 1, 1)
                if period_begin.month < 12
                else datetime(year + 1, 1, 1)
            )
            cur.execute(
                "SELECT id FROM rentReceipts WHERE tenantId = %s AND periodBegin >= %s AND periodBegin < %s LIMIT 1",
                (args.tenant_id, datetime(year, period_begin.month, 1), next_month_begin),
            )
            existing = cur.fetchone()
            if existing:
                print(f"\nAvertissement : quittance déjà existante pour {period_begin.strftime('%Y-%m')} (id={existing['id']}). Abandon.")
                sys.exit(0)

            # --- Rents actifs (hors Garantie) -------------------------
            cur.execute(
                "SELECT * FROM rents WHERE tenantId = %s AND active = 1 AND type != 'Garantie'",
                (args.tenant_id,),
            )
            rents = cur.fetchall()
            if not rents:
                print(f"\nAvertissement : aucun loyer/charge actif pour le locataire {args.tenant_id}. Abandon.")
                sys.exit(1)

            rents.sort(key=lambda r: (RENT_TYPE_ORDER.get(r.get("type") or "", 99), r["id"]))
            total = sum(float(r["price"] or 0) for r in rents)

            # --- Résumé -----------------------------------------------
            print(f"\nPériode : {period_begin.strftime('%d/%m/%Y')} → {period_end.strftime('%d/%m/%Y')}")
            print("Lignes de détail :")
            for i, r in enumerate(rents, 1):
                print(f"  {i}. [{r['type']}] {fmt_price(float(r['price'] or 0))}")
            print(f"  Total : {fmt_price(total)}")

            send_email_flag = bool(tenant.get("sendNoticeOfLeaseRental"))
            print(f"\nEnvoi email : {'oui' if send_email_flag else 'non (sendNoticeOfLeaseRental = 0)'}")
            if send_email_flag and not tenant_email:
                print("  ⚠ Pas d'email locataire — envoi ignoré.")
                send_email_flag = False
            if send_email_flag and not owner_email:
                print("  ⚠ Pas d'email propriétaire — envoi ignoré.")
                send_email_flag = False

            if args.dry_run:
                print("\n[DRY-RUN] Aucune écriture ni envoi effectué.")
                return

            # --- Créer la quittance -----------------------------------
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            cur.execute(
                """
                INSERT INTO rentReceipts
                    (tenantId, placeUnitId, placeUnitRoomId, amount, periodBegin, periodEnd, paid, createdAt, updatedAt)
                VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s)
                """,
                (
                    args.tenant_id,
                    tenant.get("placeUnitId"),
                    tenant.get("placeUnitRoomId"),
                    total,
                    datetime(period_begin.year, period_begin.month, period_begin.day).strftime("%Y-%m-%d %H:%M:%S.000"),
                    datetime(period_end.year, period_end.month, period_end.day).strftime("%Y-%m-%d %H:%M:%S.000"),
                    now, now,
                ),
            )
            receipt_id = cur.lastrowid
            print(f"\nrentReceipt créé : id={receipt_id}")

            for i, r in enumerate(rents, 1):
                cur.execute(
                    "INSERT INTO rentReceiptsDetail (rentReceiptsId, sortOrder, description, price, createdAt, updatedAt) VALUES (%s, %s, %s, %s, %s, %s)",
                    (receipt_id, i, r["type"], float(r["price"] or 0), now, now),
                )
            print(f"{len(rents)} ligne(s) de détail créée(s).")
            conn.commit()

    # ------------------------------------------------------------------
    # PDF via API
    # ------------------------------------------------------------------
    print(f"\nGénération du PDF (API {args.api_url}) …")
    api = APIClient(args.api_url)
    api.login(api_email, api_password)
    pdf_filename = api.generate_pdf(receipt_id)
    print(f"  → {pdf_filename}")

    pdf_bytes = api.download_pdf(receipt_id)
    print(f"  → PDF téléchargé ({len(pdf_bytes)} octets)")

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------
    if not send_email_flag:
        print(f"\nDone. Quittance id={receipt_id} pour {tenant_name} ({period_begin.strftime('%Y-%m')}).")
        return

    subject = f"Avis d'échéance - {unit_friendly}" if unit_friendly else "Avis d'échéance"
    body = (
        f"Bonjour,\n\n"
        f"Vous trouverez ci-joint l'avis d'échéance du mois de {month_name} {year}.\n"
        f"Vous souhaitant bonne réception.\n\n"
        f"Bonne journée,\n"
        f"{owner_name}\n"
    )

    print(f"\nEnvoi email à {tenant_email} …")
    print(f"  Sujet : {subject}")
    print(f"  SMTP  : {smtp_host}:{smtp_port}" + (" (auth)" if smtp_user else ""))

    try:
        send_email(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_addr=owner_email,
            from_name=owner_name,
            to_addr=tenant_email,
            to_name=tenant_name,
            subject=subject,
            body=body,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )
        print("  → Email envoyé.")
    except Exception as e:
        print(f"  ⚠ Échec envoi email : {e}")

    print(f"\nDone. Quittance id={receipt_id} pour {tenant_name} ({period_begin.strftime('%Y-%m')}).")


if __name__ == "__main__":
    main()
