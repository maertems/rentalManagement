# Rental Management

Application web de gestion locative, pensée pour des propriétaires bailleurs qui gèrent un ou plusieurs biens en direct.

---

## Fonctionnalités

### Multi-propriétaire, multi-biens

Chaque propriétaire dispose de son propre compte : il ne voit que ses biens et ses locataires.  
Un compte administrateur permet de superviser l'ensemble sans restriction.

Un propriétaire peut gérer :
- plusieurs **biens** (maisons, immeubles…)
- plusieurs **logements** par bien (appartements, studios…)
- les **colocations** : un logement peut être découpé en chambres, chaque colocataire ayant sa propre quittance

### Gestion des locataires

Pour chaque locataire :
- Informations personnelles (nom, prénom, civilité, email, téléphone)
- Adresse de facturation distincte de l'adresse du logement si nécessaire
- Définition des lignes de loyer : **Loyer**, **Charges**, **Dépôt de garantie** — chacune avec son montant
- Choix du jour de prélèvement (utilisé comme date d'exigibilité sur l'avis d'échéance)
- Option d'envoi automatique de l'avis d'échéance par email

### Quittances et avis d'échéance

L'application génère trois types de documents PDF :

| Document | Quand |
|----------|-------|
| **Avis d'échéance** | Chaque mois, avant paiement — demande de paiement avec IBAN, ne vaut pas quittance |
| **Quittance de loyer** | Après validation du paiement — attestation légale de réception |
| **Reçu de dépôt de garantie** | À l'entrée du locataire — reçu du dépôt de garantie |

**Génération automatique** : un cron quotidien crée les avis d'échéance le jour du mois configuré par le propriétaire (défaut : le 25) et envoie l'email au locataire si l'option est activée.

**Validation du paiement** : quand un virement est reçu, le script `validate_withdrawal.sh` identifie le locataire correspondant, marque la quittance comme payée et génère le PDF quittance de loyer.

### Charges exceptionnelles

En dehors des loyers récurrents, il est possible d'ajouter des **frais ponctuels** pour un locataire et un mois donné (régularisation de charges, travaux refacturés, etc.) :
- Description libre et montant
- Possibilité de joindre un **justificatif** (facture, relevé…)
- Automatiquement inclus dans l'avis d'échéance du mois concerné, avec le justificatif en pièce jointe de l'email

### Interface

- Tableau de bord par propriétaire
- Vue locataires avec statut (actif / inactif), montant du loyer, date de dernière quittance
- Historique des quittances par locataire avec visualisation du PDF
- Gestion des frais et charges par locataire
- Page Paramètres : configuration du jour de génération, test d'envoi d'email simulant exactement le cron

---

## Stack

| Composant | Technologie |
|-----------|-------------|
| Backend API | Python 3.11 · FastAPI · SQLAlchemy 2.0 async |
| Base de données | MySQL 8.0 |
| Frontend | React 18 · TypeScript · Vite · TanStack Router/Query · Tailwind CSS |
| Auth | Cookies HTTP-only (JWT access + refresh) |
| PDF | fpdf2 · num2words |
| Cron | APScheduler (génération automatique des avis d'échéance) |

---

## Structure du projet

```
.
├── build/
│   ├── api/          # Sources Python (FastAPI)
│   ├── front/        # Sources React (Vite dev server)
│   └── mysql/        # Script d'initialisation MySQL
├── data/
│   ├── api/
│   │   ├── files/    # Fichiers persistants : PDF générés, params.yaml
│   │   └── .env      # Configuration API (secrets — non versionné, jamais pushé)
│   └── mysql/        # Données MySQL (bind-mount dans le container)
├── scripts/          # Scripts utilitaires (import, reset, génération quittance)
├── tests/            # Tests API (pytest-asyncio)
├── pytest.ini        # Configuration pytest
└── docs/             # Documentation technique par page
```

---

## Prérequis

- Docker installé
- Ports disponibles : `3306` (MySQL), `8000` (API), `5173` (Frontend)

---

## Démarrage

### 1. Créer le réseau Docker

```bash
docker network create rental
```

### 2. MySQL (optionnel — ignorer si vous utilisez un serveur MySQL existant)

```bash
docker run -d \
  --name rental_mysql \
  --network rental \
  --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=rental \
  -e MYSQL_USER=rental \
  -e MYSQL_PASSWORD=rental \
  -p 3306:3306 \
  -v "$(pwd)/data/mysql:/var/lib/mysql" \
  -v "$(pwd)/build/mysql/001_schema.sql:/docker-entrypoint-initdb.d/001_schema.sql:ro" \
  mysql:8.0
```

> Le schéma est initialisé automatiquement au premier démarrage.  
> Si vous utilisez un serveur MySQL externe, exécutez manuellement `build/mysql/001_schema.sql`.

### 3. Configurer l'API

Copier le fichier d'exemple et l'adapter :

```bash
cp build/api/.env.example data/api/.env
```

Variables à configurer dans `data/api/.env` :

```env
DATABASE_URL=mysql+asyncmy://rental:rental@rental_mysql:3306/rental
JWT_SECRET=changez-moi-en-production
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
JWT_REFRESH_EXPIRES_DAYS=7
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=motdepasseadmin
SMTP_HOST=smtp.example.com
SMTP_PORT=25
SMTP_USER=
SMTP_PASSWORD=
CORS_ORIGINS=["http://localhost:5173"]
```

> Si MySQL tourne sur un serveur externe, remplacer `rental_mysql` par l'IP ou le hostname.

### 4. Lancer l'API

```bash
docker build -t rental_api ./build/api

docker run -d \
  --name rental_api \
  --network rental \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file ./build/api/.env \
  -v "$(pwd)/data/api/files:/app/files" \
  rental_api
```

### 5. Lancer le Frontend

```bash
docker build -t rental_front ./build/front

docker run -d \
  --name rental_front \
  --restart unless-stopped \
  -p 5173:5173 \
  -v "$(pwd)/build/front:/app" \
  -v /app/node_modules \
  -e CHOKIDAR_USEPOLLING=true \
  rental_front
```

> Le frontend est accessible sur `http://localhost:5173` (ou l'IP LAN de la machine).  
> Il détecte automatiquement l'URL de l'API depuis `window.location.hostname` — aucune configuration nécessaire pour le LAN.

---

### 6. (Optionnel) Reverse proxy Apache — accès via nom de domaine

Pour exposer l'application sur un domaine (ex : `rental.example.com`) via HTTPS, configurer Apache en reverse proxy.

Modules requis :

```bash
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite
sudo systemctl reload apache2
```

VirtualHost (`/etc/apache2/sites-available/rental.example.com.conf`) :

```apache
<VirtualHost *:443>
    ServerName rental.example.com

    # SSL (adapter selon votre configuration Let's Encrypt / certbot)
    SSLEngine on
    SSLCertificateFile    /etc/letsencrypt/live/rental.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/rental.example.com/privkey.pem

    ProxyPreserveHost On

    # WebSocket HMR Vite
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} =websocket [NC]
    RewriteRule ^/(.*) ws://localhost:5173/$1 [P,L]

    # API — DOIT être déclaré AVANT le catch-all /
    # (sinon toutes les requêtes /api/ partent vers le frontend → erreurs JSON)
    ProxyPass        /api/  http://localhost:8000/api/
    ProxyPassReverse /api/  http://localhost:8000/api/
    ProxyPass        /docs  http://localhost:8000/docs
    ProxyPassReverse /docs  http://localhost:8000/docs
    ProxyPass        /openapi.json  http://localhost:8000/openapi.json
    ProxyPassReverse /openapi.json  http://localhost:8000/openapi.json

    # Frontend — catch-all en dernier
    ProxyPass        /  http://localhost:5173/
    ProxyPassReverse /  http://localhost:5173/
</VirtualHost>
```

> `localhost:8000` et `localhost:5173` fonctionnent car les containers publient leurs ports sur l'hôte via `-p`.  
> Le frontend doit être lancé avec `-e VITE_API_BASE_URL=""` (déjà dans `build/front/docker.sh`) pour que les appels API passent par le proxy Apache plutôt que directement sur le port 8000.

---

## Mise à jour

### API (changement de code Python)

Le code Python est intégré dans l'image Docker — un rebuild est nécessaire à chaque modification :

```bash
docker stop rental_api && docker rm rental_api
docker build -t rental_api ./build/api
docker run -d --name rental_api --network rental --restart unless-stopped \
  -p 8000:8000 --env-file ./build/api/.env \
  -v "$(pwd)/data/api/files:/app/files" rental_api
```

### Frontend (changement de code React/TypeScript)

Le frontend est monté en bind-mount — Vite HMR rechargera automatiquement.  
Aucun rebuild nécessaire pour le développement.

---

## Cron — Génération automatique des avis d'échéance

Le cron tourne **à l'intérieur du container API** (APScheduler), tous les jours à **12h24 heure Paris**.

Pour chaque propriétaire, il génère les avis d'échéance le jour configuré dans les paramètres  
(`Paramètres` dans l'interface, défaut : le 25 du mois).

Le processus est idempotent : si une quittance existe déjà pour le mois en cours, elle est ignorée.

---

## Scripts utilitaires

Les scripts se trouvent dans `scripts/` :

| Script | Usage |
|--------|-------|
| `validate_withdrawal.sh` | Valider un virement bancaire reçu (met à jour la quittance + génère le PDF) |
| `generate_receipt.py` | Générer manuellement la quittance d'un locataire |
| `reset_database.py` | Remettre à zéro la base de données |

```bash
# Valider un virement
API_URL=http://localhost:8000 API_EMAIL=admin@example.com API_PASSWORD=xxx \
  ./scripts/validate_withdrawal.sh "NOM DU LOCATAIRE" "800,00"
```

---

## Documentation Swagger

Accessible sur `http://localhost:8000/docs` quand l'API est démarrée.

---

## Développement — Tests API

```bash
# Depuis la racine du projet
TEST_DATABASE_URL=mysql+asyncmy://rental:rental@localhost:3306/rental_test \
  pytest -v
```

---

## Fichiers persistants

| Chemin hôte | Monté dans le container | Contenu |
|-------------|------------------------|---------|
| `data/api/files/` | `/app/files` | PDF des quittances, `params.yaml` |
| `data/api/.env` | `--env-file` | Configuration et secrets de l'API |
| `data/mysql/` | `/var/lib/mysql` | Données MySQL |

> Ces répertoires sont à **exclure du dépôt Git** (données sensibles / binaires).
