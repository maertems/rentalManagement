# Page Dashboard

**Status: ✅ Done (v1) — but data feedback loop is incomplete (see "Not done")**

## Purpose

Single overview screen used as the home page (`/`). Shows at-a-glance whether
each tenant has paid this month's rent, plus aggregate KPIs.

## Route

| Path | File | Component |
|------|------|-----------|
| `/` | `src/routes/_authenticated.index.tsx` | `DashboardPage` (inline) |

Sits under the `_authenticated` layout (auto-redirect to `/login` if no
session).

## Layout

```
┌────────────────────────────────────────────────────────┐
│ Tableau de bord                     [<] Avril 2026 [>] │
├────────────────────────────────────────────────────────┤
│  StatCards (4)                                         │
│  ┌──────┬──────┬──────┬──────┐                         │
│  │ Loc. │ Payé │ Imp. │ Occ. │                         │
│  │  N   │  N   │  N   │ N %  │                         │
│  └──────┴──────┴──────┴──────┘                         │
├────────────────────────────────────────────────────────┤
│  OccupancyGrid                                         │
│  ┌─ Place A ──────────────────────────────────────────┐│
│  │  ┌─ Unit 1 ────────┐  ┌─ Unit 2 (coloc) ─────────┐ ││
│  │  │  Tenant ✓ 800€  │  │  Ch.1 — Bob    ✓ 400€    │ ││
│  │  └─────────────────┘  │  Ch.2 — Alice  ✗ 400€    │ ││
│  │                       └──────────────────────────┘ ││
│  └────────────────────────────────────────────────────┘│
│  ┌─ Place B ──────────────────────────────────────────┐│
│  │  ┌─ Unit 1 ────────┐  ┌─ Unit 2 ─────────────────┐ ││
│  │  │  Tenant ✗ 700€  │  │  (vacant)                │ ││
│  │  └─────────────────┘  └──────────────────────────┘ ││
│  └────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────┘
```

**Places** : colonne pleine largeur, empilées verticalement (`flex flex-col gap-4`).  
**Logements dans chaque place** : côte à côte en `flex flex-wrap gap-3`, `min-w-[220px] flex-1` — passent à la ligne si l'écran est trop étroit.

## Components

| Component | File | Role |
|-----------|------|------|
| `PageHeader` | `src/components/common/PageHeader.tsx` | Title + actions (the month picker lives in actions) |
| `StatCards` | `src/features/dashboard/StatCards.tsx` | Computes 4 KPIs from the OccupancyResponse |
| `OccupancyGrid` | `src/features/dashboard/OccupancyGrid.tsx` | Renders one card per place with nested units / rooms / tenants |

`OccupancyGrid` recursively iterates:
- For each `place` → card with header (name, owner)
- For each `unit` inside → sub-card with header (name, level, "Coloc" badge)
- If `unit.flatshare === false` → list `unit.tenants` directly
- If `unit.flatshare === true` → list `unit.rooms`; each row shows `room.name —
  tenant name`
- Vacant rendering: italic "vacant" placeholder

## Backend endpoint

| Method | Path | Query | Response |
|--------|------|-------|----------|
| `GET` | `/api/v1/dashboard/occupancy` | `month=YYYY-MM` | Single aggregated object: `{ month, places: [{ placeId, units: [{ rooms, tenants }] }] }` |

The backend joins `places`, `placesUnits`, `placesUnitsRooms`, `tenants`,
`rents` (only `Loyer` active), and `rentReceipts` (only paid in the requested
month). One round-trip — no N+1.

## Hooks / state

- `useOccupancy(month)` — `queryKey: ["occupancy", month]`
- Local state: `cursor: Date` (always pinned to the 1st of a month). Prev/Next
  arrows shift by ±1 month.
- `monthKey(date)` formats as `YYYY-MM` for the API param.

## Payment rule

A tenant is shown with a green ✓ if a `rentReceipts` row exists where:
- `tenantId == tenant.id`
- `YEAR(periodBegin) == year AND MONTH(periodBegin) == month`
- `paid == 1`

Otherwise red ✗.

## KPIs computed in `StatCards`

| Card | Formula |
|------|---------|
| Locataires actifs | Count of all tenants in the tree |
| Loyer payé ce mois | Count of tenants with `rentPaid === true` |
| Loyer impayé | Count of tenants with `rentPaid === false` (red if > 0) |
| Taux d'occupation | `occupiedSlots / totalSlots`, where a slot is a unit (non-coloc) or a room (coloc) |

## Montant affiché par locataire

Priorité 1 — **`rentReceipts.amount`** du mois affiché (somme si plusieurs quittances) :
affichage normal en gris.

Priorité 2 — **fallback** : somme des `rents` actifs de type `Loyer` + `Charges` (quand aucune quittance n'existe pour ce mois) : affiché en gris clair italique avec tooltip "Estimation (pas de quittance ce mois)".

Le champ `rentAmountEstimated: bool` est renvoyé par le backend dans `OccupancyTenant`.

## Done

- ✅ Month navigation (←/→) anchored on current month at first render
- ✅ 4 KPI cards with icons and contextual coloring
- ✅ Hierarchical grid: places → units → rooms → tenants
- ✅ Places en colonne pleine largeur (une au-dessus de l'autre)
- ✅ Logements horizontaux à l'intérieur de chaque place (flex-wrap)
- ✅ Visual distinction: coloc badge, vacant rows in italic
- ✅ Empty state ("Aucun bien enregistré") with neutral box
- ✅ Single API call per month change
- ✅ Montant = total `rentReceipts` du mois (loyer + charges + extras) ; fallback loyer+charges depuis `rents` si pas de quittance, affiché en gris clair italique

## Not done / future

- ❌ **Manual receipt creation** — without it, the page always shows ✗
  everywhere. This is the single biggest functional gap.
  Sub-pages or modals to:
  - Generate receipts for a month for one or all tenants
  - Toggle paid/unpaid on a receipt
  - Edit amount, period
- ❌ Click on a tenant → quick view (open the receipts modal)
- ❌ Click on a place / unit → navigate to `/places` and scroll to that node
- ❌ Loading skeletons (currently plain "Chargement…" text)
- ❌ Year navigation (only month-by-month for now)
- ❌ Stat card for "fees this month" (`rentsFees`)

## Edge cases handled

- No places at all → empty state with friendly message
- Unit with no tenants → "vacant"
- Coloc unit with no rooms → row "Aucune chambre"
- Coloc room without a tenant → "{roomName} — vacant"
- Unit with `flatshare=1` but tenants assigned at unit level (not room) → those
  tenants are not displayed (data inconsistency); we may want to fall back to
  showing them
