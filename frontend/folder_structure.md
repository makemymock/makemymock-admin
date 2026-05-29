# Admin Frontend Folder Structure

React (Vite) admin console for **MakeMyMock**. Talks to the Admin FastAPI backend
over HTTP, uses **CSS Modules** for styling, **Axios** for HTTP, **React Router
DOM** for routing, and **React hooks** for state. Same conventions as the
Client frontend — no Tailwind, no Bootstrap, no MUI, no Redux.

---

## Top-level layout

```
frontend/
├── public/                      # (empty by default — drop favicons here)
├── src/
│   ├── components/
│   │   ├── common/              # Generic primitives (Button, InputField, StatCard, …)
│   │   ├── layout/              # AdminShell (sidebar + main outlet)
│   │   └── questions/           # Question-specific render components
│   ├── pages/                   # One folder per route, owns its own .module.css
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── users/
│   │   ├── email/
│   │   ├── questions/
│   │   └── contests/            # Contests.jsx (list) + ContestForm.jsx
│   │                             #   (create / edit + question picker)
│   ├── routes/
│   │   ├── AppRoutes.jsx
│   │   └── ProtectedRoute.jsx
│   ├── services/                # All network I/O — components NEVER call axios directly
│   │   ├── axiosInstance.js
│   │   ├── authService.js
│   │   ├── statsService.js
│   │   ├── userService.js
│   │   ├── emailService.js
│   │   ├── questionService.js
│   │   └── contestService.js
│   ├── utils/
│   │   ├── token.js             # localStorage wrapper (`mmma_*` keys)
│   │   └── validators.js
│   ├── styles/global.css        # CSS variables (colors, spacing, radii)
│   ├── App.jsx                  # BrowserRouter + AppRoutes
│   ├── App.css                  # Base resets + focus styles
│   ├── index.css                # Body defaults
│   ├── config.js                # `API_BASE_URL` from VITE_API_BASE_URL
│   └── main.jsx                 # ReactDOM root
├── index.html
├── vite.config.js
├── eslint.config.js
├── .env                         # VITE_API_BASE_URL (gitignored)
├── .env.example
└── package.json
```

---

## Layer responsibilities

### `services/`
All HTTP traffic. **Components never import axios directly.**

- `axiosInstance.js` — single configured client. Reads `VITE_API_BASE_URL`,
  attaches `Authorization: Bearer <token>` from `tokenStorage`, single-flight
  refresh on 401. The CSV download uses raw `fetch()` from `userService.js`
  because it streams the body straight to disk.
- One service per backend domain (`auth`, `stats`, `users`, `email`, `questions`).

### `utils/`
Pure helpers — no React, no axios.

- `token.js` — `tokenStorage` wrapping localStorage. Keys are namespaced
  `mmma_*` so they cannot collide with the Client app (`mmm_*`) when the
  two frontends share a dev origin.
- `validators.js` — validators return `''` on success, an error string on
  failure. `parseEmailListInput` accepts commas, semicolons, whitespace,
  or newlines as separators.

### `components/common/`
Reusable, presentational primitives. Receive everything via props.

| Component | Purpose |
|---|---|
| `Button` | CTA. Variants: `primary`, `outline`, `ghost`, `danger`. |
| `InputField` | Labeled input with error slot and right adornment. |
| `SelectField` | Labeled dropdown. Empty option supported. |
| `Loader` | Spinner. `fullscreen` prop for overlay mode. |
| `ErrorMessage` | Tinted error pill. |
| `StatCard` | Headline + value + sub-label for the dashboard. |
| `MarkdownText` | Renders Markdown + GFM + KaTeX. Used by the email composer body + preview, and by question solutions. |

### `components/layout/`
- `AdminShell` — sidebar nav + `<Outlet>` for protected pages. Holds the
  brand mark, sidebar nav links, user chip, and sign-out button.

### `components/questions/`
- `QuestionCard` — renders one question with options, integer answer,
  matching columns, passage block, sub-questions, and solution. Correct
  options are tinted green.

### `pages/<route>/`
One folder per route, owns its own CSS module.

| Page | Route | Responsibilities |
|---|---|---|
| `Login` | `/login` | Email + password → `authService.login` → `/dashboard`. |
| `Dashboard` | `/dashboard` *(protected)* | Calls `/stats/overview`. Stat cards + 30-day signup chart + target-exam breakdown. |
| `Users` | `/users` *(protected)* | Paginated list, search, **Download CSV** (one-click). |
| `UserDetail` | `/users/:userId` *(protected)* | Single user — profile, session/battle counts. |
| `EmailComposer` | `/email` *(protected)* | Subject + body + recipients list with **Load all users**, live iframe preview, dispatch. |
| `Questions` | `/questions` *(protected)* | Subject → chapter → topic dropdowns, type + difficulty filters, free-text search. Renders each question with correct answers highlighted in green. |
| `Contests` | `/contests` *(protected)* | List of every scheduled / live / completed contest with status badges + participant count. Edit and delete actions; delete is hidden once the contest starts. |
| `ContestForm` | `/contests/new`, `/contests/:id` *(protected)* | Create + edit. Fields: title, description, start datetime (local), duration, marking scheme, rules markdown (prefilled from `/contests/default-rules`, with live `{question_count}` / `{duration_minutes}` / `{marks_*}` token substitution). Embedded question picker reuses the catalog filters from `questionService` and filters passages out. Right pane shows running summary + selected list with remove buttons. |

### `routes/`
- `AppRoutes.jsx` — central `<Routes>` block. All protected pages share an
  `AdminShell` layout via a parent `<Route>` that wraps them in
  `<ProtectedRoute><AdminShell/></ProtectedRoute>`.
- `ProtectedRoute.jsx` — bounces unauth users to `/login` and stashes the
  original location in `state.from`.

---

## Conventions (must follow)

1. **No direct `axios.*` calls in components.** Always import from `services/`.
2. **No direct `localStorage.*` calls.** Always go through `tokenStorage`.
3. **No inline styles, no global CSS for pages.** Use `*.module.css`.
4. **No Tailwind / Bootstrap / MUI / Redux.** State is `useState`/`useReducer`.
5. **Mobile-first responsive CSS.** Default styles target mobile; scale up with `@media`.
6. **Form pattern**: one `form` (or several `useState`s), one `errors` object, one top-level `formError` for API failures. Validate on blur + submit, clear field error on next change.
7. **Validators return strings, not booleans.** Empty string = valid.
8. **Page components default-exported.** Reusable components also default-exported.
9. **File extensions**: `.jsx` for files with JSX; `.js` for plain JS.
10. **Env vars** must start with `VITE_` and live in both `.env` and `.env.example`. Read them only inside `services/` via `import.meta.env.VITE_*` (or through `config.js`).
11. **Routes are added in one place** — `routes/AppRoutes.jsx`.

---

## Auth + token flow

1. Login → `authService.login` → tokens persisted via `tokenStorage.setSession`.
2. Authenticated request → interceptor attaches `Authorization: Bearer <token>`.
3. 401 → single-flight `/auth/refresh-token`. On failure, storage is cleared and the browser is sent back to `/login`.
4. Logout → `tokenStorage.clear()` + `navigate('/login')`. Stateless JWT, no server call.

Token keys in localStorage: `mmma_access_token`, `mmma_refresh_token`, `mmma_admin_user`.

---

## Tech stack reference

- **Framework**: React 19 (Vite 8 + `@vitejs/plugin-react`)
- **Routing**: react-router-dom v6
- **HTTP**: axios (single instance + interceptors) + native `fetch` for CSV
- **Styling**: CSS Modules (no preprocessor) + CSS custom properties in `styles/global.css`
- **State**: React hooks only
