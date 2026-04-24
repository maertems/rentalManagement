# Rental Management — Frontend Plan

Full specification of the web frontend.
All identifiers are in English, camelCase.

> **Status legend**
> - ✅ **Done** — implemented and live
> - ⚠️ **Partial** — basic version live, missing items called out
> - ❌ **Todo** — not implemented yet
> - 🚫 **Out of scope (v1)** — explicitly deferred
>
> Last updated: 2026-04-20 — RentsFees feature full stack ✅, logout redirect + cache clear ✅, TenantReceiptsDialog scrollable + PDF view ✅, users page email fix ✅, `isWithdraw` user role ✅, tenant detail page `/tenants/$tenantId` ✅, PDF download fix ✅ (`pdfFilename` en base), page Paramètres `/settings` ✅ (jour de génération des quittances par propriétaire, stocké dans `params.yaml`).

---

## 1. Goals

Build a single-page application used by the property manager to:

- ✅ Authenticate (login only, no self-registration)
- ✅ See at a glance which tenants have paid this month's rent (receipts can be created and toggled from `/tenants`)
- ✅ Manage owners, places (with units and rooms), and tenants
- ✅ Browse and manage receipts for each tenant (create, toggle paid, delete)
- ✅ Owner-scoped isolation — each owner sees and manages only their own data; admins have global access
- ✅ "Mes infos" page — any authenticated user can view and edit their own account + linked owner profile

---

## 2. Technical Stack — ✅ Done

| Layer | Choice | Status |
|-------|--------|--------|
| Build tool | **Vite 6** | ✅ |
| Language | **TypeScript 5** strict | ✅ |
| UI framework | **React 18.3** | ✅ |
| Routing | **TanStack Router** (file-based) | ✅ |
| Data fetching | **TanStack Query v5** | ✅ |
| HTTP client | **axios** with `withCredentials: true` | ✅ |
| UI library | **Tailwind CSS 3.4** + **shadcn/ui** primitives | ✅ |
| Forms | Native React forms with local state | ⚠️ — `react-hook-form` + `zod` are installed but not yet used. Forms work fine; can be migrated later. |
| Tables | Plain HTML tables with Tailwind | ⚠️ — `@tanstack/react-table` is installed but not yet used. Sufficient for v1 volumes. |
| Icons | **lucide-react** | ✅ |
| Date | **date-fns** + native `Intl.DateTimeFormat` | ✅ |

### Why not Next.js — n/a (decision honored)

---

## 3. Backend Changes Required Before The Frontend — ✅ Done

| # | Item | Status |
|---|------|--------|
| 3.1 | `users.isAdmin` column + model + schema | ✅ |
| 3.2 | Admin bootstrap at startup (with retry while DB warms up) | ✅ |
| 3.3 | Cookie auth (login / refresh / logout / me) + CORS `allow_credentials` | ✅ |
| 3.4 | `POST /api/v1/users` admin-only (via `get_admin_user` dependency) | ✅ |
| 3.5 | `GET /api/v1/dashboard/occupancy?month=YYYY-MM` (single SQL aggregation) | ✅ |
| 3.6 | `POST /api/v1/tenants/full` (atomic tenant + 3 rents + caution) | ✅ |
| 3.7 | `GET /api/v1/tenants/{id}/receipts` | ✅ |
| 3.8 | `POST /api/v1/places/full` (atomic place + units + rooms) | ✅ |
| 3.9 | `owners.userId` requis à la création — unicité 1-pour-1 enforced at API level | ✅ |
| 3.10 | `POST /api/v1/owners/full` — création atomique user + owner en une transaction | ✅ |
| 3.11 | `GET + PATCH /api/v1/me/profile` — infos combinées user + owner pour l'utilisateur courant | ✅ |
| 3.12 | `get_owner_context` dep + `services/scope.py` — isolation lecture et écriture par owner | ✅ |
| 3.13 | Tous les endpoints LIST filtrés par owner_ctx (places, units, rooms, tenants, rents, receipts, dashboard) | ✅ |
| 3.14 | Toutes les mutations protégées (`assert_place_scope`, `assert_unit_scope`, `assert_tenant_scope`) | ✅ |
| 3.15 | `GET /owners` et `GET /users` restreints au compte propre si non-admin | ✅ |
| 3.16 | `users.isWithdraw` colonne + `get_withdraw_user` dep + `POST /withdraw/validate` endpoint | ✅ |

Bonus done while implementing:
- ✅ `CORS_ORIGIN_REGEX` to accept any LAN host (needed when accessing the app
  via the LAN IP `192.168.x.y`)
- ✅ **27 backend tests passing** (including isolation tests, `/full` endpoints, and occupancy aggregator)

---

## 4. Repository Layout — ✅ Done

```
/data/lolo/dev/rentalManagement/
├── api/                  # backend (existing)
├── front/                # frontend (NEW — created in Phase B)
├── pocketBase/           # legacy import source
├── docs/                 # NEW — per-page detailed specs
│   ├── PAGE_LOGIN.md
│   ├── PAGE_DASHBOARD.md
│   ├── PAGE_OWNERS.md
│   ├── PAGE_PLACES.md
│   ├── PAGE_TENANTS.md
│   └── PLAN_MULTITENANCY.md   # spec complète isolation owner-scope (Phases A–F)
├── PLAN.md               # backend plan
└── FRONTEND_PLAN.md      # THIS file
```

---

## 5. Docker Setup — ✅ Done

- `front/Dockerfile` runs `npm install`, exposes 5173, runs `vite --host 0.0.0.0`.
- `front/docker-compose.yml` bind-mounts the entire project (`.:/app`) with an
  anonymous volume for `/app/node_modules`. This was required to fix the
  TanStack Router plugin's `EXDEV: cross-device link not permitted` error
  caused by `.tanstack/tmp/` being on a different filesystem than `src/`.
- HMR works via `CHOKIDAR_USEPOLLING=true` and `vite.config.ts` `usePolling: true`.
- `VITE_API_BASE_URL` is intentionally **unset** so the front resolves the API
  base URL from `window.location.hostname` at runtime — works on
  `localhost:5173`, `192.168.x.y:5173`, etc.

---

## 6. Project Structure (inside `front/`) — ✅ Done

```
front/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── postcss.config.js
├── index.html
├── README.md
├── public/
└── src/
    ├── main.tsx
    ├── routeTree.gen.ts             # generated by TanStack Router plugin
    ├── routes/
    │   ├── __root.tsx
    │   ├── login.tsx
    │   ├── _authenticated.tsx
    │   ├── _authenticated.index.tsx               → DashboardPage
    │   ├── _authenticated.owners.tsx              → OwnersPage (admin only)
    │   ├── _authenticated.places.tsx              → PlacesPage
    │   ├── _authenticated.tenants.tsx             → layout (Outlet) — parent /tenants
    │   ├── _authenticated.tenants.index.tsx       → TenantsPage (listing actifs + inactifs)
    │   ├── _authenticated.tenants.$tenantId.tsx   → TenantDetailPage (fiche locataire)
    │   ├── _authenticated.users.tsx               → UsersPage (admin guard)
    │   ├── _authenticated.profile.tsx             → ProfilePage (tous — "Mes infos")
    │   └── _authenticated.settings.tsx            → SettingsPage (tous — "Paramètres")
    ├── api/
    │   ├── httpClient.ts
    │   ├── types.ts                        # + ProfileRead, ProfileUpdate, OwnerFullInput, OwnerFullResponse
    │   ├── authApi.ts
    │   ├── ownersApi.ts                    # + createOwnerFull()
    │   ├── placesApi.ts
    │   ├── tenantsApi.ts                   # includes rents + receipts CRUD
    │   ├── usersApi.ts
    │   ├── dashboardApi.ts
    │   ├── profileApi.ts                   # getMyProfile(), updateMyProfile()
    │   └── paramsApi.ts                    # getOwnerParams(), updateOwnerParams()
    ├── hooks/
    │   ├── useAuth.ts
    │   ├── useOwners.ts                    # + useCreateOwnerFull()
    │   ├── usePlaces.ts
    │   ├── useTenants.ts                   # includes useCreateRentReceipt, useUpdateRentReceipt, etc.
    │   ├── useUsers.ts
    │   ├── useOccupancy.ts
    │   ├── useProfile.ts                   # useMyProfile(), useUpdateMyProfile()
    │   └── useParams.ts                    # useOwnerParams(ownerId), useUpdateOwnerParams()
    ├── contexts/
    │   └── authContext.tsx
    ├── components/
    │   ├── ui/                       # shadcn primitives
    │   │   ├── button.tsx
    │   │   ├── input.tsx
    │   │   ├── label.tsx
    │   │   ├── card.tsx
    │   │   └── dialog.tsx
    │   ├── layout/
    │   │   ├── AppLayout.tsx
    │   │   ├── AppSidebar.tsx
    │   │   └── AppHeader.tsx
    │   └── common/
    │       ├── PageHeader.tsx
    │       └── ConfirmDialog.tsx
    ├── features/
    │   ├── auth/
    │   │   └── LoginForm.tsx
    │   ├── dashboard/
    │   │   ├── StatCards.tsx
    │   │   └── OccupancyGrid.tsx
    │   ├── owners/
    │   │   ├── OwnersTable.tsx
    │   │   ├── OwnerFormDialog.tsx         # édition owner fields seuls (existant)
    │   │   ├── OwnerFullFormDialog.tsx     # création user + owner (admin) → POST /owners/full
    │   │   └── OwnerParamsDialog.tsx       # édition paramètres propriétaire (rentReceiptDay)
    │   ├── places/
    │   │   ├── PlacesTree.tsx
    │   │   ├── PlaceFullFormDialog.tsx
    │   │   ├── PlaceEditDialog.tsx
    │   │   ├── UnitFormDialog.tsx
    │   │   └── RoomFormDialog.tsx
    │   ├── tenants/
    │   │   ├── TenantsTable.tsx            # listing cliquable → navigation vers TenantDetailPage
    │   │   ├── TenantFullFormDialog.tsx    # création uniquement
    │   │   ├── TenantReceiptsDialog.tsx    # liste quittances + toggle payé + delete + view PDF + bouton "Frais & charges"
    │   │   └── TenantFeesDialog.tsx        # CRUD: create, delete, upload/download/delete justificatif
    │   └── users/
    │       └── UserFormDialog.tsx
    ├── lib/
    │   ├── utils.ts
    │   ├── queryClient.ts
    │   ├── formatters.ts
    │   └── apiError.ts
    └── styles/
        └── globals.css
```

Diff vs original plan:
- ⚠️ No `src/components/forms/` directory — forms are local to each
  feature folder.
- ⚠️ No `src/components/common/DataTable.tsx` — plain HTML tables are
  used directly. Will refactor to TanStack Table when sorting / pagination
  / virtualization is needed.
- ⚠️ No `src/features/{owners,places,tenants}/*Schema.ts` — zod schemas
  not used yet (form validation is done with simple checks).

---

## 7. Authentication Flow — ✅ Done

- `httpClient.ts` axios instance with `withCredentials: true`. Interceptor
  catches 401 (except on `/auth/*` endpoints), calls `/auth/refresh`, retries
  the original request once. On refresh failure → `window.location.href = '/login'`.
- `authContext.tsx` exposes `{ user, isLoading, login, logout, refresh }`.
- `_authenticated.tsx` route guard: on `beforeLoad`, calls `getMe()`; throws
  `redirect({ to: '/login' })` if unauthenticated.

---

## 8. State Management — ✅ Done

- ✅ Server state via TanStack Query, query keys per resource.
- ✅ Auth state via React context.
- ✅ Form state via local `useState` (will migrate to `react-hook-form` if
  forms grow).
- ✅ UI state (open dialogs, sidebar) via component state.

---

## 9. Layout — ✅ Done

```
┌────────────────────────────────────────────────┐
│ Header: "Gestion locative" · email · [Logout]  │
├──────────┬─────────────────────────────────────┤
│ Sidebar  │                                     │
│ Accueil  │                                     │
│ Biens    │          <Outlet />                 │
│ Locataires│                                    │
│ Propri.. 🛡│ (admin only — hidden for others)  │
│ Utilisat.🛡│ (admin only — hidden for others)  │
│ ──────── │                                     │
│ Mes infos│ (tous les utilisateurs)             │
└──────────┴─────────────────────────────────────┘
```

- ✅ Sidebar with active-route highlight (`activeProps`)
- ✅ Header with user email + admin badge + logout button
- ✅ "Propriétaires" masqué pour les non-admins
- ✅ "Utilisateurs" masqué pour les non-admins
- ✅ "Mes infos" visible pour tous, lien vers `/profile`
- ❌ Mobile burger menu — out of v1 scope

---

## 10. Pages — Status Summary

| Route | Page | Status | Detailed spec |
|-------|------|--------|---------------|
| `/login` | Login | ✅ Done | [docs/PAGE_LOGIN.md](docs/PAGE_LOGIN.md) |
| `/` | Dashboard | ✅ Done — data loop complete, filtré par owner pour non-admins | [docs/PAGE_DASHBOARD.md](docs/PAGE_DASHBOARD.md) |
| `/owners` | Owners (admin only) | ✅ Done — CRUD + search + création via OwnerFullFormDialog | [docs/PAGE_OWNERS.md](docs/PAGE_OWNERS.md) |
| `/places` | Places (Biens) | ✅ Done — CRUD tree + search, chaque owner ne voit que ses biens | [docs/PAGE_PLACES.md](docs/PAGE_PLACES.md) |
| `/tenants` | Tenants — listing | ✅ Done — listing actifs/inactifs + search, lignes cliquables → detail page, scoped par owner | [docs/PAGE_TENANTS.md](docs/PAGE_TENANTS.md) |
| `/tenants/:id` | Tenant — fiche détail | ✅ Done — sections Identité (+ adresse facturation inline), Logement, Paiement, Loyers ; mode lecture + édition inline ; archivage/réactivation |  |
| `/users` | Users (admin only) | ✅ Done — CRUD with admin guard, colonnes isAdmin + isWithdraw, checkboxes dans formulaire | [docs/PAGE_USERS.md](docs/PAGE_USERS.md) |
| `/profile` | Mes infos (tous) | ✅ Done — formulaire user + formulaire owner en deux cartes côte à côte | — |

Each page doc contains: layout, components, hooks, backend endpoints, form
behavior, edge cases handled, and "what's left to do" for that page.

---

## 11. Shared UI Components — ⚠️ Partially Done

| Component | Status | Notes |
|-----------|--------|-------|
| `Button`, `Input`, `Label`, `Card`, `Dialog` (shadcn) | ✅ | |
| `PageHeader` | ✅ | |
| `ConfirmDialog` | ✅ | |
| `DataTable` | ❌ | Not built. Pages use plain HTML tables. |
| `FormDialog` (generic wrapper) | ❌ | Each form dialog is its own component. |
| `FormField` (RHF wrapper) | ❌ | Forms use plain `<Input>` + `<Label>`. |
| `StatusBadge` | ❌ | Inline `<span>` instead. |
| `CurrencyInput` | ❌ | Plain `type=number` inputs. |
| `EmptyState` | ❌ | Each page hand-rolls its empty state. |
| Toaster (`sonner`) | ✅ | Globally mounted in `__root.tsx` |

These can be extracted later if duplication grows.

---

## 12. Design System — ✅ Done (defaults)

- ✅ shadcn defaults palette (neutral)
- ✅ `--radius: 0.5rem`
- ✅ System font stack (no Google Fonts dependency in Docker)
- 🚫 Dark mode (out of scope v1)

---

## 13. Error Handling & Toasts — ⚠️ Partial

| Item | Status |
|------|--------|
| `sonner` toaster mounted | ✅ |
| Success toasts on create/update/delete | ✅ |
| Backend `detail` extraction (`getApiErrorMessage`) | ✅ |
| 409 → toast with backend message | ✅ |
| 422 → toast with backend message | ✅ |
| 401 → axios interceptor refreshes silently | ✅ |
| 401 after refresh fails → redirect to /login | ⚠️ Brutal `window.location.href` (no message) |
| Inline form errors (per field) | ❌ Toast-only for now |
| Global error boundary | ❌ |

---

## 14. Testing — ❌ Not Done

- ❌ `vitest` + `@testing-library/react` not yet configured
- ❌ No smoke tests per page

The backend has 24 tests; the front has none yet. Acceptable for v1 polish but
should be added before any major refactor.

---

## 15. Internationalization — ✅ As planned

Hardcoded French throughout. No i18n layer.

---

## 16. Execution Phases — Status

### Phase A — Backend prerequisites — ✅ Done

| Step | Status |
|------|--------|
| A1 — `isAdmin` column / model / schema | ✅ |
| A2 — `ADMIN_EMAIL` / `ADMIN_PASSWORD` config | ✅ |
| A3 — startup hook seeds admin (with retry) | ✅ |
| A4 — cookie reader + `getAdminUser` dep | ✅ |
| A5 — login/logout/refresh cookie-based | ✅ |
| A6 — CORS `allow_credentials=True` + regex for LAN | ✅ |
| A7 — `POST /users` admin-only | ✅ |
| A8 — `/dashboard/occupancy` endpoint | ✅ |
| A9 — `/tenants/full` + `/tenants/{id}/receipts` | ✅ |
| A10 — `/places/full` | ✅ |
| A11 — tests updated (27/27 passing) | ✅ |
| A12 — `isWithdraw` colonne + modèle + schéma ; `get_withdraw_user` dep ; `POST /withdraw/validate` | ✅ |

### Phase B — Frontend bootstrap — ✅ Done

| Step | Status |
|------|--------|
| B1 — `Dockerfile`, `docker-compose.yml`, `package.json` | ✅ |
| B2 — `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts` | ✅ |
| B3 — `main.tsx`, `__root.tsx` (providers) | ✅ |
| B4 — `httpClient.ts` (axios + 401 interceptor) | ✅ |
| B5 — `authContext.tsx`, `useAuth.ts` | ✅ |
| B6 — shadcn primitives | ✅ (button, input, label, card, dialog) |
| B7 — `AppLayout`, `AppSidebar`, `AppHeader` | ✅ |
| B8 — common: `PageHeader`, `ConfirmDialog` | ✅ (no `DataTable` yet) |

### Phase C — Pages — ✅ Done

| Step | Page | Status |
|------|------|--------|
| C1 | `/login` | ✅ |
| C2 | `/` (dashboard) | ✅ |
| C3 | `/owners` | ✅ (CRUD + search by name) |
| C4 | `/places` | ✅ (CRUD on places + units + rooms) |
| C5 | `/tenants` | ✅ (CRUD + rent price edit + receipts CRUD + search) |
| C6 | `/users` | ✅ (admin-only CRUD — colonnes isAdmin + isWithdraw avec icônes, checkboxes dans UserFormDialog) |

### Phase D — Polish — ⚠️ Partial

| Step | Item | Status |
|------|------|--------|
| D1 | Global toast/error handling | ⚠️ Partial (per-mutation only) |
| D2 | Loading skeletons for each page | ❌ Plain "Chargement…" text |
| D3 | README in `front/` | ⚠️ Minimal |
| D4 | One smoke test per page | ❌ Not configured |

### Phase E — Multi-tenancy owner-scope — ✅ Done

| Step | Item | Status |
|------|------|--------|
| E1 | Sidebar : masquer "Propriétaires" et "Utilisateurs" pour non-admins | ✅ |
| E2 | Sidebar : ajouter lien "Mes infos" (`/profile`) pour tous | ✅ |
| E3 | `src/api/profileApi.ts` : `getMyProfile()`, `updateMyProfile()` | ✅ |
| E4 | `src/hooks/useProfile.ts` : `useMyProfile()`, `useUpdateMyProfile()` | ✅ |
| E5 | `src/routes/_authenticated.profile.tsx` : page "Mes infos" deux colonnes | ✅ |
| E6 | `src/api/types.ts` : `ProfileRead`, `ProfileUpdate`, `OwnerFullInput`, `OwnerFullResponse` | ✅ |
| E7 | `src/api/ownersApi.ts` : `createOwnerFull()` → `POST /owners/full` | ✅ |
| E8 | `src/hooks/useOwners.ts` : `useCreateOwnerFull()` | ✅ |
| E9 | `src/features/owners/OwnerFullFormDialog.tsx` : formulaire création user+owner (admin) | ✅ |
| E10 | `src/routes/_authenticated.owners.tsx` : "Nouveau" ouvre `OwnerFullFormDialog` | ✅ |
| E11 | `src/lib/formatters.ts` : `formatCurrency()` — toujours 2 décimales (`800,00 €`) | ✅ |

### Phase G — Génération PDF des quittances — ⚠️ Backend done, frontend partiel

| Step | Item | Status |
|------|------|--------|
| G1 | Backend : `app/services/pdf_context.py` — dataclass `ReceiptContext` + `get_receipt_context(db, receipt_id)` charge Tenant → PlacesUnit → Place → Owner | ✅ |
| G2 | Backend : `app/services/pdf_generator.py` — `generate_quittance_loyer`, `generate_avis_echeance`, `generate_quittance_garantie` (fpdf2 + num2words) | ✅ |
| G3 | Backend : `POST /api/v1/rentReceipts/{id}/pdf` — génère le PDF et l'écrit dans `/app/files/` ; 409 si déjà généré | ✅ |
| G4 | Backend : `GET /api/v1/rentReceipts/{id}/pdf` — sert le fichier existant (FileResponse) ; 404 si non généré | ✅ |
| G5 | Backend : `requirements.txt` + `fpdf2>=2.7.9` + `num2words>=0.5.14` | ✅ |
| G6 | Backend : `docker-compose.yml` volume `./files:/app/files` pour la persistance des PDF | ✅ |
| G7 | Frontend : `tenantsApi.ts` — `downloadReceiptPdf(id)` (blob) | ✅ (`generateReceiptPdf` ❌) |
| G8 | Frontend : `useTenants.ts` — `useDownloadReceiptPdf()` | ✅ (`useGenerateReceiptPdf` ❌) |
| G9 | Frontend : `TenantReceiptsDialog` — bouton "Voir PDF" (œil, ouvre blob dans onglet) par ligne | ✅ (bouton "Générer PDF" ❌) |

**Règles métier** :
- Le PDF est **immuable** une fois généré — POST → 409 si le fichier existe déjà.
- Auto-détection du type : garantie → `QuittanceGarantie` ; payé → `QuittanceLoyer` ; non payé → `AvisEcheance`.
- Type forçable via `?doc_type=quittance|avis|garantie`.
- Nom de fichier : `{zipCode}-{placeName}-{unitName}.{YYYY-MM}.{docType}.pdf` (espaces supprimés).
- Montant en lettres FR : centimes omis si `.00` (ex : "huit cents euros", pas "huit cents euros et zéro centime").
- `withdrawDay` clampé au dernier jour du mois (évite le 31 en février) ; fallback jour 6 si null.

---

### Phase H — Frais &amp; charges (RentsFees) — ✅ Done

#### Backend

| Step | Item | Status |
|------|------|--------|
| H1 | `app/schemas/rentsFee.py` : `hasDocument: bool = False` dans `RentsFeeRead` (calculé depuis filesystem, non stocké en DB) | ✅ |
| H2 | `app/crud/rentsFee.py` : `scope_tenant_ids: list[int] \| None` dans `list_filtered` | ✅ |
| H3 | `app/api/v1/rentsFees.py` : `FEES_DIR = /app/files/fees/`, `_doc_path(id)` via glob `{id}.*`, `_with_doc(fee, id)` | ✅ |
| H4 | CRUD avec isolation `get_owner_context` + `assert_tenant_scope` sur tous les endpoints | ✅ |
| H5 | `POST /rentsFees/{id}/document` — UploadFile, stocke en `fees/{id}{suffix}`, remplace l'existant | ✅ |
| H6 | `GET /rentsFees/{id}/document` — FileResponse | ✅ |
| H7 | `DELETE /rentsFees/{id}/document` — supprime le fichier | ✅ |
| H8 | `DELETE /rentsFees/{id}` — supprime aussi le justificatif associé si présent | ✅ |

#### Frontend

| Step | Item | Status |
|------|------|--------|
| H9 | `src/api/types.ts` : interface `RentsFee` (`id`, `tenantId`, `applicationMonth`, `description`, `subDescription`, `price`, `hasDocument`, `createdAt`, `updatedAt`) | ✅ |
| H10 | `src/api/tenantsApi.ts` : `RentsFeeInput`, `listTenantFees`, `createRentsFee`, `deleteRentsFee`, `uploadFeeDocument` (FormData), `downloadFeeDocument` (blob), `deleteFeeDocument` | ✅ |
| H11 | `src/hooks/useTenants.ts` : `useTenantFees`, `useCreateRentsFee`, `useDeleteRentsFee`, `useUploadFeeDocument`, `useDownloadFeeDocument`, `useDeleteFeeDocument` | ✅ |
| H12 | `src/features/tenants/TenantFeesDialog.tsx` : liste des frais (mois, description, sous-desc, montant), formulaire d'ajout, upload/download/delete justificatif par ligne, suppression de frais | ✅ |
| H13 | `src/features/tenants/TenantsTable.tsx` : bouton Receipt (icône) `onShowFees` pour les locataires actifs | ✅ |
| H14 | `src/routes/_authenticated.tenants.tsx` : state `showFees`, `TenantFeesDialog` branché | ✅ |

---

### Phase F — Owner/User 1-to-N + améliorations formulaires — ✅ Done

| Step | Item | Status |
|------|------|--------|
| F1 | Modèle DB : `users.ownerId` remplace `owners.userId` comme relation principale (1 owner → N users) | ✅ |
| F2 | Backend : `get_owner_context` utilise `user.ownerId` (lookup direct par PK) | ✅ |
| F3 | Backend : `crud_owner.create/update` — suppression contrainte unicité 1-to-1 sur `userId` | ✅ |
| F4 | Backend : `me.py` — `_get_owner_for_user` utilise `user.ownerId` | ✅ |
| F5 | `src/api/types.ts` : `User` + `ownerId: number \| null` ; `OwnerFullInput` supporte `user` OU `existingUserId` | ✅ |
| F6 | `src/api/usersApi.ts` : `UserInput` + `ownerId?: number \| null` | ✅ |
| F7 | `OwnerFullFormDialog` : toggle radio "Créer un nouvel utilisateur" / "Utiliser un existant" ; email saisi une seule fois → inséré dans `user.email` ET `owner.email` | ✅ |
| F8 | `UserFormDialog` : dropdown "Propriétaire associé" (liste tous les owners) | ✅ |
| F9 | Champs code postal : `type="number"` → `type="text" inputMode="numeric"` (suppression spinners +/−) dans `OwnerFormDialog`, `OwnerFullFormDialog`, `PlaceEditDialog`, `PlaceFullFormDialog`, `profile.tsx`, `TenantEditDialog` (billingZipCode) | ✅ |
| F10 | `TenantFullFormDialog` + `TenantEditDialog` : champ "Nom du virement" (`withdrawName`) dans section Logement | ✅ |
| F11 | Dashboard — layout : places en colonne pleine largeur, logements en `flex-wrap` horizontal à l'intérieur | ✅ |
| F12 | Dashboard — montant locataire : `rentReceipts.amount` du mois en priorité ; fallback `rents` (Loyer+Charges) affiché en gris clair italique + tooltip si pas de quittance (`rentAmountEstimated`) | ✅ |

---

## 17. What's Left To Build (Outside Phase D)

All **high-priority functional gaps** have been resolved:
- ✅ Receipts CRUD (create / toggle paid / delete / view PDF)
- ✅ Admin-only Users page (CRUD with guard)
- ✅ Search on `/places` and `/tenants`
- ✅ Owner-scope isolation (backend auto-filters; frontend receives only owned data)
- ✅ "Mes infos" page (user + owner self-edit)
- ✅ Admin création user+owner en une étape (`OwnerFullFormDialog`)
- ✅ Frais & charges (RentsFees) — liste, ajout, suppression, justificatif upload/download/delete
- ✅ Logout → redirect `/login` + `queryClient.clear()` (cache vidé)
- ✅ `TenantReceiptsDialog` — hauteur max + ascenseur + bouton œil pour voir le PDF
- ✅ Users page — fix crash `EmailStr` sur emails vides importés
- ✅ `isWithdraw` user role — colonne Withdraw (icône Landmark) + checkbox "Accès virement" dans `UserFormDialog`

### Remaining items (medium priority — quality of life)

1. **Générer PDF depuis le frontend** (Phase G) — bouton "Générer" par quittance dans `TenantReceiptsDialog` (appelle `POST /{id}/pdf` ; actuellement seul le téléchargement du PDF déjà généré est disponible via l'œil).
2. **Pagination UI** — backend supports `limit`/`offset`/`X-Total-Count`. UI
   shows everything in one page.
3. **Sortable columns** in tables.
4. **Bulk receipt generation** — generate all unpaid receipts for a given month
   across all active tenants in one click (button on dashboard or tenant page).
5. **Filter tenants by place/unit** (dropdown in toolbar).
6. **Inline form errors** (per-field) instead of toast-only validation.
7. **Loading skeletons** to replace plain "Chargement…" text.
8. **Error boundary** (global React error catcher).
9. **Changement de mot de passe** depuis "Mes infos" (endpoint backend à créer : `POST /me/change-password`).

### Polish

9. Smoke tests with vitest + Testing Library.
10. Migrate forms to `react-hook-form` + `zod` (already installed).
11. Migrate tables to `@tanstack/react-table` (already installed) once we need
    pagination/sort.
12. README expansion in `front/`.

---

## 18. Out Of Scope (v1) — 🚫 Confirmed deferred

- ⚠️ PDF generation of receipts — backend ✅, téléchargement frontend ✅ (Phase G), bouton "Générer" frontend ❌
- ⚠️ Script génération quittance mensuelle — `generate_receipt.py` ✅ (Phase I-bis PLAN.md) ; cron/automatisation planifiée 🚫
- ✅ Validation virement bancaire — `POST /withdraw/validate` ✅ + `validate_withdrawal.sh` ✅ (Phase J-bis PLAN.md)
- 🚫 Bank statement import / reconciliation
- 🚫 Dark mode
- 🚫 i18n
- 🚫 Mobile-first responsive design (current layout works on tablet+)
- 🚫 Forgot password / email verification
- 🚫 Per-user audit log
- 🚫 Hard delete of tenants (only deactivate)
- 🚫 Changement de password depuis "Mes infos" (endpoint backend non encore créé)
- ✅ Un owner avec plusieurs utilisateurs — implémenté en Phase F (relation 1-to-N via `users.ownerId`)
- 🚫 Délégation d'accès entre owners

---

## 19. Conventions — ✅ As planned

- ✅ Code: English identifiers, camelCase. (`firstName`, `placeUnitId`,
  `rentAmount`)
- ✅ UI copy: French, hardcoded.
- ✅ Component files: PascalCase (`OwnersTable.tsx`)
- ✅ Hook files: camelCase prefixed `use` (`useOwners.ts`)
- ✅ Query keys: `["resource", filterObject]`
- ✅ Currency display: `formatCurrency()` in `src/lib/formatters.ts` — always 2
  decimal places, `fr-FR` locale (e.g. `800,00 €`, `1 250,50 €`)
- ❌ Conventional Commits — not enforced (no commit hooks)
- ❌ zod schemas suffix — n/a (not using zod yet)
