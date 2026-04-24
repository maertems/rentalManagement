# Rental Management — Migration PocketBase → MySQL + API FastAPI

> **Plan d'exécution détaillé**. Ce document est auto-suffisant : un modèle d'exécution doit pouvoir le dérouler de bout en bout sans contexte supplémentaire.

---

## 0. Contexte

Export PocketBase disponible dans `poketBase/pb_schema.json` (10 collections, domaine = gestion locative).

**Schéma métier :**

```
users (1) ──< owners (1) ──< places (1) ──< placesUnits (1) ──< placesUnitsRooms
                                                   │                    │
                                                   └──< tenants >───────┘
                                                         │
                                                   ┌─────┼─────────────┐
                                                   ▼     ▼             ▼
                                                 rents rentsFees   rentReceipts
                                                                       │
                                                                       ▼
                                                              rentReceiptsDetail

Relation spéciale : tenants.warantyReceiptId → rentReceipts.id
                    rentReceipts.tenantId    → tenants.id
```

**Objectif :** recréer le schéma en MySQL (sans FK), exposer une API FastAPI async avec Swagger et auth JWT.

---

## 1. Décisions actées

| # | Décision |
|---|---|
| 1 | **IDs** : `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` sur toutes les tables |
| 2 | **Aucune FOREIGN KEY** en base — intégrité gérée par l'API |
| 3 | **Auth JWT** (OAuth2PasswordBearer) |
| 4 | **SQLAlchemy 2.0 async** via `asyncmy` |
| 5 | **Pydantic v2** |
| 6 | **Schéma vide uniquement** (l'import de données viendra plus tard) |
| 7 | **camelCase** partout (colonnes SQL, JSON API, noms Python) + tout en **anglais** |

**Conséquence "pas de FK"** : le cycle `tenants ↔ rentReceipts` ne pose plus de problème. Aucun `ALTER TABLE` différé, ordre de création libre. Les relations sont uniquement logiques, vérifiées dans le code API.

**Règle de validation applicative** (centralisée dans la couche CRUD) :
- Avant `create`/`update` : si un champ `*Id` est fourni, vérifier que la ligne existe → sinon `422`.
- Avant `delete` : vérifier qu'aucun enregistrement ne la référence → sinon `409 Conflict`.

---

## 2. Schéma MySQL (`sql/001_schema.sql`)

### Conventions

- Moteur **InnoDB**, charset **utf8mb4 / utf8mb4_unicode_ci**
- PK : `id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT`
- Timestamps :
  - `createdAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)`
  - `updatedAt DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)`
- Colonnes en **camelCase** (backticks obligatoires si mot réservé)
- **Aucune** `FOREIGN KEY`, **aucun** `CONSTRAINT fk_*`
- **Index** sur les colonnes de relation + colonnes filtrables fréquentes
- Mot réservé traité : `order` → renommé **`sortOrder`**

### DDL complet

```sql
-- =========================================================================
-- Rental Management — MySQL schema (no FK, camelCase, BIGINT auto-increment)
-- =========================================================================

-- Users (auth)
CREATE TABLE `users` (
  `id`                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `email`                  VARCHAR(255) NOT NULL,
  `username`               VARCHAR(150),
  `passwordHash`           VARCHAR(255) NOT NULL,
  `tokenKey`               VARCHAR(255),
  `verified`               TINYINT(1) NOT NULL DEFAULT 0,
  `emailVisibility`        TINYINT(1) NOT NULL DEFAULT 0,
  `isAdmin`                TINYINT(1) NOT NULL DEFAULT 0,
  `isWithdraw`             TINYINT(1) NOT NULL DEFAULT 0,  -- accès uniquement à POST /withdraw/validate
  `name`                   VARCHAR(255),
  `avatar`                 VARCHAR(255),
  `ownerId`                BIGINT UNSIGNED NULL,           -- relation 1 owner → N users
  `lastResetSentAt`        DATETIME(3) NULL,
  `lastVerificationSentAt` DATETIME(3) NULL,
  `createdAt`              DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`              DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`),
  UNIQUE KEY `uq_users_username` (`username`),
  KEY `idx_users_ownerId` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Owners
CREATE TABLE `owners` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(255),
  `email`       VARCHAR(255),
  `address`     VARCHAR(500),
  `zipCode`     INT,
  `city`        VARCHAR(255),
  `phoneNumber` VARCHAR(50),
  `iban`        VARCHAR(64),
  `userId`      BIGINT UNSIGNED,
  `createdAt`   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_owners_userId` (`userId`),
  KEY `idx_owners_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places
CREATE TABLE `places` (
  `id`        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`      VARCHAR(255),
  `address`   VARCHAR(500),
  `zipCode`   INT,
  `city`      VARCHAR(255),
  `ownerId`   BIGINT UNSIGNED,
  `createdAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_places_ownerId` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places Units
CREATE TABLE `placesUnits` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`         VARCHAR(255),
  `level`        VARCHAR(50),
  `flatshare`    TINYINT(1) NOT NULL DEFAULT 0,
  `address`      VARCHAR(500),
  `zipCode`      INT,
  `city`         VARCHAR(255),
  `surfaceArea`  DECIMAL(10,2),
  `placeId`      BIGINT UNSIGNED,
  `friendlyName` VARCHAR(255),
  `createdAt`    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`    DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_placesUnits_placeId` (`placeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Places Units Rooms
CREATE TABLE `placesUnitsRooms` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`           VARCHAR(255),
  `surfaceArea`    DECIMAL(10,2),
  `placesUnitsId`  BIGINT UNSIGNED,
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_pur_placesUnitsId` (`placesUnitsId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tenants
CREATE TABLE `tenants` (
  `id`                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `genre`                   ENUM('Mlle','Mme','M','Societe'),
  `firstName`               VARCHAR(150),
  `name`                    VARCHAR(150),
  `email`                   VARCHAR(255),
  `phone`                   VARCHAR(50),
  `billingSameAsRental`     TINYINT(1) NOT NULL DEFAULT 1,
  `billingAddress`          VARCHAR(500),
  `billingZipCode`          INT,
  `billingCity`             VARCHAR(255),
  `billingPhone`            VARCHAR(50),
  `withdrawName`            VARCHAR(255),
  `withdrawDay`             TINYINT NOT NULL,
  `placeUnitId`             BIGINT UNSIGNED,
  `placeUnitRoomId`         BIGINT UNSIGNED,
  `sendNoticeOfLeaseRental` TINYINT(1) NOT NULL DEFAULT 0,
  `sendLeaseRental`         TINYINT(1) NOT NULL DEFAULT 0,
  `active`                  TINYINT(1) NOT NULL DEFAULT 1,
  `dateEntrance`            DATETIME(3),
  `dateExit`                DATETIME(3),
  `warantyReceiptId`        BIGINT UNSIGNED,
  `createdAt`               DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`               DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_tenants_placeUnitId` (`placeUnitId`),
  KEY `idx_tenants_active` (`active`),
  KEY `idx_tenants_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rent Receipts
CREATE TABLE `rentReceipts` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `placeUnitId`     BIGINT UNSIGNED,
  `placeUnitRoomId` BIGINT UNSIGNED,
  `tenantId`        BIGINT UNSIGNED,
  `amount`          DECIMAL(12,2),
  `periodBegin`     DATETIME(3),
  `periodEnd`       DATETIME(3),
  `paid`            TINYINT(1) NOT NULL DEFAULT 0,
  `pdfFilename`     VARCHAR(255) NULL DEFAULT NULL,  -- nom du fichier PDF généré (persisté au POST /pdf)
  `createdAt`       DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`       DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rr_tenantId` (`tenantId`),
  KEY `idx_rr_placeUnitId` (`placeUnitId`),
  KEY `idx_rr_paid` (`paid`),
  KEY `idx_rr_period` (`periodBegin`, `periodEnd`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rent Receipts Detail (note: `order` renamed to `sortOrder` — MySQL reserved word)
CREATE TABLE `rentReceiptsDetail` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `rentReceiptsId` BIGINT UNSIGNED,
  `sortOrder`      INT,
  `description`    VARCHAR(500),
  `price`          DECIMAL(12,2),
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rrd_rentReceiptsId` (`rentReceiptsId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rents (recurring charges)
CREATE TABLE `rents` (
  `id`             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tenantId`       BIGINT UNSIGNED,
  `type`           ENUM('Loyer','Charges','Garantie'),
  `price`          DECIMAL(12,2),
  `dateExpiration` DATETIME(3),
  `active`         TINYINT(1) NOT NULL DEFAULT 1,
  `createdAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rents_tenantId` (`tenantId`),
  KEY `idx_rents_active` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rents Fees (one-off fees)
CREATE TABLE `rentsFees` (
  `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tenantId`         BIGINT UNSIGNED,
  `applicationMonth` DATETIME(3),
  `description`      VARCHAR(500),
  `subDescription`   VARCHAR(500),
  `price`            DECIMAL(12,2),
  `createdAt`        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updatedAt`        DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (`id`),
  KEY `idx_rfees_tenantId` (`tenantId`),
  KEY `idx_rfees_applicationMonth` (`applicationMonth`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Mapping PocketBase → MySQL

| PocketBase type | MySQL type |
|---|---|
| text (court) | `VARCHAR(255)` ou `VARCHAR(500)` selon usage |
| email | `VARCHAR(255)` |
| number (noDecimal=true) | `INT` |
| number (noDecimal=false) | `DECIMAL(10,2)` ou `DECIMAL(12,2)` |
| bool | `TINYINT(1)` |
| date | `DATETIME(3)` |
| select (single) | `ENUM(...)` |
| relation (maxSelect=1) | `BIGINT UNSIGNED` (sans FK) |
| file | `VARCHAR(255)` (nom de fichier, stockage externe) |

---

## 3. Architecture API FastAPI

### 3.1 Stack figée

```
Python 3.11+
fastapi
uvicorn[standard]
sqlalchemy[asyncio]>=2.0
asyncmy                     # driver MySQL async
pydantic>=2
pydantic-settings
python-jose[cryptography]   # JWT
passlib[bcrypt]             # hashing mots de passe
python-multipart            # OAuth2PasswordRequestForm
pytest
pytest-asyncio
httpx                       # AsyncClient pour les tests
```

### 3.2 Arborescence du projet

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings (DATABASE_URL, JWT_SECRET, ...)
│   │   ├── database.py         # async engine, AsyncSessionLocal, Base, get_db
│   │   └── security.py         # hash_password, verify_password, JWT encode/decode
│   ├── models/                 # SQLAlchemy 2.0 ORM (sans FK, camelCase)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── owner.py
│   │   ├── place.py
│   │   ├── placesUnit.py
│   │   ├── placesUnitsRoom.py
│   │   ├── tenant.py
│   │   ├── rent.py
│   │   ├── rentsFee.py
│   │   ├── rentReceipt.py
│   │   └── rentReceiptsDetail.py
│   ├── schemas/                # Pydantic v2 (Base/Create/Update/Read/Filter)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── owner.py            # OwnerCreate.userId requis (int) + OwnerFullCreate/OwnerFullRead
│   │   ├── place.py
│   │   ├── placesUnit.py
│   │   ├── placesUnitsRoom.py
│   │   ├── tenant.py
│   │   ├── rent.py
│   │   ├── rentsFee.py
│   │   ├── rentReceipt.py
│   │   ├── rentReceiptsDetail.py
│   │   ├── auth.py             # Token, TokenPayload, LoginInput, RegisterInput
│   │   └── profile.py          # ProfileRead, ProfileUserUpdate, ProfileOwnerUpdate, ProfileUpdate
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py             # CRUDBase générique async — list() supporte in_filters
│   │   └── <un fichier par ressource>
│   ├── services/
│   │   ├── relations.py        # helpers d'intégrité (remplacent les FK)
│   │   ├── scope.py            # isolation owner-scope (get_owner_*_ids, assert_*_scope)
│   │   ├── pdf_context.py      # dataclass ReceiptContext + get_receipt_context(db, id)
│   │   ├── pdf_generator.py    # generate_quittance_loyer, generate_avis_echeance, generate_quittance_garantie
│   │   ├── params.py           # lecture/écriture /app/files/params.yaml (paramètres par propriétaire)
│   │   └── cron.py             # tâche cron quotidienne — génération automatique des avis d'échéance
│   └── api/
│       ├── __init__.py
│       ├── deps.py             # get_db, get_current_user, get_admin_user, get_owner_context, get_withdraw_user
│       └── v1/
│           ├── __init__.py
│           ├── router.py       # inclusion des 13 routers + auth + me
│           ├── auth.py
│           ├── me.py           # GET/PATCH /me/profile
│           ├── users.py
│           ├── owners.py       # + POST /owners/full (création atomique user+owner)
│           ├── places.py
│           ├── placesUnits.py
│           ├── placesUnitsRooms.py
│           ├── tenants.py
│           ├── rents.py
│           ├── rentsFees.py
│           ├── rentReceipts.py
│           ├── rentReceiptsDetails.py
│           ├── withdraw.py     # POST /withdraw/validate — accès isAdmin ou isWithdraw
│           └── params.py       # GET/PATCH /params/{owner_id} — paramètres propriétaire (fichier YAML)
├── sql/
│   └── 001_schema.sql
├── tests/
│   ├── conftest.py
│   └── test_<resource>.py  (un par ressource)
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 3.3 Modèles SQLAlchemy — règles strictes

- Style **SQLAlchemy 2.0** : `Mapped[...]`, `mapped_column(...)`.
- **Pas de `ForeignKey`**, **pas de `relationship()`**. Les relations sont uniquement logiques (champs `*Id` typés `BIGINT UNSIGNED`).
- Les éventuelles jointures se font manuellement dans les CRUD avec `select(...).join(Other, Model.otherId == Other.id)`.
- **Noms de classes** en `PascalCase` anglais : `User`, `Owner`, `Place`, `PlacesUnit`, `PlacesUnitsRoom`, `Tenant`, `Rent`, `RentsFee`, `RentReceipt`, `RentReceiptsDetail`.
- `__tablename__` = nom MySQL exact (`"placesUnits"`, `"rentReceiptsDetail"`, etc. — **camelCase**).
- Noms de colonnes Python = noms SQL (pas de conversion).
- `createdAt` / `updatedAt` gérés par DB (`server_default=func.now()`, `onupdate=func.now()`).

**Exemple modèle `Owner`** :

```python
# app/models/owner.py
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Owner(Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    zipCode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phoneNumber: Mapped[str | None] = mapped_column(String(50), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    userId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(fsp=3), server_default=func.current_timestamp(3))
    updatedAt: Mapped[datetime] = mapped_column(DateTime(fsp=3), server_default=func.current_timestamp(3), onupdate=func.current_timestamp(3))
```

### 3.4 Schémas Pydantic — règles

Pour chaque ressource, 5 classes : `XxxBase`, `XxxCreate`, `XxxUpdate`, `XxxRead`, `XxxFilter`.

**Exemple schémas `Owner`** :

```python
# app/schemas/owner.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class OwnerBase(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    zipCode: int | None = None
    city: str | None = None
    phoneNumber: str | None = None
    iban: str | None = None
    userId: int | None = None

class OwnerCreate(OwnerBase):
    userId: int  # requis (override OwnerBase) — un owner doit toujours avoir un user

class OwnerUpdate(OwnerBase):
    pass

# Création atomique user + owner en une seule transaction (POST /owners/full)
class OwnerFullCreate(BaseModel):
    user: UserCreate
    owner: OwnerBase  # userId sera défini côté serveur après création du user

class OwnerFullRead(BaseModel):
    user: UserRead
    owner: OwnerRead

class OwnerRead(OwnerBase):
    id: int
    createdAt: datetime
    updatedAt: datetime
    model_config = ConfigDict(from_attributes=True)

class OwnerFilter(BaseModel):
    userId: int | None = None
    name: str | None = None      # LIKE %name%
    email: str | None = None     # LIKE %email%
    city: str | None = None
    zipCode: int | None = None
    limit: int = Field(50, ge=1, le=500)
    offset: int = Field(0, ge=0)
    sort: str | None = None      # ex: "-createdAt,name"
```

**Critères de filtrage par ressource** (à implémenter dans le `list()` de chaque CRUD) :

| Table | Filtres |
|---|---|
| users | email, username, verified, name |
| owners | userId, name (LIKE), email (LIKE), city, zipCode |
| places | ownerId, name (LIKE), city, zipCode |
| placesUnits | placeId, flatshare, city, friendlyName (LIKE) |
| placesUnitsRooms | placesUnitsId, name (LIKE) |
| tenants | placeUnitId, active, genre, name (LIKE), email (LIKE), dateEntranceGte, dateEntranceLte, dateExitGte, dateExitLte |
| rents | tenantId, type, active |
| rentsFees | tenantId, applicationMonthGte, applicationMonthLte, description (LIKE) |
| rentReceipts | tenantId, placeUnitId, paid, periodBeginGte, periodBeginLte, periodEndGte, periodEndLte |
| rentReceiptsDetail | rentReceiptsId |

### 3.5 Endpoints — pattern par ressource

Pour chaque ressource, **exactement 5 routes** :

| Méthode | Route | Auth | Input | Output | Codes |
|---|---|---|---|---|---|
| POST | `/api/v1/<res>` | JWT | `<Res>Create` | `<Res>Read` | 201, 422 |
| GET | `/api/v1/<res>/{id}` | JWT | — | `<Res>Read` | 200, 404 |
| GET | `/api/v1/<res>` | JWT | query `<Res>Filter` | `list[<Res>Read]` + header `X-Total-Count` | 200 |
| PATCH | `/api/v1/<res>/{id}` | JWT | `<Res>Update` | `<Res>Read` | 200, 404, 422 |
| DELETE | `/api/v1/<res>/{id}` | JWT | — | — | 204, 404, 409 |

**12 routers métier** :
1. `/api/v1/users`
2. `/api/v1/owners` — + `POST /owners/full` (création atomique user+owner)
3. `/api/v1/places` — + `POST /places/full` (place + units + rooms en une transaction)
4. `/api/v1/placesUnits`
5. `/api/v1/placesUnitsRooms`
6. `/api/v1/tenants` — + `POST /tenants/full` (tenant + rents + caution)
7. `/api/v1/rents`
8. `/api/v1/rentsFees`
9. `/api/v1/rentReceipts` — + `POST /{id}/pdf` (génération) + `GET /{id}/pdf` (téléchargement)
10. `/api/v1/rentReceiptsDetails`
11. `/api/v1/withdraw` — `POST /withdraw/validate` (virement bancaire → validation paiement)
12. `/api/v1/params` — `GET/PATCH /params/{owner_id}` (paramètres par propriétaire, stockés dans `params.yaml`)

**Router profile** (`/api/v1/me`) :
- `GET  /api/v1/me/profile` — retourne `{ user: UserRead, owner: OwnerRead | null }` pour l'utilisateur courant
- `PATCH /api/v1/me/profile` — met à jour `name`/`username` du user et/ou les champs du owner lié

**Router d'auth** (`/api/v1/auth`) — endpoints publics :
- `POST /api/v1/auth/login` — `{email, password}` → httpOnly cookies `access_token` + `refresh_token`
- `POST /api/v1/auth/refresh` — renouvelle l'access token (lit le refresh cookie)
- `POST /api/v1/auth/logout` — efface les cookies
- `GET  /api/v1/auth/me` — retourne le user courant (lit le cookie access_token)

**Dashboard** :
- `GET /api/v1/dashboard/occupancy?month=YYYY-MM` — agrégation SQL : taux d'occupation + état des quittances par mois.  
  Champ `rentAmountEstimated: bool` : `false` si montant issu d'un `rentReceipt` du mois, `true` si fallback sur la somme `Loyer+Charges` des `rents` actifs.

**PDF quittances** (Phase G — ✅ done) :
- `POST /api/v1/rentReceipts/{id}/pdf` — génère le PDF et l'écrit dans `/app/files/` ; retourne `{filename, path}` (201). Retourne 409 si le fichier existe déjà (PDF immuable).  
  Paramètre optionnel `?doc_type=quittance|avis|garantie` pour forcer le type (auto-détection par défaut).  
  Après écriture, persiste `rentReceipts.pdfFilename = ctx.filename` en base.
- `GET  /api/v1/rentReceipts/{id}/pdf` — lit `obj.pdfFilename` en base, sert le fichier via `FileResponse` ; 404 si non généré ou fichier manquant sur disque.  
  ⚠️ Le GET n'auto-détecte plus le type — il utilise le nom exact stocké au POST, ce qui évite toute ambiguïté quand `?doc_type=` override a été utilisé.

**Withdraw validation** (Phase J — ✅ done) :
- `POST /api/v1/withdraw/validate` — reçoit `{name, rent}` ; cherche le locataire actif par `withdrawName` (insensible à la casse) ; trouve la quittance impayée la plus ancienne dont le montant correspond ; génère le PDF (`doc_type_override` forcé) ; marque `paid=True` ; met à jour `tenant.warantyReceiptId` si garantie ; envoie la quittance par email si `sendLeaseRental=1` en arrière-plan.  
  Accessible aux utilisateurs `isAdmin=1` **ou** `isWithdraw=1` (dep `get_withdraw_user`).  
  Retourne `{"status": 100, "log": [...]}`.

**Justificatifs rentsFees** (Phase H — ✅ done) :
- `POST /api/v1/rentsFees/{id}/document` — upload `UploadFile`, stocké dans `/app/files/fees/{id}.{ext}` (remplace l'existant).
- `GET  /api/v1/rentsFees/{id}/document` — téléchargement via `FileResponse`.
- `DELETE /api/v1/rentsFees/{id}/document` — supprime le fichier.
- `hasDocument: bool` dans `RentsFeeRead` — calculé au runtime via glob `fees/{id}.*`, non stocké en DB.
- `DELETE /api/v1/rentsFees/{id}` — supprime également le justificatif associé si présent.

**Paramètres propriétaire** (Phase K — ✅ done) :
- `GET  /api/v1/params/{owner_id}` — retourne les paramètres du propriétaire (défaut : `rentReceiptDay: 25`). Non-admin limité à son propre `owner_id`.
- `PATCH /api/v1/params/{owner_id}` — met à jour les paramètres. Non-admin limité à son propre `owner_id`.
- `GET  /api/v1/params` — liste tous les params (admin uniquement).
- Stockage : `/app/files/params.yaml` (volume Docker persisté, hors image). Format :
  ```yaml
  owners:
    "1":
      rentReceiptDay: 25
  ```
- Dépendances : `pyyaml>=6.0` (ajouté à `requirements.txt`).

**Endpoint libre** :
- `GET /health` — healthcheck (pas d'auth)

### 3.6 Validation d'intégrité applicative (remplace les FK)

Module `app/services/relations.py` :

```python
# app/services/relations.py
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def ensure_exists(
    db: AsyncSession,
    Model: type,
    id_: int | None,
    field_name: str,
) -> None:
    if id_ is None:
        return
    obj = await db.get(Model, id_)
    if obj is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{field_name}={id_} does not reference an existing row",
        )

async def ensure_no_children(
    db: AsyncSession,
    Model: type,
    filter_col,
    value: int,
    label: str,
) -> None:
    exists = await db.scalar(select(Model.id).where(filter_col == value).limit(1))
    if exists is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot delete: referenced by {label}",
        )
```

**Règles par table** (à appeler dans chaque CRUD) :

| Table | À valider en CREATE/UPDATE | À valider en DELETE |
|---|---|---|
| owners | `userId` → users | `places.ownerId` |
| places | `ownerId` → owners | `placesUnits.placeId` |
| placesUnits | `placeId` → places | `placesUnitsRooms.placesUnitsId`, `tenants.placeUnitId`, `rentReceipts.placeUnitId` |
| placesUnitsRooms | `placesUnitsId` → placesUnits | `tenants.placeUnitRoomId`, `rentReceipts.placeUnitRoomId` |
| tenants | `placeUnitId`, `placeUnitRoomId`, `warantyReceiptId` | `rents.tenantId`, `rentsFees.tenantId`, `rentReceipts.tenantId` |
| rents | `tenantId` | — |
| rentsFees | `tenantId` | — |
| rentReceipts | `placeUnitId`, `placeUnitRoomId`, `tenantId` | `rentReceiptsDetail.rentReceiptsId`, `tenants.warantyReceiptId` |
| rentReceiptsDetail | `rentReceiptsId` | — |
| users | — | `owners.userId` |

### 3.7 CRUD générique async (`crud/base.py`)

```python
# app/crud/base.py
from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)

class CRUDBase(Generic[ModelT, CreateT, UpdateT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    async def get(self, db: AsyncSession, id_: int) -> ModelT | None:
        return await db.get(self.model, id_)

    async def list(
        self,
        db: AsyncSession,
        *,
        filters: dict[str, Any] | None = None,
        in_filters: dict[str, list[int]] | None = None,  # WHERE col IN (ids) pour l'isolation owner
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[ModelT], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)
        # Apply filters (LIKE for str filters starting with pattern, eq for others)
        # Apply sort (comma-separated, `-` prefix = desc)
        if in_filters:
            for key, values in in_filters.items():
                col = getattr(self.model, key, None)
                if col is not None:
                    if not values:
                        return [], 0  # scope vide = aucun résultat (évite IN () vide)
                    stmt = stmt.where(col.in_(values))
                    count_stmt = count_stmt.where(col.in_(values))
        total = (await db.execute(count_stmt)).scalar_one()
        stmt = stmt.limit(limit).offset(offset)
        rows = (await db.execute(stmt)).scalars().all()
        return list(rows), total

    async def create(self, db: AsyncSession, obj_in: CreateT) -> ModelT:
        obj = self.model(**obj_in.model_dump(exclude_unset=True))
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self, db: AsyncSession, db_obj: ModelT, obj_in: UpdateT) -> ModelT:
        for k, v in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, k, v)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id_: int) -> None:
        obj = await self.get(db, id_)
        if obj is not None:
            await db.delete(obj)
            await db.commit()
```

Chaque CRUD concret hérite de `CRUDBase`, surcharge `list()` pour appliquer les filtres spécifiques, et ajoute des hooks `ensure_exists` / `ensure_no_children` avant les opérations concernées.

### 3.8 Authentification JWT (cookie-based)

L'authentification utilise des **httpOnly cookies** (pas de `Authorization` header). Deux cookies sont posés au login :
- `access_token` (durée courte, ex. 60 min)
- `refresh_token` (durée longue, ex. 7 jours)

`app/core/security.py` :

```python
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.core.config import settings

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str: ...
def verify_password(p: str, h: str) -> bool: ...
def create_access_token(sub: int) -> str: ...   # exp = JWT_EXPIRES_MIN
def create_refresh_token(sub: int) -> str: ...  # exp = JWT_REFRESH_EXPIRES_DAYS
def decode_token(token: str) -> dict: ...
```

`app/api/deps.py` :

```python
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.owner import Owner

async def get_db() -> AsyncSession: ...

async def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Lit le cookie httpOnly 'access_token'. Lève 401 si absent/invalide."""
    ...

async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Lève 403 si l'utilisateur n'est pas admin."""
    if not current_user.isAdmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return current_user

async def get_withdraw_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Lève 403 si l'utilisateur n'est ni admin ni withdraw."""
    if not current_user.isAdmin and not current_user.isWithdraw:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Withdraw privileges required")
    return current_user

async def get_owner_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Owner | None:
    """
    - Admin → retourne None (vue globale, pas de filtre)
    - Non-admin avec owner lié → retourne l'Owner
    - Non-admin sans owner → lève 403 (compte orphelin)
    """
    if current_user.isAdmin:
        return None
    owner = (await db.execute(
        select(Owner).where(Owner.userId == current_user.id)
    )).scalar_one_or_none()
    if owner is None:
        raise HTTPException(403, "No owner profile linked to this account. Contact an administrator.")
    return owner
```

**Tous les routers métier** déclarent `dependencies=[Depends(get_current_user)]` au niveau de leur `APIRouter`. Les mutations admin (POST/DELETE users, POST owners, DELETE owners) utilisent `Depends(get_admin_user)`. Le router `withdraw` utilise `Depends(get_withdraw_user)` (isAdmin **ou** isWithdraw). Seuls `auth.py` et `GET /health` sont publics.

### 3.12 Isolation owner-scope (`services/scope.py`)

Chaque propriétaire (non-admin) ne voit et ne modifie que ses propres données. L'isolation est implémentée via `get_owner_context` (voir §3.8) + helpers dans `services/scope.py`.

```python
# app/services/scope.py

async def get_owner_place_ids(db, owner_id: int) -> list[int]:
    """Retourne la liste des place.id appartenant à cet owner."""

async def get_owner_unit_ids(db, owner_id: int) -> list[int]:
    """Retourne la liste des placesUnit.id des places de cet owner."""

async def get_owner_tenant_ids(db, owner_id: int) -> list[int]:
    """Retourne la liste des tenant.id des units de cet owner."""

async def assert_place_scope(db, owner_ctx: Owner | None, place_id: int) -> None:
    """Lève 403 si le place n'appartient pas à owner_ctx (no-op si admin)."""

async def assert_unit_scope(db, owner_ctx: Owner | None, unit_id: int) -> None:
    """Lève 403 si l'unit ne fait pas partie des places de owner_ctx."""

async def assert_tenant_scope(db, owner_ctx: Owner | None, tenant_id: int) -> None:
    """Lève 403 si le tenant n'est pas dans le périmètre de owner_ctx."""
```

**Règles de filtrage des LIST** :

| Endpoint | Stratégie |
|----------|-----------|
| `GET /places` | `f.ownerId = owner_ctx.id` (filtre direct) |
| `GET /placesUnits` | `in_filters={"placeId": place_ids}` |
| `GET /placesUnitsRooms` | `in_filters={"placesUnitsId": unit_ids}` |
| `GET /tenants` | `in_filters={"placeUnitId": unit_ids}` |
| `GET /rents` | `in_filters={"tenantId": tenant_ids}` |
| `GET /rentsFees` | `in_filters={"tenantId": tenant_ids}` |
| `GET /rentReceipts` | `in_filters={"tenantId": tenant_ids}` |
| `GET /owners` | non-admin → filtre `userId == current_user.id` |
| `GET /users` | non-admin → retourne `[current_user]` sans requête |
| `GET /dashboard/occupancy` | `places_stmt.where(Place.ownerId == owner_ctx.id)` |

**Règles de protection des mutations** :

| Endpoint | Vérification |
|----------|-------------|
| `POST /places` | `payload.ownerId = owner_ctx.id` (auto-injecté si non-admin) |
| `PATCH/DELETE /places/{id}` | `assert_place_scope` |
| `POST/PATCH/DELETE /placesUnits/{id}` | `assert_place_scope` via `unit.placeId` |
| `POST/PATCH/DELETE /placesUnitsRooms/{id}` | `assert_unit_scope` |
| `POST /tenants/full` | `assert_unit_scope` |
| `PATCH/DELETE /tenants/{id}` | `assert_tenant_scope` |
| `POST/PATCH/DELETE /rents/{id}` | `assert_tenant_scope` via `rent.tenantId` |
| `POST/PATCH/DELETE /rentsFees/{id}` | idem |
| `POST/PATCH/DELETE /rentReceipts/{id}` | idem |

### 3.9 Swagger

`app/main.py` :

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="Rental Management API",
    version="1.0.0",
    description="Rental management backend (MySQL + FastAPI).",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "Authentication & registration"},
        {"name": "Users"},
        {"name": "Owners"},
        {"name": "Places"},
        {"name": "PlacesUnits"},
        {"name": "PlacesUnitsRooms"},
        {"name": "Tenants"},
        {"name": "Rents"},
        {"name": "RentsFees"},
        {"name": "RentReceipts"},
        {"name": "RentReceiptsDetails"},
        {"name": "Withdraw"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 3.10 Configuration (`.env.example`)

```
DATABASE_URL=mysql+asyncmy://rental:rental@mysql:3306/rental
JWT_SECRET=change-me-in-production-please
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
JWT_REFRESH_EXPIRES_DAYS=7
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 3.11 Gestion des exceptions

Dans `app/main.py`, ajouter des handlers :
- `RequestValidationError` → 422 (défaut FastAPI, on peut le customiser pour uniformiser le format)
- `IntegrityError` (SQLAlchemy) → 409 Conflict
- `NoResultFound` → 404 Not Found

---

## 4. Plan d'exécution (étapes numérotées)

### Phase A — Bootstrap projet
1. Créer l'arborescence `api/app/{core,models,schemas,crud,services,api/v1}`, `api/sql/`, `api/tests/`
2. Écrire `api/requirements.txt` avec les dépendances de §3.1
3. Écrire `api/.env.example` (§3.10)
4. Écrire `api/Dockerfile` (Python 3.11-slim, install requirements, `uvicorn app.main:app --host 0.0.0.0 --port 8000`)
5. Écrire `api/docker-compose.yml` : service `mysql` (image mysql:8.0, volume persistant, init script monté depuis `sql/`) + service `api` (build local, depends_on mysql, port 8000, env_file `.env`)
6. Écrire `api/sql/001_schema.sql` (contenu complet de §2 — DDL)
7. Écrire `api/README.md` avec instructions de démarrage

### Phase B — Core
8. `app/core/config.py` : classe `Settings` héritant de `BaseSettings` (pydantic-settings), lit `.env`
9. `app/core/database.py` : `create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)`, `AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)`, `class Base(DeclarativeBase): pass`
10. `app/core/security.py` : fonctions bcrypt + JWT (§3.8)

### Phase C — Modèles SQLAlchemy (10 fichiers)
Chaque fichier suit le patron de `Owner` (§3.3). Ordre libre (pas de FK).

11. `app/models/user.py` — champs : id, email (unique), username (unique), passwordHash, tokenKey, verified, emailVisibility, name, avatar, lastResetSentAt, lastVerificationSentAt, createdAt, updatedAt
12. `app/models/owner.py` — id, name, email, address, zipCode, city, phoneNumber, iban, userId, createdAt, updatedAt
13. `app/models/place.py` — id, name, address, zipCode, city, ownerId, createdAt, updatedAt
14. `app/models/placesUnit.py` — id, name, level, flatshare, address, zipCode, city, surfaceArea, placeId, friendlyName, createdAt, updatedAt — `__tablename__ = "placesUnits"`
15. `app/models/placesUnitsRoom.py` — id, name, surfaceArea, placesUnitsId, createdAt, updatedAt — `__tablename__ = "placesUnitsRooms"`
16. `app/models/tenant.py` — tous les champs tenants de §2, `genre` en `Enum('Mlle','Mme','M','Societe')`
17. `app/models/rent.py` — id, tenantId, type (Enum), price, dateExpiration, active, createdAt, updatedAt
18. `app/models/rentsFee.py` — id, tenantId, applicationMonth, description, subDescription, price, createdAt, updatedAt — `__tablename__ = "rentsFees"`
19. `app/models/rentReceipt.py` — id, placeUnitId, placeUnitRoomId, tenantId, amount, periodBegin, periodEnd, paid, createdAt, updatedAt — `__tablename__ = "rentReceipts"`
20. `app/models/rentReceiptsDetail.py` — id, rentReceiptsId, sortOrder, description, price, createdAt, updatedAt — `__tablename__ = "rentReceiptsDetail"`

Créer aussi `app/models/__init__.py` qui importe toutes les classes.

### Phase D — Schémas Pydantic (11 fichiers)
Chaque fichier suit le patron `Owner` (§3.4). Modèles en camelCase, `from_attributes=True`.

21. `app/schemas/user.py` (UserBase exclut `passwordHash`, `tokenKey` ; ajoute `UserCreate` avec champ `password: str`)
22. `app/schemas/owner.py`
23. `app/schemas/place.py`
24. `app/schemas/placesUnit.py`
25. `app/schemas/placesUnitsRoom.py`
26. `app/schemas/tenant.py`
27. `app/schemas/rent.py`
28. `app/schemas/rentsFee.py`
29. `app/schemas/rentReceipt.py`
30. `app/schemas/rentReceiptsDetail.py`
31. `app/schemas/auth.py` : `Token` `{accessToken, tokenType="bearer", expiresIn, refreshToken}`, `TokenPayload`, `RefreshInput {refreshToken: str}`

### Phase E — Services d'intégrité et isolation
32. `app/services/relations.py` (code de §3.6) — `ensure_exists`, `ensure_no_children`
32b. `app/services/scope.py` (code de §3.12) — `get_owner_*_ids`, `assert_*_scope`

### Phase F — CRUD (11 fichiers)
33. `app/crud/base.py` : `CRUDBase` générique (code §3.7)
34. `app/crud/user.py` : surcharge `create()` pour hasher le mot de passe, ajoute `get_by_email()`, `get_by_username()`
35. `app/crud/owner.py` : hooks `ensure_exists(User, obj_in.userId, "userId")` en create/update ; `ensure_no_children(Place, Place.ownerId, id_, "places")` en delete
36. `app/crud/place.py` : ensure_exists owners ; ensure_no_children placesUnits
37. `app/crud/placesUnit.py` : ensure_exists places ; ensure_no_children placesUnitsRooms + tenants + rentReceipts
38. `app/crud/placesUnitsRoom.py` : ensure_exists placesUnits ; ensure_no_children tenants + rentReceipts
39. `app/crud/tenant.py` : ensure_exists placesUnits, placesUnitsRooms, rentReceipts ; ensure_no_children rents + rentsFees + rentReceipts
40. `app/crud/rent.py` : ensure_exists tenants
41. `app/crud/rentsFee.py` : ensure_exists tenants
42. `app/crud/rentReceipt.py` : ensure_exists placesUnits, placesUnitsRooms, tenants ; ensure_no_children rentReceiptsDetail + tenants (warantyReceiptId)
43. `app/crud/rentReceiptsDetail.py` : ensure_exists rentReceipts

### Phase G — Routers
44. `app/api/deps.py` : `get_db`, `get_current_user` (cookie), `get_admin_user`, `get_owner_context` (code §3.8)
45. `app/api/v1/auth.py` : endpoints login (httpOnly cookie), refresh, logout, me
46. `app/api/v1/me.py` : `GET /me/profile` + `PATCH /me/profile` (schémas ProfileRead/ProfileUpdate §3.4)
47. `app/api/v1/users.py` — CRUD, non-admin ne voit que lui-même (§3.12)
48. `app/api/v1/owners.py` — CRUD + `POST /owners/full` (atomique user+owner), isolation scope
49. `app/api/v1/places.py` — CRUD + `POST /places/full`, isolation scope
50. `app/api/v1/placesUnits.py` — isolation scope
51. `app/api/v1/placesUnitsRooms.py` — isolation scope
52. `app/api/v1/tenants.py` — CRUD + `POST /tenants/full`, isolation scope
53. `app/api/v1/rents.py` — isolation scope
54. `app/api/v1/rentsFees.py` — isolation scope
55. `app/api/v1/rentReceipts.py` — isolation scope
56. `app/api/v1/rentReceiptsDetails.py`
57. `app/api/v1/dashboard.py` : `GET /dashboard/occupancy` — filtré par owner_ctx
58. `app/api/v1/router.py` : `api_router = APIRouter()` + `api_router.include_router(...)` pour auth + me + 10 métier + dashboard
59. `app/main.py` (code §3.9) + handlers d'exceptions (§3.11) + bootstrap admin au démarrage

### Phase H — Tests
58. `tests/conftest.py` : fixtures `client` (non-authed) + `authedClient` (admin cookie) + truncate entre tests
59. `tests/test_auth.py` : login → me → refresh → logout
60. `tests/test_owners.py` (9 tests) :
    - create → get → list (avec filtre) → patch → delete
    - `test_create_owner_requires_user_id` (422 sans userId)
    - `test_create_owner_userId_unique` (409 si userId déjà utilisé)
    - `test_create_owner_full` (POST /owners/full — atomique)
61. `tests/test_places.py` — inclut test POST /places/full
62. `tests/test_placesUnits.py`
63. `tests/test_placesUnitsRooms.py`
64. `tests/test_tenants.py` — inclut test POST /tenants/full
65. `tests/test_rents.py`
66. `tests/test_rentsFees.py`
67. `tests/test_rentReceipts.py`
68. `tests/test_rentReceiptsDetails.py`
69. `tests/test_integrity.py` :
    - DELETE d'un place avec placesUnits → 409
    - Création d'un tenant avec `placeUnitId` inexistant → 422
    - Création d'un rentReceipt avec `tenantId` inexistant → 422
    - `GET /owners` sans auth → 401
    
> **27/27 tests passent** (à jour au 2026-04-15)

### Phase H-bis — Génération PDF des quittances — ✅ Done

**Dépendances ajoutées** (`requirements.txt`) :
- `fpdf2>=2.7.9` — portage Python de FPDF, UTF-8 natif, pas de dépendance système
- `num2words>=0.5.14` — conversion nombre → lettres en français

**Fichiers créés** :

| Fichier | Rôle |
|---------|------|
| `app/static/signature.png` | Image de signature (copiée depuis l'ancienne version PHP) |
| `app/services/pdf_context.py` | Dataclass `ReceiptContext` + `get_receipt_context(db, receipt_id, doc_type_override)` |
| `app/services/pdf_generator.py` | Trois générateurs PDF + `generate_receipt_pdf()` auto-detect |

**`pdf_context.py`** charge en une passe : `RentReceipt` → `RentReceiptsDetail` → `Tenant` → `PlacesUnit` → `Place` → `Owner`.  
Détecte `is_garantie` si un détail contient "garantie" (insensible casse).  
Calcule la date d'exigibilité : `withdrawDay` du mois de `periodBegin`, clampé au dernier jour du mois (`calendar.monthrange`), fallback jour 6 si `withdrawDay` null.  
Construit le nom de fichier : `{zipCode}-{placeName}-{unitName}.{YYYY-MM}.{docType}.pdf` (espaces supprimés).

**`pdf_generator.py`** — trois fonctions retournant `bytes` :
- `generate_quittance_loyer(ctx)` — texte légal + tableau détails + signature + clause légale
- `generate_avis_echeance(ctx)` — en-tête owner|tenant, tableau, date exigible, IBAN
- `generate_quittance_garantie(ctx)` — reçu dépôt + clause restitution + signature
- `generate_receipt_pdf(ctx, doc_type_override)` — auto-détect : garantie → quittance garantie ; payé → quittance loyer ; non payé → avis échéance

**Montant en lettres** : `_amount_to_words_fr()` — centimes omis si `.00` (ex : "huit cents euros", pas "huit cents euros et zéro centime").

**Endpoints ajoutés sur `/api/v1/rentReceipts`** :
- `POST /{id}/pdf` — génère et écrit dans `FILES_DIR` (`/app/files/`) ; 409 si déjà généré ; retourne `{filename, path}` (201)
- `GET  /{id}/pdf` — sert via `FileResponse` ; 404 si non généré

**Infrastructure** :
- Répertoire `api/files/` créé, monté en volume Docker `./files:/app/files`

---

### Phase H — Justificatifs rentsFees — ✅ Done

Gestion des documents justificatifs associés aux frais (`rentsFees`). Les fichiers sont stockés dans `/app/files/fees/` (volume Docker partagé avec les PDF quittances), identifiés par `{id}.{ext}`.

| Fichier | Modification |
|---------|-------------|
| `app/schemas/rentsFee.py` | `hasDocument: bool = False` dans `RentsFeeRead` |
| `app/crud/rentsFee.py` | Param `scope_tenant_ids` dans `list_filtered` + filtre IN |
| `app/api/v1/rentsFees.py` | `FEES_DIR`, `_doc_path()`, `_with_doc()`, isolation `assert_tenant_scope` sur tous les endpoints CRUD + 3 endpoints document (POST/GET/DELETE `/{id}/document`) |

**Règles** :
- `hasDocument` calculé au runtime via `glob(f"{id}.*")` dans `/app/files/fees/` — non stocké en DB.
- L'upload remplace automatiquement le justificatif existant (un seul par frais).
- La suppression du frais (`DELETE /{id}`) supprime aussi le justificatif associé.

---

### Phase I — Validation manuelle
70. `docker compose up --build` depuis `api/`
71. Ouvrir `http://localhost:8000/docs`
72. Scénario de bout en bout via Swagger :
    1. `POST /api/v1/auth/register` avec `email`, `password`, `username`
    2. `POST /api/v1/auth/login` (form) → copier le `accessToken`
    3. Bouton "Authorize" → coller le token
    4. `POST /api/v1/owners` → récupérer `id`
    5. `POST /api/v1/places` avec `ownerId`
    6. `POST /api/v1/placesUnits` avec `placeId`
    7. `POST /api/v1/tenants` avec `placeUnitId`, `withdrawDay=5`
    8. `POST /api/v1/rents` avec `tenantId`, `type="Loyer"`, `price=800`
    9. `POST /api/v1/rentReceipts` avec `tenantId`, `placeUnitId`
    10. `POST /api/v1/rentReceiptsDetails` avec `rentReceiptsId`
    11. `GET /api/v1/tenants?active=true&placeUnitId=...` → vérifier filtre

### Phase I-bis — Scripts utilitaires (`api/scripts/`) — ✅ Done

Les scripts tournent dans leur propre image Docker (`api/scripts/Dockerfile`), avec `network_mode: host` pour accéder à MySQL exposé sur `127.0.0.1:3306`. Ils partagent le même `docker-compose.yml` de scripts.

| Script | Rôle | Status |
|--------|------|--------|
| `import_pocketbase.py` | Import initial depuis les dumps JSON PocketBase | ✅ |
| `reset_database.py` | TRUNCATE toutes les tables + reset AUTO_INCREMENT | ✅ |
| `generate_receipt.py` | Génère la quittance mensuelle d'un locataire | ✅ |
| `validate_withdrawal.sh` | Script bash appelant `POST /withdraw/validate` (2 curl : login + validate) | ✅ |

**`generate_receipt.py`** — flow complet :

1. Lit les rents actifs du locataire (hors `Garantie`) → calcule le total
2. Vérifie l'absence de doublon (même locataire, même mois)
3. Insère `rentReceipt` + `rentReceiptsDetail` directement en DB (pymysql)
4. Appelle `POST /api/v1/rentReceipts/{id}/pdf` pour générer le PDF (auth admin via `.env`)
5. Télécharge le PDF via `GET /api/v1/rentReceipts/{id}/pdf`
6. Si `tenant.sendNoticeOfLeaseRental == 1` : envoie le PDF en pièce jointe par email
   - SMTP : `mail.notrebicoque.com:25`, sans auth
   - From/CC : email du propriétaire (`owner.email`)
   - To : email du locataire (`tenant.email`)
   - Sujet : `"Avis d'échéance - {unit.friendlyName}"`

**Règle de calendrier** : lancé le **25 du mois courant** pour générer la quittance du **mois suivant**.
`--month` est optionnel — si absent, le script calcule automatiquement `mois_courant + 1`.

**Deux flags d'envoi email** sur le locataire :
| Flag | Document envoyé | Quand |
|------|-----------------|-------|
| `sendNoticeOfLeaseRental` | Avis d'échéance | `generate_receipt.py` (25 du mois) |
| `sendLeaseRental` | Quittance de loyer | `POST /withdraw/validate` (virement reçu) |

**`validate_withdrawal.sh`** — 2 paramètres positionnels : `NAME` (nom du virement) et `RENT` (montant, ex: "800.00") :
1. `POST /api/v1/auth/login` → cookie temporaire dans fichier mktemp
2. `POST /api/v1/withdraw/validate` avec `{"name": "$NAME", "rent": "$RENT"}` → affiche la réponse JSON

Variables d'environnement : `API_URL` (défaut `http://localhost:8000`), `API_EMAIL`, `API_PASSWORD`.

```bash
# Lancé le 25 → génère automatiquement le mois suivant
sudo docker-compose run --rm generate-receipt --tenant-id 42

# Forcer un mois spécifique
sudo docker-compose run --rm generate-receipt --tenant-id 42 --month 2026-06

# Tester sans écrire ni envoyer
sudo docker-compose run --rm generate-receipt --tenant-id 42 --dry-run
```

---

### Phase K — Paramètres propriétaire — ✅ Done

**Objectif** : permettre à chaque propriétaire de configurer le jour du mois auquel ses avis d'échéance sont générés.

**Fichiers créés** :

| Fichier | Rôle |
|---------|------|
| `app/services/params.py` | Lecture/écriture de `/app/files/params.yaml` — `get_owner_params(id)`, `set_owner_params(id, params)`, `get_all_params()` |
| `app/api/v1/params.py` | `GET/PATCH /params/{owner_id}` + `GET /params` (admin) — schéma `OwnerParams { rentReceiptDay: int|None }` |

Stockage : `/app/files/params.yaml` (volume Docker persisté). Format :
```yaml
owners:
  "1":
    rentReceiptDay: 25
```
Défaut : `rentReceiptDay = 25`. Un non-admin ne peut consulter/modifier que ses propres params. Dépendance ajoutée : `pyyaml>=6.0`.

---

### Phase J-bis — Endpoint withdraw validation — ✅ Done

**Rôle `isWithdraw`** :
- Colonne `users.isWithdraw TINYINT(1) NOT NULL DEFAULT 0`
- Modèle `app/models/user.py` + schéma `app/schemas/user.py` mis à jour
- Dépendance `get_withdraw_user` dans `app/api/deps.py` : autorise `isAdmin=1` **ou** `isWithdraw=1`, sinon 403
- Frontend : page `/users` — colonne "Withdraw" (icône Landmark) + checkbox "Accès virement" dans `UserFormDialog`

**`app/api/v1/withdraw.py`** — algorithme (réplique fidèle de `withdrawValidation.php`) :
1. Nettoyage du montant reçu (remplacer `,` par `.`, supprimer espaces et `+`)
2. Chercher le locataire actif (`active=1`) par `withdrawName` (insensible à la casse via `func.lower()`)
3. Si non trouvé → `{"status": 200, "log": [..., "Locataire introuvable"]}`
4. Parmi les `rentReceipts` du locataire avec `amount == montant` et `paid=0`, prendre le plus ancien (`ORDER BY periodBegin ASC`)
5. Si aucun → `{"status": 200, "log": [..., "Aucune quittance impayée correspondante"]}`
6. Charger les `rentReceiptsDetail` — `is_garantie` = `any(d.description == "Garantie" for d in details)` (match **exact**, sensible à la casse)
7. `doc_type_override` = `"garantie"` si garantie, sinon `"quittance"` (forcé car `paid=False` au moment de la génération)
8. Générer le PDF via `POST /api/v1/rentReceipts/{id}/pdf?doc_type={override}` (appel HTTP interne)
9. Marquer `receipt.paid = True` ; si garantie → `tenant.warantyReceiptId = receipt.id`
10. `await db.commit()`
11. Si `tenant.sendLeaseRental == 1` : envoyer la quittance par email via `BackgroundTask`

Retourne `{"status": 100, "log": [...messages...]}`.

**Script d'appel** : `api/scripts/validate_withdrawal.sh` (bash, 2 params : nom et montant, 2 curl).

### Phase L — Cron génération automatique des avis d'échéance — ✅ Done

**Objectif** : générer automatiquement les avis d'échéance chaque mois au jour configuré par le propriétaire, sans intervention manuelle.

**Dépendances ajoutées** (`requirements.txt`) :
- `apscheduler>=3.10.0` — scheduler asynchrone intégré au process FastAPI
- `pytz>=2024.1` — gestion des fuseaux horaires (Europe/Paris — CET/CEST)

**Fichiers modifiés/créés** :

| Fichier | Modification |
|---------|-------------|
| `app/services/cron.py` | **Créé** — tâche `run_daily_receipt_generation()` |
| `app/main.py` | `AsyncIOScheduler` démarré/arrêté dans le `lifespan` FastAPI |
| `requirements.txt` | `apscheduler>=3.10.0` + `pytz>=2024.1` |

**Algorithme de `run_daily_receipt_generation()`** (lancé chaque jour à **12h24 Europe/Paris**) :

1. Charge tous les propriétaires en base
2. Pour chaque propriétaire :
   - Lit `rentReceiptDay` dans `params.yaml` (défaut 25), clampé au dernier jour du mois (ex: 31 → 28 en février)
   - Si `aujourd'hui.jour != jour_clampé` → passe au suivant
3. Pour chaque propriétaire concerné → tous ses biens → tous ses logements → tous ses locataires actifs :
   - Vérifie qu'aucune quittance n'existe déjà pour ce mois (`periodBegin >= 1er du mois`) — **idempotent**
   - Récupère les loyers actifs (hors `Garantie`)
   - Crée `RentReceipt` (amount = somme des loyers, `paid=0`, période = mois courant)
   - Crée `RentReceiptsDetail` (Loyer → Charges → reste, par `sortOrder`)
   - Génère le PDF `AvisEcheance` → écrit dans `/app/files/` → sauvegarde `pdfFilename` en DB

**Tolérance au redémarrage** : `misfire_grace_time=3600` — si le container redémarre jusqu'à 1h après 12h24, le job s'exécute quand même.

**Prise en compte du changement de jour** : `params.yaml` est relu à chaque exécution du cron — un changement via l'interface `/settings` est effectif dès le lendemain.

---

### Phase J — Finalisation
73. Passe `ruff check .` et `ruff format .`
74. `pytest -v` → tous les tests passent
75. Compléter le `README.md` avec : prérequis, démarrage (`docker compose up`), URL Swagger, commandes de test, exemples curl

---

## 5. Checklist de livrables finaux

- [x] `api/sql/001_schema.sql` : 10 tables, camelCase, BIGINT AUTO_INCREMENT, zéro FK
- [x] 10 modèles SQLAlchemy async, sans ForeignKey, sans relationship
- [x] 12 fichiers de schémas Pydantic (10 ressources + auth + profile)
- [x] 11 modules CRUD async avec validations d'intégrité applicatives
- [x] Routers FastAPI :
  - 55 endpoints CRUD de base (10 × 5)
  - Endpoints bonus : `POST /owners/full`, `POST /places/full`, `POST /tenants/full`, `GET /tenants/{id}/receipts`
  - `GET /dashboard/occupancy` + champ `rentAmountEstimated`
  - `GET + PATCH /me/profile`
  - `POST/GET/POST /auth/login|refresh|logout|me`
  - `POST /rentReceipts/{id}/pdf` (génération) + `GET /rentReceipts/{id}/pdf` (téléchargement)
  - `POST/GET/DELETE /rentsFees/{id}/document` (justificatif — stockage filesystem `/app/files/fees/`)
- [x] Authentification **httpOnly cookie** (access + refresh token)
- [x] `get_admin_user` dep — protection des mutations admin
- [x] `get_withdraw_user` dep — protection de `POST /withdraw/validate` (isAdmin ou isWithdraw)
- [x] `users.isWithdraw` colonne + modèle + schéma + frontend (colonne + checkbox UserFormDialog)
- [x] `get_owner_context` dep + `services/scope.py` — isolation complète par owner
- [x] Bootstrap admin au démarrage (`ADMIN_EMAIL` / `ADMIN_PASSWORD` dans `.env`)
- [x] Suite de tests pytest-asyncio : **27/27 tests passent**
- [x] `docker-compose.yml` démarrant MySQL + API en une commande
- [x] `README.md` documentant le setup et l'usage
- [x] Scripts utilitaires (`api/scripts/`) : import PocketBase, reset DB, génération quittance mensuelle + PDF + email
- [x] `POST /api/v1/withdraw/validate` — validation virement bancaire (matching withdrawName + montant → PDF + paid=True + email si sendLeaseRental)
- [x] `api/scripts/validate_withdrawal.sh` — script bash 2-curl (login + validate)
- [x] `GET/PATCH /api/v1/params/{owner_id}` — paramètres propriétaire (`rentReceiptDay`) stockés dans `params.yaml`
- [x] Cron quotidien 12h24 Europe/Paris — génération automatique des avis d'échéance par propriétaire au jour configuré (APScheduler + pytz, idempotent)

---

## 6. Suite (hors scope de ce plan)

- Script d'import des données depuis l'export PocketBase (via API REST PocketBase ou dump SQLite)
- ~~Règles d'autorisation fines par utilisateur~~ → **Implémenté** (voir §3.12 et `PLAN_MULTITENANCY.md`)
- ~~Génération PDF des quittances~~ → **Implémenté** (Phase H-bis — backend complet ✅)
- ~~Script génération quittance mensuelle + email~~ → **Implémenté** (`generate_receipt.py` — Phase I-bis ✅)
- ~~`validate_withdrawal` : validation virement bancaire~~ → **Implémenté** (`POST /withdraw/validate` + `validate_withdrawal.sh` — Phase J-bis ✅)
- ~~Cron génération automatique des avis d'échéance~~ → **Implémenté** (Phase L — APScheduler 12h24 Europe/Paris, idempotent ✅)
- Frontend PDF : bouton "Générer PDF" dans `TenantReceiptsDialog` (Phase G — `downloadReceiptPdf` ✅, `generateReceiptPdf` ❌)
- Envoi du justificatif `rentsFees` en pièce jointe dans l'avis d'échéance (actuellement seul le PDF quittance est joint)
- Envoi du justificatif `rentsFees` en pièce jointe dans l'avis d'échéance (actuellement seul le PDF quittance est joint)
- Refresh-token rotation et blacklist
- Pagination cursor-based
- Observabilité (logs structurés, métriques)
- Changement de mot de passe via un endpoint dédié (ex. `POST /me/change-password`)
- Audit log des accès par owner
