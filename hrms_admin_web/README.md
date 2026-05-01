# Jaikalki HRMS — Admin Web

React + TypeScript + Vite + Tailwind + shadcn/ui admin console for
**Jaikalki Technology Pvt Ltd**.

## Quick start

```bash
npm install
cp .env.example .env
npm run dev
```

App opens at <http://localhost:5173> and proxies `/api` to the FastAPI
backend on `:8000`.

## Stack

- React 18 + TypeScript (strict)
- Vite 5
- Tailwind CSS 3 + shadcn/ui (custom Jaikalki tokens)
- React Router v6
- TanStack Query + Axios (httpOnly cookie auth)
- Zustand for client state
- React Hook Form + Zod for forms

## Brand tokens

Configured in `tailwind.config.ts` and `src/index.css`:

- Brown palette: `brand-brown` `#3D2817`, plus `-dark` / `-darker` / `-light` / `-50` / `-100`
- Gold accent: `brand-gold` `#F4B71F`, plus `-bright` / `-light` / `-dark` / `-pale`
- Surfaces: `surface-warm` `#FAFAF7`, `surface-cream` `#FDF8EE`
- Role colors: `role-{superadmin,admin,director,hr,manager,employee,field,trainer,intern}`
- Fonts: `font-display` Playfair Display, `font-body` Poppins, `font-mono` JetBrains Mono

## Project layout

```
src/
  components/
    ui/         shadcn primitives (button, input, label, card)
    layouts/    AdminLayout (sidebar + header)
    shared/     Logo, branding helpers
  features/
    auth/       LoginPage
    dashboard/  DashboardPage, PlaceholderPage
    super-admin/, admin/, employees/, reports/  (filled in later phases)
  lib/
    api/        Axios client + per-resource modules
    constants.ts, utils.ts
  store/        Zustand stores (auth)
  router/       React Router config
  hooks/, types/
public/branding/  PNG logos (favicons, lockups)
```

## Phase status

- Phase 0 ✅ — Foundation: structure, theme, layout, login + dashboard skeletons,
  axios client wired to `/health`.
- Phase 1.5 — auth (login → cookie session), protected routes, role-aware nav.
- Phase 4.5 — Super Admin module config & permission editor.
