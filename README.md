# Jaikalki HRMS

Multi-platform Human Resource Management System for **Jaikalki Technology
Pvt Ltd** (employee code prefix `JKT`).

One backend, three clients:

```
            ┌──────────────────────┐    ┌──────────────────────┐
            │  hrms_admin_web      │    │  hrms_mobile         │
            │  React + TS + Vite   │    │  Flutter (Android,   │
            │  Tailwind + shadcn   │    │  iOS, Web)           │
            └──────────────────────┘    └──────────────────────┘
                          ↘                ↙
                       ┌──────────────────────┐
                       │  hrms_backend        │
                       │  FastAPI + MySQL     │
                       │  + Redis + MinIO     │
                       └──────────────────────┘
```

## Repository layout

| Folder | Purpose |
|---|---|
| `hrms_backend/` | FastAPI backend (Python 3.11, SQLAlchemy 2.0 async, MySQL 8). |
| `hrms_admin_web/` | React 18 + TypeScript admin console. |
| `hrms_mobile/` | Flutter app — Android, iOS, Web. |
| `hrms_structure/` | Phase-by-phase architecture & implementation specs. |
| `app_designed/` | Design system & screen mockups (`jaikalki-design.html`). |
| `logos/` | Brand asset pack — 19 PNGs (lockups, app icons, splash, favicons). |

## Quick start

```bash
# Backend
cd hrms_backend
docker-compose up -d mysql redis minio phpmyadmin
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload   # http://localhost:8000

# Admin web
cd ../hrms_admin_web
npm install
cp .env.example .env
npm run dev                     # http://localhost:5173

# Mobile / web
cd ../hrms_mobile
flutter pub get
flutter run -d chrome           # http://localhost:8081 (or chosen port)
```

## Production environment

| Surface | URL |
|---|---|
| API | `https://api-hrms.jaikalki.com` |
| Admin web | `https://portal.jaikalki.com` |
| Flutter mobile | reads `API_BASE_URL` dart-define; falls back to the prod URL above in release builds |

Production overrides:

- **Backend** — copy `hrms_backend/.env.production.example` → `.env`,
  fill in DB / Redis / S3 / `JWT_SECRET_KEY`.
- **Admin web** — `hrms_admin_web/.env.production` is loaded automatically
  by `npm run build`.
- **Mobile** — `flutter build apk --release` or
  `flutter build web --release` automatically targets the prod API.
  Override per-build with `--dart-define=API_BASE_URL=https://...`.

## Brand tokens (single source of truth)

Defined in three places that must stay in sync:

| Surface | File |
|---|---|
| Spec / mockups | `app_designed/jaikalki-design.html` (`:root` CSS variables) |
| React (Tailwind) | `hrms_admin_web/tailwind.config.ts` + `src/index.css` |
| Flutter | `hrms_mobile/lib/core/theme/app_colors.dart` |

Core palette: brown `#3D2817`, gold `#F4B71F`, cream `#FDF8EE`,
warm white `#FAFAF7`. Fonts: Playfair Display (display), Poppins (body),
JetBrains Mono (labels).

## Phase progress

- ✅ **Phase 0 — Foundation** (this commit). Three runnable projects,
  Docker stack, design system wired in, logos in place.
- ⏳ Phase 1 — Auth + RBAC (backend) & Phase 1.5 — React admin auth.
- ⏳ Phase 2 — Employee master with Jaikalki categories
  (Intern / Trainee / Permanent / Contract).
- See `hrms_structure/README.md` for the full 21-phase plan.
