# Observability Setup

The Admin Console now ships with an **Observability** page that surfaces
two kinds of metrics in one place:

1. **Usage** — SolverX call counts, token totals, per-model breakdown,
   DAU/WAU/MAU. Sourced from the `usage_events` collection in Mongo,
   which the **Client backend** writes every time SolverX makes a
   Vertex AI call. Loads instantly; no GCP API in the path.
2. **Infrastructure** — Cloud Run request rate, 5xx rate, container
   instance count, p95 latency. Sourced from **GCP Cloud Monitoring**
   on the project the Client is deployed in. Cached server-side for
   60s; falls back to an empty payload with an error message if the
   API isn't reachable.

This doc covers the 3 setup steps needed: install the new pip dep,
grant the runtime SA permission to read Cloud Monitoring, and point
`GCP_PROJECT_ID` at your Client's GCP project.

---

## 1. Install the new backend dependency

```powershell
cd Admin/backend
pip install -r requirements.txt
```

`google-cloud-monitoring>=2.21.0,<3.0` is now in `requirements.txt`.

> If you skip this, the **Usage** tab still works (it doesn't touch
> GCP at all). The **Infrastructure** tab renders empty charts with a
> red banner explaining what's missing.

## 2. Set GCP env vars in `Admin/backend/.env`

```env
# The Client's GCP project — the Admin doesn't host anything in GCP
# itself, it just queries that project's Cloud Run + Vertex metrics.
GCP_PROJECT_ID=project-834fbe74-a4ec-4098-bb0
GCP_LOCATION=global
```

Restart the Admin backend (`uvicorn` auto-reload picks it up).

Leave `GCP_PROJECT_ID` blank to disable the Infrastructure tab — the
Usage tab will still work.

## 3. Grant the runtime SA `roles/monitoring.viewer`

The Admin backend's runtime identity needs permission to read the
target GCP project's metrics.

### Local dev

If you're already authenticated with `gcloud auth application-default
login` as a project owner (you are, if you set up the Client), nothing
to do — your ADC identity already has the access.

### Cloud-deployed Admin backend

The Admin backend, when deployed, runs as its own service account.
Grant that SA `roles/monitoring.viewer` on the **Client's** project:

```powershell
# The project where the Client (and its Cloud Run service) lives
$TARGET_PROJECT_ID = "project-834fbe74-a4ec-4098-bb0"

# The service account the Admin backend runs as. If you haven't created
# a dedicated SA for the admin deploy, this is the default compute SA
# of whatever project the admin is hosted in.
$ADMIN_SA = "ADMIN_RUNTIME_SA_EMAIL_HERE"

gcloud projects add-iam-policy-binding $TARGET_PROJECT_ID `
  --member="serviceAccount:$ADMIN_SA" `
  --role="roles/monitoring.viewer"
```

The Cloud Monitoring API itself doesn't need explicit enabling — it's
on by default for every GCP project that runs any service.

---

## How it all hangs together

```
   ┌────────────────────────┐                  ┌──────────────────┐
   │   Client backend       │                  │  Vertex AI       │
   │ (SolverX, port 8000)   │ ──── chat() ───▶ │  (Gemini)        │
   └───────────┬────────────┘                  └──────────────────┘
               │
               │ writes usage_event per chat()
               ▼
   ┌──────────────────────────────────────────┐
   │  MongoDB  ·  usage_events collection      │
   └──────────────────────────────────────────┘
               ▲
               │ reads aggregations (DAU, tokens, per-model, …)
               │
   ┌───────────┴────────────┐                  ┌──────────────────┐
   │   Admin backend        │                  │  GCP Cloud       │
   │ (Observability,        │ ───── 60s ─────▶ │  Monitoring API  │
   │  port 8001)            │ ◀── cached ───── │                  │
   └───────────┬────────────┘                  └──────────────────┘
               │
               │ JSON
               ▼
   ┌────────────────────────┐
   │   Admin frontend       │
   │ (Observability page,   │
   │  port 3100)            │
   └────────────────────────┘
```

The Client backend writes `usage_events`; the Admin backend only
**reads** them (per the project rule that Admin owns no indexes). The
indexes on `usage_events` live in the Client backend's
`_ensure_indexes()` and are created on Client boot.

If you need the Observability page to show data immediately, run a
couple of SolverX queries in the Client first to seed the collection.

---

## What gets surfaced

### Usage tab (Mongo, instant)

| Card | Source |
|---|---|
| Calls (24h, 7d) | `count_documents({source: "solverx", ts: >= cutoff})` |
| Tokens (24h, 7d) | `$sum: $total_tokens` |
| DAU / WAU / MAU | distinct `user_id` since cutoff |
| Error rate (24h) | `errors_24h / calls_24h` |
| 14-day SolverX line chart | day-bucketed counts, zero-padded |
| Per-model table (7d) | calls + input + output + total tokens per model |

### Infrastructure tab (Cloud Monitoring, 60s cache)

| Chart | Metric |
|---|---|
| Request rate | `run.googleapis.com/request_count` (sum) |
| 5xx error rate | `run.googleapis.com/request_count` filtered by `response_code_class=5xx` |
| Instance count | `run.googleapis.com/container/instance_count` (mean) |
| p95 latency | `run.googleapis.com/request_latencies` (95th percentile) |

Window: last 6h, 5-min alignment step. Auto-refresh every 60s while
the tab is mounted.

---

## Files added

**Admin backend** (new)
- [Admin/backend/modules/observability/__init__.py](Admin/backend/modules/observability/__init__.py)
- [Admin/backend/modules/observability/schema.py](Admin/backend/modules/observability/schema.py) — `UsageResponse`, `InfraResponse`
- [Admin/backend/modules/observability/repository.py](Admin/backend/modules/observability/repository.py) — `usage_events` Mongo aggregations (read-only)
- [Admin/backend/modules/observability/service.py](Admin/backend/modules/observability/service.py) — composes usage + infra
- [Admin/backend/modules/observability/gcp_metrics.py](Admin/backend/modules/observability/gcp_metrics.py) — Cloud Monitoring wrapper with cache + graceful degradation
- [Admin/backend/modules/observability/controller.py](Admin/backend/modules/observability/controller.py) — `/observability/usage` + `/observability/infra` routes

**Admin backend** (modified)
- [Admin/backend/config/settings.py](Admin/backend/config/settings.py) — added `GCP_PROJECT_ID` + `GCP_LOCATION`
- [Admin/backend/api/__init__.py](Admin/backend/api/__init__.py) — registered observability router
- [Admin/backend/requirements.txt](Admin/backend/requirements.txt) — added `google-cloud-monitoring`

**Admin frontend** (new)
- [Admin/frontend/src/components/common/LineChart/LineChart.jsx](Admin/frontend/src/components/common/LineChart/LineChart.jsx) — copied from Client (GCP-style crosshair hover)
- [Admin/frontend/src/components/common/LineChart/LineChart.module.css](Admin/frontend/src/components/common/LineChart/LineChart.module.css)
- [Admin/frontend/src/services/observabilityService.js](Admin/frontend/src/services/observabilityService.js)
- [Admin/frontend/src/pages/observability/Observability.jsx](Admin/frontend/src/pages/observability/Observability.jsx) — Usage + Infra tabs
- [Admin/frontend/src/pages/observability/observability.module.css](Admin/frontend/src/pages/observability/observability.module.css)

**Admin frontend** (modified)
- [Admin/frontend/src/routes/AppRoutes.jsx](Admin/frontend/src/routes/AppRoutes.jsx) — registered `/observability` route
- [Admin/frontend/src/components/layout/AdminShell.jsx](Admin/frontend/src/components/layout/AdminShell.jsx) — added Observability nav item (Activity icon)

**Client backend** (kept from earlier work — required to populate `usage_events`)
- [Client/backend/config/database.py](Client/backend/config/database.py) — `usage_events` indexes
- [Client/backend/core/usage_events.py](Client/backend/core/usage_events.py) — `record_event` + `usage_context`
- [Client/backend/modules/solverx/llm.py](Client/backend/modules/solverx/llm.py) — instrumented `chat_json` + `chat_stream`
- [Client/backend/modules/solverx/service.py](Client/backend/modules/solverx/service.py) — wraps `stream_solve` / `stream_theory` in `usage_context`

---

## Smoke test

1. Start the Client backend (`uvicorn main:app --reload --port 8000`).
2. Start the Admin backend (`uvicorn main:app --reload --port 8001`).
3. Start the Admin frontend (`npm run dev` from `Admin/frontend`).
4. Open http://localhost:3100, log in, click **Observability**.
5. **Usage tab** should load — most numbers are 0 on a fresh DB.
6. From the Client side, run a couple of SolverX queries to seed
   events.
7. Refresh the Admin Observability page — Usage numbers should be
   non-zero, model table populated, 14-day chart has a data point.
8. Switch to **Infrastructure** tab — if Cloud Monitoring is wired
   correctly you'll see four charts; otherwise a red banner explains
   what's missing (most likely the pip dep or the IAM grant).
