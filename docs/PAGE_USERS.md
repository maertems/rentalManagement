# Page Users (Utilisateurs)

**Status: ✅ Done (v1)**

## Purpose

Admin-only page to manage system login accounts (`users` table). Only users
with `isAdmin = 1` can access this page. Regular users who navigate to `/users`
are redirected to `/`.

## Route

| Path | File | Component |
|------|------|-----------|
| `/users` | `src/routes/_authenticated.users.tsx` | `UsersPage` (inline) |

**Access control**: the route's `beforeLoad` calls `authApi.getMe()` and
checks `me.isAdmin`. If not admin → `redirect({ to: '/' })`.

**Sidebar visibility**: the "Utilisateurs" link only appears when
`useAuth().user.isAdmin === 1`.

## Layout

```
┌────────────────────────────────────────────────────┐
│ Utilisateurs                        [+ Nouveau]    │
│ Seuls les administrateurs peuvent gérer cette page │
├────────────────────────────────────────────────────┤
│ Email | Nom | Username | Admin | Créé le | Actions │
│ ────────────────────────────────────────────────── │
│ admin@... | Admin | — | 🛡️ | 13/04/26 | ✏️ 🗑️     │
│ user1@... | User 1 | — | — | 13/04/26 | ✏️ 🗑️     │
└────────────────────────────────────────────────────┘
```

## Components

| Component | File | Role |
|-----------|------|------|
| `PageHeader` | `src/components/common/PageHeader.tsx` | Title + subtitle + [+ Nouveau] |
| `UserFormDialog` | `src/features/users/UserFormDialog.tsx` | Create or edit user (mode driven by `user` prop being null or existing) |
| `ConfirmDialog` | `src/components/common/ConfirmDialog.tsx` | Delete confirmation |
| Table | Inline in UsersPage | Simple HTML table |

## Backend endpoints

| Method | Path | Auth required | Used for |
|--------|------|---------------|----------|
| `GET` | `/api/v1/users` | Any authenticated user | List all users |
| `POST` | `/api/v1/users` | **Admin only** (403 otherwise) | Create user |
| `PATCH` | `/api/v1/users/{id}` | **Admin only** | Edit user |
| `DELETE` | `/api/v1/users/{id}` | **Admin only** | Delete user |

## Hooks (in `src/hooks/useUsers.ts`)

| Hook | Purpose |
|------|---------|
| `useUsersList()` | `queryKey: ["users"]` — list all users |
| `useCreateUser()` | mutation → POST, invalidates `["users"]` |
| `useUpdateUser()` | mutation → PATCH, invalidates `["users"]` |
| `useDeleteUser()` | mutation → DELETE, invalidates `["users"]` |

## Form fields (`UserFormDialog`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | email | **yes** | Used as login identifier |
| `username` | text | no | Optional display name |
| `name` | text | no | Full name |
| `password` | password | **yes** (create) / no (edit) | In edit mode: "laisser vide pour ne pas changer" |
| `isAdmin` | checkbox | no | Defaults to unchecked |

## Behaviour

| Action | Effect |
|--------|--------|
| Click `[+ Nouveau]` | Opens dialog in create mode |
| Click ✏️ | Opens dialog in edit mode, fields pre-filled, password empty |
| Click 🗑️ | Opens confirm dialog |
| Confirm delete | `DELETE /users/{id}`. Toast on success. Toast with error message on 409 (e.g. if user is referenced by owners) |
| Non-admin tries to access `/users` | Redirected to `/` by `beforeLoad` guard |
| Non-admin API call to `POST /users` | Backend returns 403, toast: "Admin privileges required" |

## Done

- ✅ Route with admin guard (`beforeLoad` + sidebar visibility)
- ✅ List all users with admin badge
- ✅ Create user (email + password required)
- ✅ Edit user (password optional)
- ✅ Delete user with confirmation
- ✅ Toast on all operations

## Not done / future

- ❌ Password strength indicator
- ❌ Force-reset password flag
- ❌ Prevent deleting yourself (currently allowed — leads to session loss)
- ❌ User profile self-edit page (non-admin users editing their own name)
- ❌ Search / filter
- ❌ Pagination
