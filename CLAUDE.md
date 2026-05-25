# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**MakeMyMock Admin** — internal observability + management console that sits next to the **Client** product. Where the Client is what students see, the Admin is what the operators see: who signed up, who's active, exports to CSV, mass promo emails, and a question-catalog browser with correct answers and solutions revealed.

Two top-level packages, mirroring the Client layout exactly so context transfers cleanly:
- [backend/](backend/) — FastAPI + MongoDB (Motor async) API. Reads from the same Mongo cluster the Client writes to. Read-mostly.
- [frontend/](frontend/) — React 19 + Vite SPA. Sidebar shell + protected routes.

## Common commands

### Backend (run from [backend/](backend/))

```powershell
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

API docs at http://localhost:8001/docs. Health at `/health`. All feature routes are mounted under `settings.API_V1_PREFIX` (default `/api/v1`).

The admin backend runs on port **8001** by convention so it can run alongside the Client backend (port 8000) on the same machine.

### Frontend (run from [frontend/](frontend/))

```powershell
npm install
npm run dev        # vite on :3100, auto-opens browser
npm run build      # production build to dist/
npm run preview    # serve the built dist/
npm run lint       # eslint . (flat config)
```

`VITE_API_BASE_URL` (in `frontend/.env`) must point at the admin backend, e.g. `http://localhost:8001/api/v1`.

## Backend architecture

Same conventions as the Client backend (see [backend/folder_structure.md](backend/folder_structure.md)).

- `controller → service → repository` per module.
- `core/dependencies.py` exposes `DBDep`, `QuestionsDBDep`, and `CurrentAdmin`.
- Admin identity is **single-tenant via env vars** — `ADMIN_EMAIL` + `ADMIN_PASSWORD_HASH` (preferred) or `ADMIN_PASSWORD`. Tokens are stamped with `role=admin` so a Client token cannot be reused here.
- Two Mongo handles: the primary DB (`MONGO_DB_NAME`, e.g. `makemymock`) and the catalog DB (`MONGO_QUESTIONS_DB_NAME`, e.g. `bbd_db`).
- The admin owns **no indexes**. The Client backend's `_ensure_indexes()` already covers every collection this service reads.

Modules:
- `authentication/` — `/auth/login`, `/auth/refresh-token`, `/auth/me`.
- `stats/` — `/stats/overview` (counters + 30-day signup trend).
- `users/` — `/users` (list), `/users/{id}` (detail), `/users/export.csv` (one-click CSV), `/users/emails` (used by the promo composer).
- `promotional_email/` — `/promo-emails/preview`, `/promo-emails/send`. Bounded concurrency; per-recipient results in the response.
- `questions/` — `/questions/catalog`, `/questions`, `/questions/{id}`. Heterogeneous source documents are normalised in the service before the schema sees them.

## Frontend architecture

React 19 + Vite SPA. CSS Modules for styling. Sidebar shell at [components/layout/AdminShell.jsx](frontend/src/components/layout/AdminShell.jsx) wraps every protected page via a parent route in [routes/AppRoutes.jsx](frontend/src/routes/AppRoutes.jsx).

Same hard rules as the Client frontend (see [frontend/folder_structure.md](frontend/folder_structure.md)):

- `services/` owns all HTTP. Components never import axios directly.
- `utils/token.js` owns localStorage. Keys are `mmma_*` (different namespace from the Client's `mmm_*`).
- Pages own their CSS module (`<page>.module.css`, lowercase).
- Env vars start with `VITE_`, live in both `.env` and `.env.example`, are read only inside `services/`.
- The CSV download in [services/userService.js](frontend/src/services/userService.js) uses native `fetch()` so the browser streams the body straight to disk instead of buffering through axios.

## Operational notes

- **Admin port:** backend 8001, frontend 3100. Adjust in `vite.config.js` if these collide.
- **CORS:** backend currently allows `*`; tighten in production to the admin frontend's origin.
- **Email:** prefer `BREVO_API_KEY` for cloud deploys — most hosts block outbound port 587 so SMTP times out. SMTP is the local-dev fallback.
- **Promo concurrency:** `PROMO_EMAIL_CONCURRENCY` caps in-flight sends. The hard cap on a single batch is `PROMO_EMAIL_MAX_RECIPIENTS`.

## Database collections (reference)

Read-only from this service:
- `users`, `student_profiles`, `email_otps` (auth domain — read for stats and listing).
- `mock_test_sessions`, `battles` (per-user activity counters).
- `questions` (catalog — lives in `MONGO_QUESTIONS_DB_NAME`).

The mock-test detailed collections (`mock_test_responses`, `mock_test_topics`, `user_topic_attempts`, the id-map collections) are **off-limits to this service** — they're owned by the Client's `modules/mock_test/`. If you need their data here, hit the Client's HTTP API instead of reading the collections directly.
