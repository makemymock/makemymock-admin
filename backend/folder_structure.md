# Admin Backend Folder Structure

FastAPI + MongoDB (Motor async driver) admin observability API for **MakeMyMock**.
It mirrors the Client backend's conventions so anything you learnt over there
applies here.

---

## Top-level layout

```
backend/
├── api/                  # Aggregates module routers under one APIRouter
├── config/               # Settings (.env) + MongoDB client/lifespan
├── core/                 # Cross-cutting concerns shared by all modules
├── modules/              # Feature modules (one folder per domain)
│   ├── authentication/   # Single-tenant admin login (env-based credentials)
│   ├── stats/            # Dashboard overview counters + signup trend
│   ├── users/            # User listing, detail, CSV export
│   ├── promotional_email/# Mass email composer + dispatcher
│   ├── questions/        # Catalog browser (subject → chapter → topic → Q)
│   └── contest/          # Scheduled contests: CRUD + read-only participants view.
│                         #   Writes go to `contests`; reads from `contest_participations`
│                         #   (Client backend owns the writes there).
├── services/             # Reserved for cross-module orchestration services
├── main.py               # FastAPI app factory + lifespan + global handlers
├── requirements.txt
├── .env                  # Real secrets (gitignored)
└── .env.example          # Template
```

---

## Layer responsibilities

### `config/`
- `settings.py` — Pydantic v2 `BaseSettings` reading from `.env`. The admin
  service has an extra `MONGO_QUESTIONS_DB_NAME` setting because the Client
  deployment splits the questions catalog into `bbd_db`.
- `database.py` — Motor client lifecycle. Exposes both `get_database()` (the
  primary DB) and `get_questions_database()` (the catalog DB).

### `core/`
Reusable infrastructure. Modules import **from** core, never the reverse.

- `security.py` — bcrypt verify/hash.
- `jwt_handler.py` — admin-scoped tokens (`role=admin` claim).
- `email.py` — Brevo HTTPS + SMTP fallback, per-module Jinja2 template loader.
- `exceptions.py` — domain exception subclasses.
- `dependencies.py` — `DBDep`, `QuestionsDBDep`, `CurrentAdmin`, `oauth2_scheme`.

### `modules/<feature>/`
Same controller → service → repository pattern as the Client backend.

| File | Responsibility |
|---|---|
| `controller.py` | `APIRouter`, route definitions, request/response models. **No business logic.** |
| `service.py` | Business logic, orchestration, calls repositories, raises domain exceptions. |
| `repository.py` | Direct MongoDB access for this module's collections. **No business logic.** |
| `schema.py` | Pydantic v2 request/response models + reusable type aliases. |
| `constants.py` *(optional)* | Collection names, magic numbers. |
| `email_templates/` *(optional)* | Jinja2 HTML templates if the module sends emails. |

The `authentication` module skips `repository.py` and `model.py` because there
is no persisted admin record — credentials live in env vars.

### `api/__init__.py`
Imports each module's `router` and combines them into a single `api_router`.

### `main.py`
Mounts `api_router` under `settings.API_V1_PREFIX` (`/api/v1`), wires CORS,
registers `AppException` and `ValidationError` handlers, and runs
`connect_to_mongo` / `close_mongo_connection` via `lifespan`.

---

## Conventions (must follow)

1. **Async everywhere.** Motor, aiosmtplib, `async def` for routes/services/repos.
2. **Pydantic v2 only.**
3. **Dependency injection for DB access.** Never call `get_database()` inside services.
4. **Auth on every non-public route via `CurrentAdmin`.** The only public route is `/auth/login` (and the refresh endpoint, which validates the refresh token itself).
5. **Raise domain exceptions from `core/exceptions.py`** — extend that file rather than raising raw `HTTPException`.
6. **ObjectId boundary handling**: services accept/return `ObjectId`; controllers/schemas use `str`.
7. **Routes return Pydantic response models**, never raw dicts (the one exception is the CSV download route, which returns a `Response` because it ships a binary blob with a `Content-Disposition` header).
8. **Secrets**: only via `config.settings.settings`. Never read `os.environ` outside `settings.py`.
9. **Admin is read-mostly.** The only writes the admin backend performs against shared collections are no-ops today. If you add a write, document why it is safe vs. the Client backend's owner of that collection.

---

## Modules at a glance

### `authentication`
Single-tenant admin login. Credentials come from env vars (`ADMIN_EMAIL`,
`ADMIN_PASSWORD` or `ADMIN_PASSWORD_HASH`). Tokens are stamped with
`role=admin` so a Client token can't be reused here.

### `stats`
A single `/stats/overview` endpoint that returns counters (users, sessions,
battles, questions) plus a 30-day signup trend padded to a continuous date axis.

### `users`
- `GET /users` — paginated list with `q` search across email/username.
- `GET /users/{user_id}` — detail + per-user session/battle counts.
- `GET /users/export.csv` — full CSV download (server flattens user + profile).
- `GET /users/emails` — emails-only payload, used by the promo composer's "select all".

### `promotional_email`
- `POST /promo-emails/preview` — renders the body through the branded template without sending.
- `POST /promo-emails/send` — bounded-concurrency dispatch to every recipient. Returns per-recipient results.

### `questions`
- `GET /questions/catalog` — subject → chapter → topic tree with counts.
- `GET /questions` — filtered list (subject, chapter, topic, question_type, difficulty, free-text). Each item already has options marked `is_correct=true` so the UI doesn't have to reconcile.
- `GET /questions/{id}` — single question with all options, correct answers, and solution.

### `contest`
- `GET /contests/default-rules` — default Markdown template the form prefills.
- `GET /contests` — every contest, newest start first, with computed status (scheduled / live / completed) and participant count.
- `POST /contests` — create. Rejects with `409 ContestOverlap` if the window intersects any existing scheduled/live contest.
- `GET /contests/{id}` — detail with the resolved question list (hydrated from bbd_db).
- `PATCH /contests/{id}` — partial update. Locked once the contest has started.
- `DELETE /contests/{id}` — only allowed before start.
- `GET /contests/{id}/participants` — leaderboard-ordered participants for the admin view.

Passage-type questions are rejected at create time — the v1 contest grader and UI only handle the leaf types (single / multi / integer / matching).

---

## Tech stack reference

- **Framework**: FastAPI
- **DB**: MongoDB Atlas via Motor (async pymongo)
- **Validation**: Pydantic v2 + `pydantic-settings`
- **Auth**: JWT (`python-jose`) + bcrypt (`passlib[bcrypt]`)
- **Email**: `aiosmtplib` + Jinja2 templates + optional Brevo HTTPS
- **Python**: 3.11+
