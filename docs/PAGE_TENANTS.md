# Page Tenants (Locataires)

**Status: ✅ Done (v1)**

## Purpose

Manage tenants. A tenant is linked to one `placesUnit` (and optionally one
`placesUnitsRoom` if the unit is a flatshare). A tenant is associated with up
to three `rents` rows (`Loyer`, `Charges`, `Garantie`) and any number of
`rentReceipts`.

## Route

| Path | File | Component |
|------|------|-----------|
| `/tenants` | `src/routes/_authenticated.tenants.tsx` | `TenantsPage` (inline) |

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Locataires                                    [+ Nouveau]   │
├─────────────────────────────────────────────────────────────┤
│ Actifs (N)                                                  │
│ Nom | Tel | Email | Logement | Loyer | Caution | 👁 ✏ ─    │
├─────────────────────────────────────────────────────────────┤
│ ▶ Inactifs (N)                                              │
│  (collapsed; expand to see deactivated rows with [Réactiver])│
└─────────────────────────────────────────────────────────────┘
```

## Components

| Component | File | Role |
|-----------|------|------|
| `PageHeader` | `src/components/common/PageHeader.tsx` | Title + [+ Nouveau] |
| `TenantsTable` | `src/features/tenants/TenantsTable.tsx` | Reusable table; `variant="active"` shows 👁 (receipts) + ✏️ (edit) + Désactiver; `variant="inactive"` shows ✏️ (edit) + Réactiver |
| `TenantFullFormDialog` | `src/features/tenants/TenantFullFormDialog.tsx` | Atomic create modal (tenant + 3 rents + optional caution receipt) |
| `TenantEditDialog` | `src/features/tenants/TenantEditDialog.tsx` | Edit identity + housing + billing + ALSO loyer / charges / caution prices |
| `TenantReceiptsDialog` | `src/features/tenants/TenantReceiptsDialog.tsx` | Read-only list of receipts for a tenant, sorted by `periodBegin` DESC |

## Backend endpoints

| Method | Path | Used for |
|--------|------|----------|
| `GET` | `/api/v1/tenants?active=1` | Active list |
| `GET` | `/api/v1/tenants?active=0` | Inactive list |
| `POST` | `/api/v1/tenants/full` | Atomic create (tenant + 3 rents + optional caution) |
| `PATCH` | `/api/v1/tenants/{id}` | Edit identity / housing / billing / `active` toggle |
| `GET` | `/api/v1/tenants/{id}/receipts` | Receipts modal data |
| `GET` | `/api/v1/rents` | Used by table to enrich each row with the active "Loyer" price |
| `GET` | `/api/v1/rents?tenantId={id}` | Used by edit dialog to pre-fill rent prices |
| `POST` | `/api/v1/rents` | Create a rent if not yet present (in edit dialog) |
| `PATCH` | `/api/v1/rents/{id}` | Update the price of an existing rent |
| `GET` | `/api/v1/rentReceipts` | Used by table to look up the caution amount via `warantyReceiptId` |
| `GET` | `/api/v1/places`, `/placesUnits`, `/placesUnitsRooms` | Build the housing dropdown labels |

## Hooks (in `src/hooks/useTenants.ts`)

| Hook | Purpose |
|------|---------|
| `useTenantsList(filter)` | List tenants — `queryKey: ["tenants", filter]` |
| `useCreateTenantFull()` | Atomic create |
| `useUpdateTenant()` | PATCH (used for edit + activate/deactivate) |
| `useTenantReceipts(tenantId)` | Receipts for one tenant; `enabled` only when `tenantId !== null` |
| `useAllRents()` | List all rents (cheap; used for table enrichment) |
| `useTenantRents(tenantId)` | Rents for one tenant — pre-fills the edit form |
| `useUpdateRent()` | PATCH a rent's price |
| `useCreateRent()` | POST a new rent (when none exists for a type) |
| `useAllRentReceipts()` | Enrich table with caution amount |

## Table enrichment

The table joins data **client-side** (no backend `enriched=true` endpoint yet):

- **Logement** column: `placeUnitId → unit → placeId → place`. If
  `placeUnitRoomId` set, append `" — roomName"`.
- **Loyer** column: from `rents` where `tenantId == t.id && type === "Loyer" && active`.
- **Caution** column: `tenant.warantyReceiptId → rentReceipts.amount`.

This means 4 list queries are fired alongside the tenants list. Acceptable at
v1's data volume; can be replaced by a backend `?enriched=true` endpoint later.

## Form behaviour

### `TenantFullFormDialog` (create only)

Sections: **Identité** | **Logement** | **Loyers** | **Caution**.

- The `Logement` dropdown is built from all `placesUnits` joined with their
  `places`. Selecting a flatshare unit reveals a `Chambre` dropdown filtered to
  rooms of that unit (required if the unit is flatshare).
- `Loyer / Charges / Garantie` prices are required.
- Optional checkbox "Caution déjà reçue" → if checked, a date input appears,
  and a `RentReceipt` is created with `paid=1`, then linked via
  `tenant.warantyReceiptId`.
- Submit → `POST /tenants/full` (single transactional call server-side).

### `TenantEditDialog`

Sections: **Identité** | **Logement** | **Loyers** | **Facturation**.

- `Identité`, `Logement`, `Facturation`: regular PATCH on `/tenants/{id}`.
- `Loyers` section pre-fills from `useTenantRents(tenantId)`. On submit:
  - For each of `Loyer`, `Charges`, `Garantie`:
    - If the field is empty → ignore.
    - Else if an active rent of that type exists AND the price changed →
      `PATCH /rents/{id}`.
    - Else if no active rent of that type exists → `POST /rents` (create new
      with `active=1`).
- The note "Modifier ces montants n'affecte que les futures quittances" makes
  the user aware that past `rentReceipts` are unchanged.
- Cache invalidation in mutations covers `["rents"]`, `["tenants"]`, and
  `["occupancy"]` so the dashboard updates immediately.

### `TenantReceiptsDialog` (CRUD)

Full interactive dialog for managing a tenant's receipts.

**Layout:**
```
┌─ Quittances — Alice Martin ─────────── [+ Nouvelle] ─┐
│                                                       │
│ (inline add form — visible when toggled)              │
│  Début [__] Fin [__] Montant [__]  [Ajouter]         │
│                                                       │
│ ┌─────────┬─────────┬─────────┬──────┬─────┐         │
│ │ Début   │ Fin     │ Montant │ Payé │     │         │
│ │ 01/04   │ 30/04   │ 800 €   │ ✓    │ 🗑️  │         │
│ │ 01/03   │ 31/03   │ 800 €   │ ✗    │ 🗑️  │         │
│ └─────────┴─────────┴─────────┴──────┴─────┘         │
└───────────────────────────────────────────────────────┘
```

**Features:**
- **[+ Nouvelle]** toggles an inline form at the top with: début (date), fin
  (date), montant (number). Creates with `paid = 0` by default.
- **Toggle paid/unpaid**: click the ✓ or ✗ icon → `PATCH /rentReceipts/{id}`
  with `paid: 0|1`. Toast confirms.
- **Delete**: trash icon per row → `DELETE /rentReceipts/{id}`.
- Cache invalidation cascades to `["tenantReceipts"]`, `["rentReceipts"]`, and
  `["occupancy"]` — the dashboard reflects changes immediately.

**Hooks:** `useCreateRentReceipt`, `useUpdateRentReceipt`, `useDeleteRentReceipt`.

## Done

- ✅ Active / inactive split (inactive section is collapsible, default closed)
- ✅ Atomic create flow including the 3 rents and optional caution
- ✅ Edit including rent price update (Loyer / Charges / Garantie)
- ✅ Receipts CRUD (create, toggle paid, delete) — no longer read-only
- ✅ Search by name, email, phone (client-side filter)
- ✅ Activate / deactivate toggle (PATCH `active`)
- ✅ Toasts on every action
- ✅ Cache invalidation cross-page (dashboard reflects rent price changes
  immediately)
- ✅ Validation: name, unit, room (if coloc), rent prices

## Not done / future

- ❌ Filter by place / unit (dropdown)
- ❌ Pagination UI
- ❌ Sortable columns
- ❌ Hard delete (only deactivate exposed; the API supports DELETE with 409
  cascading checks)
- ❌ Loading skeletons
- ❌ Smoke test
- ❌ When changing the assigned `placeUnit` of a tenant, the existing
  `rentReceipts` are not retroactively updated to point to the new unit (this
  is probably the desired behavior, but worth documenting)

## Edge cases handled

- Tenant with no rents → loyer column shows "—"
- Tenant with no `warantyReceiptId` → caution column shows "—"
- Tenant with no `placeUnitId` → logement column shows "—"
- Edit with one of the three rent prices left empty → that rent is left
  untouched (not deleted, not zeroed)
- Coloc unit selection without picking a room → submit is blocked with toast
- Toggle `billingSameAsRental` off → billing fields appear; toggling back on
  → fields are cleared on save (sent as null)
