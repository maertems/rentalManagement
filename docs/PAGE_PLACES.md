# Page Places (Biens)

**Status: ✅ Done (v1)**

## Purpose

Manage the property hierarchy:
`Place → PlacesUnit → PlacesUnitsRoom`. A "Place" represents a building or
property; each Place contains one or more "PlacesUnits" (apartments, studios);
each flatshare unit may contain "PlacesUnitsRooms" (bedrooms rented separately).

## Route

| Path | File | Component |
|------|------|-----------|
| `/places` | `src/routes/_authenticated.places.tsx` | `PlacesPage` (inline) |

## Layout

```
┌─────────────────────────────────────────────────────┐
│ Biens                                  [+ Nouveau]  │
├─────────────────────────────────────────────────────┤
│ ┌─ 🏢 Immeuble Foch — 10 rue X, Paris ──── ✏️ 🗑️ ─┐ │
│ │  ┌─ 🏠 Appart 1 (niv 1, 45 m²)        ✏️ 🗑️ ─┐ │ │
│ │  └─ 🏠 Appart 2 (niv 2, 80 m²) [Coloc] ➕ ✏️ 🗑️│ │
│ │     ├─ 🚪 Chambre 1 (12 m²)            ✏️ 🗑️   │ │
│ │     └─ 🚪 Chambre 2 (14 m²)            ✏️ 🗑️   │ │
│ │                              [+ Ajouter logement]│ │
│ └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Components

| Component | File | Role |
|-----------|------|------|
| `PageHeader` | `src/components/common/PageHeader.tsx` | Title + [+ Nouveau] |
| `PlacesTree` | `src/features/places/PlacesTree.tsx` | Renders the 3-level hierarchy with action buttons |
| `PlaceFullFormDialog` | `src/features/places/PlaceFullFormDialog.tsx` | Creates a place + units + rooms in one atomic call |
| `PlaceEditDialog` | `src/features/places/PlaceEditDialog.tsx` | Edits a place's own fields only |
| `UnitFormDialog` | `src/features/places/UnitFormDialog.tsx` | Create OR edit a unit (mode driven by props: `placeId` for create, `unit` for edit) |
| `RoomFormDialog` | `src/features/places/RoomFormDialog.tsx` | Create OR edit a room (mode driven by `placesUnitsId` vs `room`) |
| `ConfirmDialog` | `src/components/common/ConfirmDialog.tsx` | All deletes |

## Backend endpoints

| Method | Path | Used for |
|--------|------|----------|
| `GET` | `/api/v1/places` | List places |
| `POST` | `/api/v1/places/full` | Atomic place + units + rooms creation |
| `PATCH` | `/api/v1/places/{id}` | Edit place |
| `DELETE` | `/api/v1/places/{id}` | Delete place (409 if has units) |
| `GET` | `/api/v1/placesUnits` | List ALL units (no `?placeId` filter — needed to render the tree) |
| `POST` | `/api/v1/placesUnits` | Create unit |
| `PATCH` | `/api/v1/placesUnits/{id}` | Edit unit |
| `DELETE` | `/api/v1/placesUnits/{id}` | Delete unit (409 if has rooms or tenants) |
| `GET` | `/api/v1/placesUnitsRooms` | List ALL rooms |
| `POST` | `/api/v1/placesUnitsRooms` | Create room |
| `PATCH` | `/api/v1/placesUnitsRooms/{id}` | Edit room |
| `DELETE` | `/api/v1/placesUnitsRooms/{id}` | Delete room (409 if room is occupied) |
| `GET` | `/api/v1/owners` | Populate the owner dropdown in dialogs |

## Hooks (in `src/hooks/usePlaces.ts`)

All mutations call `invalidatePlacesTree(qc)` which invalidates 4 query keys:
`["places"]`, `["placesUnits"]`, `["placesUnitsRooms"]`, `["occupancy"]` —
keeps the dashboard in sync too.

| Hook | Purpose |
|------|---------|
| `usePlacesList(filter)` | List places |
| `useAllPlacesUnits()` | List all units |
| `useAllRooms()` | List all rooms |
| `useCreatePlaceFull()` | Atomic create |
| `useUpdatePlace()` | Edit place |
| `useDeletePlace()` | Delete place |
| `useCreatePlacesUnit()` | Add unit |
| `useUpdatePlacesUnit()` | Edit unit |
| `useDeletePlacesUnit()` | Delete unit |
| `useCreateRoom()` | Add room |
| `useUpdateRoom()` | Edit room |
| `useDeleteRoom()` | Delete room |

## Tree rendering logic (`PlacesTree.tsx`)

1. Builds `Map<placeId, units[]>` and `Map<unitId, rooms[]>` once for O(1) lookup.
2. For each place: header card with owner name + action buttons.
3. For each unit: row with `flatshare` badge if applicable.
4. If `flatshare === 1`: list of rooms below the unit row.
5. Bottom of each place card: `[+ Ajouter un logement]` button.

The `[+ Ajouter une chambre]` button only appears next to flatshare units.

## Form behaviour

### `PlaceFullFormDialog` (create only)
Single big modal that lets you build the full tree in one shot. State is
managed locally with arrays of `UnitDraft` / `RoomDraft`. Rooms are sent only
when `flatshare` is checked. On submit → `POST /places/full`.

### `PlaceEditDialog`
Same fields as a Place: name, address, zipCode, city, ownerId (dropdown). PATCH only.

### `UnitFormDialog`
Fields: name, level, surfaceArea, friendlyName, flatshare (checkbox).
- If create mode: receives `placeId` prop, attached on POST.
- If edit mode: receives `unit` prop, fields pre-filled, PATCH.

### `RoomFormDialog`
Fields: name, surfaceArea.
- If create mode: receives `placesUnitsId` prop, attached on POST.
- If edit mode: receives `room` prop, fields pre-filled, PATCH.

## Done

- ✅ Tree view with 3 levels
- ✅ Create everything in one shot (modal with nested form)
- ✅ Edit / add / delete at each level (3 dialogs reused for create + edit)
- ✅ Flatshare toggle controls room visibility
- ✅ Toasts on every mutation
- ✅ Cache invalidation cascades (places + units + rooms + occupancy)
- ✅ 409 errors surface backend messages
- ✅ Client-side search bar (filter by name, city, address)

## Not done / future

- ❌ Filter by owner (dropdown in toolbar)
- ❌ Collapse/expand individual places (currently always expanded)
- ❌ Drag-and-drop to reorder units within a place
- ❌ Loading skeletons
- ❌ Smoke test
- ❌ Inline edit of unit name (currently dialog only)
- ❌ "Add unit" / "Add room" workflows are 1-by-1; no batch add

## Edge cases handled

- 0 places → empty state
- Place with 0 units → "Aucun logement" in body
- Coloc unit with 0 rooms → no list section, [+ Ajouter une chambre] still shown
- Toggling `flatshare` on an existing unit that already has rooms via PATCH:
  works, but the rooms remain in DB even if you uncheck. The dashboard hides
  them (because it only walks rooms when `flatshare === true`), but they
  reappear if you re-check.
- Delete cascades NOT supported; you must delete leaves first. The toasts make
  this explicit.

## Data-flow diagram

```
PlacesTree ──reads── places, units, rooms (3 useQuery calls)
                         ▲
   any mutation ─────────┘ invalidates ["places"|"placesUnits"|"placesUnitsRooms"|"occupancy"]
```
