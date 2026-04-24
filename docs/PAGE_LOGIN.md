# Page Login

**Status: ✅ Done (v1)**

## Purpose

Sole entry point for the application. Authenticates a user via email + password
against the backend, which returns httpOnly cookies (`accessToken`,
`refreshToken`). No public registration: only an admin can create users (out of
scope for this page).

## Route

| Path | File | Component |
|------|------|-----------|
| `/login` | `src/routes/login.tsx` | `LoginForm` (`src/features/auth/LoginForm.tsx`) |

The route's `beforeLoad` calls `authApi.getMe()`. If it succeeds (user already
authenticated), the route redirects to `/`. Otherwise the form is shown.

## Layout

- Centered card on a light grey background, no sidebar/header.
- Card title: "Connexion", subtitle: "Gestion locative".
- Two stacked inputs + one full-width primary button.

```
┌────────────────────────┐
│ Connexion              │
│ Gestion locative       │
│                        │
│ Email     [_________]  │
│ Mot pwd   [_________]  │
│                        │
│ [   Se connecter   ]   │
└────────────────────────┘
```

## Form fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | email | yes | `autoComplete="email"` |
| `password` | password | yes | `autoComplete="current-password"` |

## Behaviour

| Event | Effect |
|-------|--------|
| Submit success | `useAuth().login()` runs → API sets cookies → `setUser()` → `navigate({ to: '/' })` |
| Submit 401 | Toast: "Identifiants invalides" |
| Submit other error | Toast: "Erreur de connexion" |
| Submit in flight | Button disabled, label changes to "Connexion…" |

## Backend endpoints

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/api/v1/auth/login` | `{ email, password }` | `User` (200) + Set-Cookie `accessToken`, `refreshToken` |
| `GET` | `/api/v1/auth/me` | — | `User` (200) — used by `beforeLoad` |

## Hooks / state

- `useAuth()` from `@/hooks/useAuth` — exposes `login(email, password)` which
  wraps `authApi.login` and updates `AuthContext.user`.
- Local component state: `email`, `password`, `submitting`.

## Done

- ✅ Form rendering, validation (`required`, `type=email`)
- ✅ Submit → cookies set → redirect
- ✅ Auto-redirect to `/` if already authenticated
- ✅ 401 inline toast
- ✅ Disabled state during submission

## Not done / future

- ❌ "Show password" toggle (eye icon)
- ❌ "Mot de passe oublié" — out of scope v1
- ❌ Loading skeleton on `beforeLoad` redirect check (currently a brief flash)
- ❌ Smoke test (`vitest`)

## Edge cases handled

- Already logged in user typing `/login` → redirected to `/`
- Backend down → axios timeout → "Erreur de connexion" toast
- Wrong password → server returns 401 (caught in interceptor as auth endpoint
  → no refresh attempt) → toast
