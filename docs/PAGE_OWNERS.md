# Page Owners

**Status: ✅ Done (v1)**

## Purpose

Manage property owners (`owners` table). Each owner can be linked to one or
more `places`. An owner *may* also be linked to a system `userId` if the owner
should have a login account (rare in practice, but supported).

## Route

| Path | File | Component |
|------|------|-----------|
| `/owners` | `src/routes/_authenticated.owners.tsx` | `OwnersPage` (inline) |

## Layout

```
┌────────────────────────────────────────────┐
│ Propriétaires                  [+ Nouveau] │
├────────────────────────────────────────────┤
│ 🔍 Rechercher par nom…                     │
├────────────────────────────────────────────┤
│ Nom    | Email   | Tel | Ville | CP | Act. │
│ ─────────────────────────────────────────  │
│ ...    | ...     | ... | ...   | ...| ✏️ 🗑│
└────────────────────────────────────────────┘
```

## Components

| Component | File | Role |
|-----------|------|------|
| `PageHeader` | `src/components/common/PageHeader.tsx` | Title + [+ Nouveau] button |
| `OwnersTable` | `src/features/owners/OwnersTable.tsx` | Plain HTML table with hover, edit/delete actions per row |
| `OwnerFormDialog` | `src/features/owners/OwnerFormDialog.tsx` | Modal — works in create AND edit modes (driven by the `owner` prop being null or a row) |
| `ConfirmDialog` | `src/components/common/ConfirmDialog.tsx` | Generic destructive confirm |

## Backend endpoints

| Method | Path | Used by |
|--------|------|---------|
| `GET` | `/api/v1/owners?name=...` | List + search |
| `GET` | `/api/v1/owners/{id}` | (not yet wired — table data comes from list) |
| `POST` | `/api/v1/owners` | Create |
| `PATCH` | `/api/v1/owners/{id}` | Edit |
| `DELETE` | `/api/v1/owners/{id}` | Delete (returns 409 if owner has places) |

## Hooks (in `src/hooks/useOwners.ts`)

| Hook | Returns |
|------|---------|
| `useOwnersList(filter)` | `{ rows, total }` — `queryKey: ["owners", filter]` |
| `useCreateOwner()` | mutation; on success invalidates `["owners"]` |
| `useUpdateOwner()` | mutation; same invalidation |
| `useDeleteOwner()` | mutation; same invalidation |

## Form fields (`OwnerFormDialog`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | text | **yes** | Only required field |
| `email` | email | no | |
| `phoneNumber` | text | no | |
| `address` | text | no | |
| `zipCode` | number | no | Empty string → `null` |
| `city` | text | no | |
| `iban` | text | no | |

The dialog's `onSubmit` normalizes empty strings to `null` before sending
(prevents writing empty strings to MySQL).

## Behaviour

| Action | Effect |
|--------|--------|
| Click `[+ Nouveau]` | Opens dialog in create mode (empty form) |
| Click ✏️ on a row | Opens dialog in edit mode (form pre-filled) |
| Click 🗑️ on a row | Opens `ConfirmDialog` |
| Confirm delete | `DELETE /owners/{id}`. On success → toast "Propriétaire supprimé". On 409 → toast with backend message ("Cannot delete: referenced by places") |
| Type in search box | `useOwnersList({ name: search })` re-runs (server-side LIKE) |

## Done

- ✅ Server-side filter by name (LIKE `%name%`)
- ✅ Empty state ("Aucun propriétaire pour le moment")
- ✅ Loading state ("Chargement…")
- ✅ Form normalization (empty → null)
- ✅ Toast on success (create / update / delete)
- ✅ Toast on backend error (uses `getApiErrorMessage`)

## Not done / future

- ❌ Pagination UI (the API supports `limit`/`offset` and returns
  `X-Total-Count`, but the UI shows everything in one page)
- ❌ Sortable columns
- ❌ Filter by city or by linked user
- ❌ Filter by "has places" / "no places"
- ❌ Link owner ↔ user (the `userId` field is in the DB but not editable in
  the UI — only the dropdown of users would need to exist)
- ❌ Smoke test
- ❌ Loading skeletons (replace text "Chargement…")

## Edge cases handled

- Server-side LIKE search is case-insensitive (MySQL collation
  `utf8mb4_unicode_ci`)
- Delete blocked by 409 → toast shows the backend's exact message
- Empty zipCode in form → stored as `null`, not 0
