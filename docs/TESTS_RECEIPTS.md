# Tests — Génération quittances, envoi email, validation virement

Ce document décrit comment tester manuellement les deux flux principaux de gestion des quittances :

1. **Flux avis d'échéance** (`generate_receipt.py`) — lancé le 25 du mois, génère la quittance du mois suivant et envoie l'avis si coché
2. **Flux quittance de loyer / garantie** (`validate_withdrawal.py` — *à créer*) — déclenché à réception du virement, marque `paid=1` et envoie la quittance si cochée

---

## Prérequis communs

### Services en cours d'exécution

```bash
# API + MySQL
cd /data/lolo/dev/rentalManagement/api
sudo docker-compose up -d

# Frontend (optionnel mais utile pour vérifier visuellement)
cd /home/lolo/dev/rentalManagement/front
sudo docker-compose up -d
```

### Authentification curl

Toutes les commandes curl suivantes nécessitent un cookie de session. Se connecter une fois :

```bash
curl -s -c /tmp/rental.txt -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.com","password":"admin123"}'
```

Le cookie est sauvegardé dans `/tmp/rental.txt` et réutilisé avec `-b /tmp/rental.txt` dans toutes les commandes suivantes.

### Données de test en base

Le locataire de test doit avoir :

| Champ DB | Valeur | Rôle |
|----------|--------|------|
| `active` | `1` | Locataire actif |
| `placeUnitId` | un ID valide | Détermine le bien → propriétaire |
| `email` | adresse valide | Destinataire de l'email |
| `sendNoticeOfLeaseRental` | `1` ou `0` | Active/désactive l'envoi de l'avis d'échéance |
| `sendLeaseRental` | `1` ou `0` | Active/désactive l'envoi de la quittance de loyer |
| `withdrawName` | ex. `"Dupont Jean"` | Utilisé pour matcher le virement bancaire |
| `withdrawDay` | ex. `5` | Jour de prélèvement (utilisé dans l'avis : "exigible le 05/MM/YYYY") |

Rents actifs associés (hors `Garantie`) :

| `type` | `active` | `price` |
|--------|----------|---------|
| `Loyer` | `1` | ex. `800.00` |
| `Charges` | `1` | ex. `50.00` |

**Modifier les flags via l'API :**

```bash
# Activer l'envoi de l'avis d'échéance pour un locataire
curl -s -b /tmp/rental.txt -X PATCH http://localhost:8000/api/v1/tenants/<ID> \
  -H "Content-Type: application/json" \
  -d '{"sendNoticeOfLeaseRental": 1}'

# Activer l'envoi de la quittance de loyer
curl -s -b /tmp/rental.txt -X PATCH http://localhost:8000/api/v1/tenants/<ID> \
  -H "Content-Type: application/json" \
  -d '{"sendLeaseRental": 1}'
```

Ou directement depuis le frontend (`/tenants` → Modifier le locataire).

---

## 1. Flux avis d'échéance — `generate_receipt.py`

### Ce que fait le script

```
DB: rents actifs (Loyer + Charges) → calcul total
DB: INSERT rentReceipts + rentReceiptsDetail
API: POST /rentReceipts/{id}/pdf  → génère le PDF (avis d'échéance, car paid=0)
API: GET  /rentReceipts/{id}/pdf  → télécharge le PDF
Si sendNoticeOfLeaseRental==1 : SMTP → envoie le PDF en PJ à l'email du locataire
```

Le PDF généré est de type **avis d'échéance** car la quittance est créée avec `paid=0`. Le type est auto-détecté.

### Commandes de test

Les scripts tournent dans leur propre conteneur Docker (`api/scripts/`) avec `network_mode: host` pour accéder à MySQL et à l'API sur `localhost`.

```bash
cd /data/lolo/dev/rentalManagement/api/scripts

# Builder l'image (une seule fois, ou après modif des scripts)
sudo docker-compose build
```

#### Dry-run — vérifier sans rien écrire

```bash
sudo docker-compose run --rm generate-receipt \
  --tenant-id <ID> \
  --month 2026-05 \
  --dry-run
```

Sortie attendue :
```
Locataire : [12] Jean Dupont
  Propriétaire : SCI Dupont <contact@sci-dupont.fr>
  Email locataire : jean.dupont@gmail.com
  sendNoticeOfLeaseRental : 1

Période : 01/05/2026 → 31/05/2026
Lignes de détail :
  1. [Loyer] 800,00 €
  2. [Charges] 50,00 €
  Total : 850,00 €

Envoi email : oui

[DRY-RUN] Aucune écriture ni envoi effectué.
```

#### Exécution réelle — mois forcé

```bash
sudo docker-compose run --rm generate-receipt \
  --tenant-id <ID> \
  --month 2026-05
```

Sortie attendue :
```
Locataire : [12] Jean Dupont
  ...
rentReceipt créé : id=47
2 ligne(s) de détail créée(s).

Génération du PDF (API http://localhost:8000) …
  → 59000-LeonBlum-Appt1.2026-05.AvisEcheance.pdf
  → PDF téléchargé (18432 octets)

Envoi email à jean.dupont@gmail.com …
  Sujet : Avis d'échéance - Appt1
  SMTP  : mail.notrebicoque.com:25
  → Email envoyé.

Done. Quittance id=47 pour Jean Dupont (2026-05).
```

#### Exécution sans mois — calcule automatiquement le mois suivant

```bash
# Lancé le 25 avril → génère mai
sudo docker-compose run --rm generate-receipt --tenant-id <ID>
```

### Ce qu'il faut vérifier

**La quittance créée (via API) :**
```bash
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/47 | jq .
# Attendu : paid=0, periodBegin="2026-05-01...", amount=850.0
```

**Les détails de la quittance :**
```bash
curl -s -b /tmp/rental.txt "http://localhost:8000/api/v1/rentReceiptsDetails?rentReceiptsId=47" | jq .
# Attendu : 2 lignes — Loyer 800, Charges 50
```

**Le PDF sur disque (volume monté) :**
```bash
ls /data/lolo/dev/rentalManagement/api/files/*.2026-05.AvisEcheance.pdf
```

**Télécharger le PDF via l'API :**
```bash
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/47/pdf \
  -o /tmp/avis-test.pdf
xdg-open /tmp/avis-test.pdf
```

**Via le frontend (`http://localhost:5173/tenants`) :**
- Cliquer l'œil (quittances) du locataire
- La nouvelle quittance apparaît avec `paid=❌` (croix rouge)
- Cliquer l'œil par ligne → le PDF s'ouvre dans un onglet

### Cas d'erreur à tester

| Scénario | Commande | Résultat attendu |
|----------|----------|------------------|
| Doublon (même mois) | Relancer la même commande | `Avertissement : quittance déjà existante … Abandon.` |
| Tenant inexistant | `--tenant-id 9999` | `Erreur : locataire id=9999 introuvable.` |
| Aucun rent actif | Désactiver les rents via API | `Avertissement : aucun loyer/charge actif … Abandon.` |
| Email désactivé | `sendNoticeOfLeaseRental=0` | Log `Envoi email : non`, pas de SMTP |
| Email manquant | `tenant.email` vide | `⚠ Pas d'email locataire — envoi ignoré.` |

---

## 2. Flux quittance de loyer — `validate_withdrawal.py` *(à créer)*

> **Statut : non implémenté.** Ce script est le pendant de `generate_receipt.py` pour la réception du virement. Il doit être créé selon le même pattern Docker (pymysql + requests + smtplib, `network_mode: host`).

### Ce que fera le script

```
Argument : --receipt-id <ID>  (ou --tenant-id + --month, ou matching automatique)
API: PATCH /rentReceipts/{id}  → paid=1
API: POST  /rentReceipts/{id}/pdf?doc_type=quittance → génère la QuittanceLoyer
     (distinct de l'AvisEcheance déjà sur disque : doc_type change le nom de fichier)
API: GET   /rentReceipts/{id}/pdf  → télécharge la QuittanceLoyer
Si sendLeaseRental==1 : SMTP → envoie en PJ à l'email du locataire
```

> **Point d'attention PDF :** un `AvisEcheance` a déjà été généré pour cet id. Le `POST /{id}/pdf` retourne 409 si un fichier du même nom existe. En forçant `?doc_type=quittance`, le nom change (`QuittanceLoyer`) → pas de conflit.

### Matching par `withdrawName`

Le script pourra prendre en entrée :
- `--receipt-id <ID>` — direct, si l'id est connu depuis le relevé bancaire
- `--tenant-id <ID> --month YYYY-MM` — recherche la quittance du mois via API
- `--withdraw-name "Dupont Jean" --amount 850.00 --month 2026-05` — matching automatique

Logique de matching automatique (via `GET /api/v1/tenants?name=Dupont` + `GET /api/v1/rentReceipts?tenantId=...&paid=0`) :
```
tenants[withdrawName == "Dupont Jean"]
  → rentReceipts[tenantId, paid=0, periodBegin in 2026-05, amount=850.00]
  → receipt_id
```

### Commandes (une fois créé)

```bash
cd /data/lolo/dev/rentalManagement/api/scripts
sudo docker-compose build

# Dry-run
sudo docker-compose run --rm validate-withdrawal \
  --receipt-id 47 \
  --dry-run

# Exécution directe
sudo docker-compose run --rm validate-withdrawal \
  --receipt-id 47

# Ou par matching
sudo docker-compose run --rm validate-withdrawal \
  --withdraw-name "Dupont Jean" \
  --amount 850.00 \
  --month 2026-05
```

### Ce qu'il faudra vérifier

**La quittance marquée payée :**
```bash
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/47 | jq '.paid'
# Attendu : 1
```

**Le PDF QuittanceLoyer sur disque :**
```bash
ls /data/lolo/dev/rentalManagement/api/files/*2026-05*
# Les deux fichiers doivent exister :
# → ...2026-05.AvisEcheance.pdf   (généré par generate_receipt.py)
# → ...2026-05.QuittanceLoyer.pdf (généré par validate_withdrawal.py)
```

**Télécharger et ouvrir le PDF :**
```bash
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/47/pdf \
  -o /tmp/quittance-test.pdf
xdg-open /tmp/quittance-test.pdf
# Le PDF doit afficher "QUITTANCE DE LOYER" et "déclare avoir reçu…"
```

**Via le frontend :**
- La quittance passe de `paid=❌` à `paid=✅` (coche verte)

---

## 3. Flux quittance de garantie

### Contexte

La quittance de garantie est créée lors de l'entrée du locataire (via `POST /tenants/full` ou manuellement). Son `rentReceiptsDetail` a `description = "Garantie"`. Le champ `tenant.warantyReceiptId` pointe vers cet enregistrement.

L'auto-détection dans `pdf_generator.py` regarde si un détail contient `"garantie"` (insensible à la casse) → génère une `QuittanceGarantie`.

### Vérifier la quittance de garantie

```bash
# Trouver le warantyReceiptId du locataire
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/tenants/<tenant_id> | jq '.warantyReceiptId'
# → ex: 3

# Vérifier la quittance et ses détails
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/3 | jq .
curl -s -b /tmp/rental.txt "http://localhost:8000/api/v1/rentReceiptsDetails?rentReceiptsId=3" | jq .
# Attendu : description="Garantie"
```

### Générer le PDF de garantie

La quittance de garantie n'est pas générée par `generate_receipt.py` (qui exclut les rents de type `Garantie`). Elle se génère manuellement :

```bash
# Générer le PDF (type auto-détecté → QuittanceGarantie)
curl -s -b /tmp/rental.txt -X POST http://localhost:8000/api/v1/rentReceipts/3/pdf | jq .
# → {"filename": "59000-LeonBlum-Appt1.2026-04.QuittanceGarantie.pdf", "path": "/files/..."}

# Forcer explicitement le type si nécessaire
curl -s -b /tmp/rental.txt -X POST \
  "http://localhost:8000/api/v1/rentReceipts/3/pdf?doc_type=garantie" | jq .

# Télécharger et ouvrir
curl -s -b /tmp/rental.txt http://localhost:8000/api/v1/rentReceipts/3/pdf \
  -o /tmp/garantie-test.pdf
xdg-open /tmp/garantie-test.pdf
```

Le PDF doit afficher :
- Titre : `"REÇU DU DÉPÔT DE GARANTIE"`
- Texte : "Reçu le … la somme de … au titre du dépôt de garantie…"
- Clause : "Le dépôt de garantie sera restitué dans les deux mois suivant la remise des clés…"

**Vérifier sur disque :**
```bash
ls /data/lolo/dev/rentalManagement/api/files/*.QuittanceGarantie.pdf
```

**Via le frontend :**
- `/tenants` → œil (quittances) → la quittance de garantie apparaît dans la liste → œil → PDF s'ouvre

### Envoi de la quittance de garantie

L'envoi sera géré par `validate_withdrawal.py` (même flag `sendLeaseRental`). Le type du PDF est auto-détecté d'après les détails du receipt.

---

## 4. Vérification de l'auto-détection du type de PDF

Logique dans `pdf_generator.generate_receipt_pdf()` :

| Condition sur le `rentReceipt` | Type généré | Titre dans le PDF |
|-------------------------------|-------------|-------------------|
| Un `rentReceiptsDetail.description` contient `"garantie"` (insensible) | `QuittanceGarantie` | "REÇU DU DÉPÔT DE GARANTIE" |
| `paid == 1` (et pas garantie) | `QuittanceLoyer` | "QUITTANCE DE LOYER" |
| `paid == 0` (et pas garantie) | `AvisEcheance` | "AVIS D'ÉCHÉANCE" |

Pour forcer un type : `POST /rentReceipts/{id}/pdf?doc_type=quittance|avis|garantie`

---

## 5. Résumé des flags locataire et documents envoyés

| Flag DB | Valeur | Document envoyé | Script | Déclencheur |
|---------|--------|-----------------|--------|-------------|
| `sendNoticeOfLeaseRental` | `1` | Avis d'échéance | `generate_receipt.py` | 25 du mois (pour le mois suivant) |
| `sendLeaseRental` | `1` | Quittance de loyer | `validate_withdrawal.py` *(à créer)* | Réception du virement |
| `sendLeaseRental` | `1` | Quittance de garantie | `validate_withdrawal.py` *(à créer)* | Versement de la caution |

Ces deux flags sont indépendants. Un locataire peut recevoir l'avis mais pas la quittance (ou l'inverse).

---

## 6. Checklist de test complète

### Avis d'échéance (`generate_receipt.py`)

- [ ] Dry-run affiche les bonnes informations (locataire, montant, période, flag email)
- [ ] Exécution crée `rentReceipts` + `rentReceiptsDetail` (vérifier via `GET /rentReceipts/{id}`)
- [ ] PDF `AvisEcheance` généré sur disque (`api/files/`)
- [ ] PDF ouvrable depuis le frontend (bouton œil → onglet)
- [ ] PDF téléchargeable via curl (`GET /rentReceipts/{id}/pdf`)
- [ ] Email reçu avec le PDF en PJ si `sendNoticeOfLeaseRental=1`
- [ ] Pas d'email si `sendNoticeOfLeaseRental=0`
- [ ] Doublon détecté et abandonné si quittance du mois déjà existante
- [ ] `--month` absent → mois suivant calculé automatiquement

### Quittance de loyer (`validate_withdrawal.py` — à créer)

- [ ] `rentReceipts.paid` passe à `1` (vérifier via `GET /rentReceipts/{id}`)
- [ ] PDF `QuittanceLoyer` généré sans conflit avec l'`AvisEcheance` existant
- [ ] PDF affiche "QUITTANCE DE LOYER" et "déclare avoir reçu…"
- [ ] Email reçu avec la quittance en PJ si `sendLeaseRental=1`
- [ ] Pas d'email si `sendLeaseRental=0`
- [ ] Matching automatique via `withdrawName` + montant + mois fonctionne

### Quittance de garantie

- [ ] PDF auto-détecté comme `QuittanceGarantie` (description contient "garantie")
- [ ] Titre correct : "REÇU DU DÉPÔT DE GARANTIE"
- [ ] Texte légal correct (reçu de… au titre du dépôt…)
- [ ] Clause restitution présente (deux mois après remise des clés)
- [ ] PDF sur disque dans `api/files/`
- [ ] Visible et téléchargeable depuis le frontend et via curl
