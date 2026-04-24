# Rental Management — Frontend

React + Vite + TypeScript SPA for the Rental Management backend.

## Start

```bash
cd front
sudo docker-compose up --build
```

Then open `http://localhost:5173`.

The backend API is expected at `http://localhost:8000` (same host, different port).

## Login

Default admin seeded by the backend: `admin@admin.com` / `admin123`.

## Stack

- React 18 + TypeScript
- Vite (HMR via file polling inside Docker)
- TanStack Router (file-based)
- TanStack Query
- Tailwind CSS + shadcn/ui
- axios (with `withCredentials` for httpOnly cookies)
- react-hook-form + zod
- lucide-react, sonner (toasts)
