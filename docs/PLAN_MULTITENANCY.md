# Plan — Multi-tenancy : isolation par propriétaire

> **Objectif** : chaque propriétaire (owner) est lié à un compte utilisateur et
> ne voit et ne peut interagir qu'avec ses propres données. L'admin conserve
> une vue et des droits globaux.
>
> Status legend : ❌ Todo · ✅ Done
>
> Last updated: 2026-04-15 — Phases A–F implémentées

---

## 0. Règles métier à implémenter

| Règle | Détail |
|-------|--------|
| **Owner ↔ User 1-pour-1** | Un owner a toujours un `userId`. Un user a au plus un owner. |
| **Isolation lecture** | Un owner ne voit que ses places, units, rooms, tenants, rents, rentReceipts et son dashboard. |
| **Isolation écriture** | Un owner ne peut créer/modifier/supprimer que ses propres ressources. |
| **Admin = vue globale** | L'admin voit tout, crée tout, gère utilisateurs et owners. |
| **Menus cachés** | "Propriétaires" et "Utilisateurs" disparaissent de la sidebar pour un non-admin. |
| **Page "Mes infos"** | Tout utilisateur authentifié a accès à une page combinée user + owner (lecture et édition de ses propres infos). |

---

## 1. Architecture du filtrage (backend)

La chaîne de propriété est :

```
Owner → Place → PlacesUnit → PlacesUnitsRoom
                           → Tenant → Rent
                                    → RentReceipt
```

Pour un utilisateur non-admin, toute requête LIST ou écriture doit être
contrainte à l'`ownerId` de l'utilisateur courant.

### Nouvelle dépendance FastAPI : `get_owner_context`

```python
# deps.py
async def get_owner_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Owner | None:
    """
    Retourne l'Owner lié au user courant.
    Retourne None si admin sans owner (= vue globale).
    Lève 403 si non-admin sans owner (compte orphelin).
    """
```

Cette dépendance est injectée dans tous les endpoints LIST et write.  
- `owner_ctx is None` → admin → pas de filtre  
- `owner_ctx` = instance Owner → filtre appliqué sur l'`ownerId`

---

## 2. Phase A — Backend : liaison Owner-User obligatoire ✅

### A1 — Validation `userId` requis à la création
- `OwnerCreate.userId` devient `int` (non nullable).
- Vérification que le `userId` existe (`ensure_exists`).
- Vérification qu'aucun autre owner n'utilise déjà ce `userId` (unicité logique, pas de contrainte DB).
- Pas de migration SQL (colonne déjà nullable en DB — compatibilité données existantes).

### A2 — Nouvel endpoint `POST /api/v1/owners/full` (admin only)
Crée atomiquement un user + un owner en une seule transaction.

```
Body:
{
  user: { email, password, name?, username?, isAdmin? }
  owner: { name?, email?, address?, zipCode?, city?, phoneNumber?, iban? }
}
Response: { user: UserRead, owner: OwnerRead }
```

- Remplace le workflow actuel "créer user puis créer owner".
- L'`OwnerCreate` standard (`POST /owners`) reste disponible pour lier un owner à un user existant.
- `POST /owners` et `POST /owners/full` → `get_admin_user` (admin only).
- `DELETE /owners/{id}` → `get_admin_user`.
- `PATCH /owners/{id}` → admin ou owner lui-même via `get_owner_context`.

### A3 — Nouvel endpoint `GET + PATCH /api/v1/me/profile`
Retourne et met à jour les infos combinées user + owner du compte courant.

```
GET /api/v1/me/profile
Response: { user: UserRead, owner: OwnerRead | null }

PATCH /api/v1/me/profile
Body: { user?: { name?, username? }, owner?: { name?, email?, address?, ... } }
  (pas de changement de password ici — endpoint séparé à prévoir)
Response: { user: UserRead, owner: OwnerRead | null }
```

---

## 3. Phase B — Backend : isolation en lecture ✅

Chaque endpoint LIST reçoit `owner_ctx: Owner | None = Depends(get_owner_context)`.  
Si `owner_ctx` est fourni, le filtre est appliqué.

| Endpoint | Filtre ajouté |
|----------|---------------|
| `GET /places` | `place.ownerId == owner_ctx.id` |
| `GET /placesUnits` | `unit.placeId IN (SELECT id FROM places WHERE ownerId == owner_ctx.id)` |
| `GET /placesUnitsRooms` | `room.placesUnitsId IN (units filtrées ci-dessus)` |
| `GET /tenants` | `tenant.placeUnitId IN (units filtrées)` |
| `GET /rents` | `rent.tenantId IN (tenants filtrés)` |
| `GET /rentReceipts` | `receipt.tenantId IN (tenants filtrés)` |
| `GET /dashboard/occupancy` | `places_rows` filtrées par `ownerId == owner_ctx.id` |
| `GET /owners` | admin → tout; non-admin → seulement son propre owner |
| `GET /users` | admin → tout; non-admin → seulement lui-même |

Les sous-queries de filtrage sont extraites dans un helper partagé :

```python
# services/scope.py
async def get_owner_place_ids(db, owner_id) -> list[int]: ...
async def get_owner_unit_ids(db, owner_id) -> list[int]: ...
async def get_owner_tenant_ids(db, owner_id) -> list[int]: ...
```

---

## 4. Phase C — Backend : isolation en écriture ✅

Pour chaque mutation (POST / PATCH / DELETE), vérifier que la ressource cible
appartient au scope de l'utilisateur courant. Lever `403 Forbidden` sinon.

Helper central :

```python
# services/scope.py
async def assert_owner_scope(db, owner_ctx, resource, resource_name): ...
# Vérifie que `resource` appartient au périmètre de owner_ctx.
# No-op si owner_ctx is None (admin).
```

| Endpoint | Vérification |
|----------|-------------|
| `POST /places` | `payload.ownerId == owner_ctx.id` |
| `POST /places/full` | `payload.place.ownerId == owner_ctx.id` |
| `PATCH /places/{id}` | `place.ownerId == owner_ctx.id` |
| `DELETE /places/{id}` | `place.ownerId == owner_ctx.id` |
| `POST /placesUnits` | `parent place.ownerId == owner_ctx.id` |
| `PATCH /placesUnits/{id}` | idem |
| `DELETE /placesUnits/{id}` | idem |
| `POST /placesUnitsRooms` | remonter jusqu'au place |
| `PATCH/DELETE /placesUnitsRooms/{id}` | idem |
| `POST /tenants/full` | `placeUnit.placeId` → `place.ownerId == owner_ctx.id` |
| `PATCH /tenants/{id}` | idem |
| `DELETE /tenants/{id}` | idem |
| `POST /rents` | `tenant.placeUnitId` → chaîne → owner |
| `PATCH/DELETE /rents/{id}` | idem |
| `POST /rentReceipts` | idem |
| `PATCH/DELETE /rentReceipts/{id}` | idem |

---

## 5. Phase D — Frontend : navigation ✅

### D1 — Masquer les menus admin
Dans `AppSidebar.tsx` :
- Masquer `Propriétaires` si `!user.isAdmin`.
- `Utilisateurs` est déjà masqué (garde `isAdmin` existante — vérifier).

### D2 — Ajouter "Mes infos"
Nouveau lien dans la sidebar, visible pour tous, pointant vers `/profile`.

```
┌──────────────────────┐
│ Accueil              │
│ Biens                │
│ Locataires           │
│ Propriétaires 🛡️     │  ← caché si non-admin
│ Utilisateurs  🛡️     │  ← caché si non-admin
│ ──────────────────── │
│ Mes infos            │  ← nouveau, pour tous
└──────────────────────┘
```

---

## 6. Phase E — Frontend : page "Mes infos" ✅

Nouveau fichier : `src/routes/_authenticated.profile.tsx`

### Layout

```
┌─────────────────────────────────────────────────┐
│ Mes informations                                │
├───────────────────┬─────────────────────────────┤
│ Mon compte        │ Mon profil propriétaire     │
│ ─────────────────  │ ──────────────────────────  │
│ Email (readonly)  │ Nom                         │
│ Nom               │ Email                       │
│ Username          │ Téléphone                   │
│ [Enregistrer]     │ Adresse / CP / Ville        │
│                   │ IBAN                        │
│                   │ [Enregistrer]               │
└───────────────────┴─────────────────────────────┘
```

- Si l'utilisateur est admin sans owner → section "Mon profil propriétaire" absente.
- Deux formulaires indépendants (chacun PATCH son côté).
- Utilise `GET /api/v1/me/profile` au chargement.

### Fichiers à créer/modifier

| Fichier | Action |
|---------|--------|
| `src/api/profileApi.ts` | `getMyProfile()`, `updateMyUser()`, `updateMyOwner()` |
| `src/hooks/useProfile.ts` | `useMyProfile()`, `useUpdateMyUser()`, `useUpdateMyOwner()` |
| `src/routes/_authenticated.profile.tsx` | Page inline |
| `src/components/layout/AppSidebar.tsx` | + lien "Mes infos", − "Propriétaires" si non-admin |

---

## 7. Phase F — Frontend : création owner+user (admin) ✅

Remplacer l'`OwnerFormDialog` actuel par un `OwnerFullFormDialog` qui inclut
une section "Compte utilisateur" (email + password + isAdmin checkbox).

Utilise `POST /api/v1/owners/full`.

L'ancien `OwnerFormDialog` (liaison à un user existant) est conservé mais
déprécié — peut être retiré une fois que tous les owners ont un userId.

---

## 8. Impact sur les tests existants ✅

| Test | Impact |
|------|--------|
| `test_owners.py` — `create_owner` | Ajouter `userId` dans le payload (créer un user d'abord) |
| `test_full_endpoints.py` — `create_place_full` | Idem (le place.ownerId doit pointer un owner avec userId) |
| `test_integrity.py` | Ajouter des tests de filtrage par scope |
| Nouveaux tests | Scope isolation : non-admin ne voit pas les données des autres |

---

## 9. Ordre d'exécution recommandé

```
Phase A  (deps + endpoints me/profile + owners/full)
   ↓
Phase B  (filtrage lecture — le plus gros)
   ↓
Phase C  (protection écriture)
   ↓
Phase D + E  (frontend sidebar + page Mes infos)  ← parallélisable avec B+C
   ↓
Phase F  (formulaire création owner+user admin)
   ↓
Mise à jour tests
```

---

## 10. Hors scope (v1 de cette feature)

- 🚫 Un owner peut avoir plusieurs users (1-pour-1 uniquement)
- 🚫 Délégation d'accès entre owners
- 🚫 Changement de password depuis "Mes infos" (endpoint séparé à planifier)
- 🚫 Migration automatique des owners existants sans userId
- 🚫 Audit log des accès par owner
