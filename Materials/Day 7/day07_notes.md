# Day 7 — Notes
## Week 2, Friday: Full-Stack Integration, Axios API Integration, FastAPI & React CORS Setup, MUI DataGrid & Tables, React Context API

---

## Executive Summary

Every prior frontend day (Day 6) and every prior backend day (Days
1–5) built in isolation, correctly, but never once talked to each
other. Today they finally do. CORS middleware gives the browser
explicit permission to let JavaScript on `localhost:5173` read
responses from `127.0.0.1:8000`; Axios becomes the one, shared way the
frontend actually makes that call; React's Context API becomes the
one, shared place "who's logged in, and as what role" lives; and MUI's
`DataGrid` replaces Day 6's card grid for genuinely tabular data. None
of these four pieces work in isolation from each other today — CORS
is what makes Axios's calls possible at all; Axios is what Context's
`login()` function actually uses; Context is what `DataGrid`'s data
fetch authenticates with.

This is also the day this course's two running business questions
finally converge. Business Question #1 (Low Battery Alert) and
Business Question #2 (Co-Location Discrepancy) have each now been
answered across every tool this course has introduced — Python, raw
SQL, an async ORM, a FastAPI endpoint, a mock-data React component,
and, as of today, a fully wired, authenticated, real-data table. This
isn't a coincidence or a stretch — it was the specific, deliberate
throughline planned since Day 1, and today is where it actually lands.

---

## Deep Dive: Full-Stack Integration

- **Two servers, two terminals, for the first time.** Every previous
  day had exactly one thing running at a time — a script, or a single
  server. Today genuinely requires both the FastAPI backend
  (`fastapi dev`, port 8000) and the Vite dev server (`npm run dev`,
  port 5173) running *simultaneously*, in separate terminal
  processes, because the frontend's every meaningful action depends on
  the backend being reachable. This is worth naming explicitly as a
  new operational reality, not just a footnote — debugging "it's not
  working" from here forward always starts with confirming *both*
  processes are actually still running.
- **The snake_case/camelCase reconciliation.** Day 6's `mockRobots`
  used JavaScript-convention `camelCase` keys
  (`batteryLevel`) as a reasonable guess at what a "clean" data shape
  should look like. The real API, built entirely in Python, returns
  `snake_case` (`battery_level`) — `RobotRead`'s actual field names,
  completely unmodified by Axios along the way. Today's
  `RobotDataGrid` column definitions had to be written against the
  *real* shape, not the guessed one. This is a genuine, common
  real-world integration lesson: two independently-built layers,
  each internally consistent, don't automatically agree with each
  other the moment they're connected — reconciling exactly this kind
  of mismatch is a large part of what "integration" actually means in
  practice, not just wiring two working things together and expecting
  it to be seamless.
- **The props-driven architecture from Day 6 paid off exactly as
  designed — with one honest nuance.** `RobotCard.jsx` and
  `RobotList.jsx` were not modified today at all, fulfilling Day 6's
  prediction to the letter. What *did* change is which component
  `Dashboard` chooses to render: `RobotDataGrid` instead of
  `RobotList`, since a full tabular fleet view benefits more from
  `DataGrid`'s sorting/filtering than a card grid does. The Card
  components aren't obsolete — they remain complete, working, and
  available for a future context better suited to them (a single
  robot's detail view, for instance) — but today's top-level page
  composition chose the newer tool for this particular job.

---

## Deep Dive: Axios API Integration

- **`axios.create({ baseURL })`** builds one reusable, pre-configured
  client, rather than every component constructing its own request
  settings from scratch — directly comparable to `app/database.py`'s
  single shared `engine` on the backend.
- **Interceptors as a cross-cutting concern, centralized.** The
  request interceptor in `api/client.js` runs on *every* outgoing
  request through `apiClient`, attaching the current JWT (read from
  `localStorage`) automatically. No component calling
  `apiClient.get(...)` needs to remember to attach a token by hand.
  This is the frontend mirror of Day 5's `Depends(get_db)` on the
  backend — a concern that touches nearly every request, handled in
  exactly one place instead of repeated at every call site.
- **Axios defaults to JSON, which is why login is an explicit
  exception.** Every `apiClient.get`/`apiClient.post` call this course
  writes assumes a JSON body by default — except `AuthContext`'s
  `login()`, which explicitly overrides `Content-Type` to
  `application/x-www-form-urlencoded` and builds the body with
  `URLSearchParams`. This is the frontend's half of Day 5's own
  deliberate exception (`OAuth2PasswordRequestForm` expecting form
  data, not JSON) — the same spec requirement, now visible on both
  ends of the same request.

---

## Deep Dive: FastAPI & React CORS Setup

- **CORS is a browser-enforced rule, not a network or server-level
  one.** The request itself reaches FastAPI either way — CORS only
  controls whether the *browser* subsequently allows the calling
  JavaScript to read that response. This is precisely why `curl`,
  Postman, and `/docs` itself never encountered this issue in Days 4
  and 5: `/docs` is served by FastAPI, so it's calling its own origin;
  `curl`/Postman aren't browsers, so the same-origin policy simply
  doesn't apply to them at all.
- **`allow_origins`** is an explicit allow-list of exactly which
  origins are trusted — today, only Vite's dev server address.
  **`allow_credentials=True`** is required for any request carrying an
  `Authorization` header cross-origin — and the CORS specification
  explicitly **forbids** pairing this with a wildcard `allow_origins=["*"]`;
  browsers reject that specific combination outright, which is why the
  real, specific origin is listed instead, even for local development.
- **Preflight `OPTIONS` requests** are sent automatically by the
  browser, invisibly, ahead of certain "non-simple" requests (a JSON
  body, a custom header like `Authorization`) — essentially the
  browser asking permission before actually sending the real request.
  `CORSMiddleware` answers these automatically; RoboPulse's own route
  handlers never see or need to know about them.

---

## Deep Dive: MUI DataGrid & Tables

- **`DataGrid` requires a stable `id` per row by default**, and
  `getRowId` is the escape hatch when a dataset's natural identifier
  has a different name (`mission_id`, in Phase B's case, rather than a
  literal `id` field). This is a direct echo of Day 6's `key` prop
  lesson — both React's reconciliation and `DataGrid`'s own internal
  row-tracking need a genuinely stable, unique identifier per item,
  not just *a* value that happens to look distinct today.
- **Card grid vs. `DataGrid` is a UX decision, not a strict
  progression.** A card layout suits a small, glanceable set of items
  or a rich single-item view; a data table suits a larger, sortable,
  filterable, genuinely tabular dataset. Today's course deliberately
  keeps both tools available in the codebase rather than treating one
  as simply "the newer, better version" of the other.
- **Client-side vs. server-side filtering — a real, sizeable
  tradeoff.** `DataGrid` ships with built-in client-side sorting and
  filtering on whatever data is already loaded. Today's Phase B
  challenge deliberately went the *other* direction — re-fetching from
  the server on every filter change — specifically to demonstrate that
  choice explicitly rather than defaulting to whichever one happens to
  be built in. For four seeded rows, either approach is instant and
  invisible to a user; for a fleet with tens of thousands of missions,
  loading everything up front to filter client-side would be
  genuinely wasteful, and server-side filtering (today's approach)
  becomes the only reasonable option.

---

## Deep Dive: React Context API

- **The problem Context solves.** Without it, "is the user logged in,
  and as whom" would need to be threaded down as a prop through every
  intermediate component between `App` and whatever deeply nested
  component needs to know — a pattern commonly called "prop drilling."
  `createContext` + a `Provider` + `useContext` lets any component
  anywhere inside the provider ask directly, without every layer in
  between needing to know or care that the data is passing through it.
- **`ThemeProvider`, revisited.** Day 6 used MUI's `ThemeProvider`
  without naming the mechanism behind it. Today's `AuthContext`
  is the exact same underlying React feature, used directly, by name,
  for RoboPulse's own application data rather than a third-party
  library's internal styling state. Recognizing that connection is the
  point — Context wasn't a brand-new concept today, just a newly
  *named and directly authored* one.
- **The custom `useAuth()` hook pattern.** Wrapping `useContext(AuthContext)`
  in a small custom hook (with a thrown error if used outside a
  `Provider`) is idiomatic, not mandatory — it centralizes a safety
  check in one place and gives every consuming component a cleaner
  call site (`useAuth()` instead of `useContext(AuthContext)` repeated
  everywhere).
- **Stateless sessions, now visible on the frontend too.** Day 5's
  notes described JWT-based sessions as stateless on the *backend* —
  no server-side memory of who's logged in. Today's `AuthContext`
  shows the frontend-side consequence directly: "being logged in" is
  entirely reconstructed from whatever's sitting in `localStorage` at
  page load (`useState`'s lazy initializer), not fetched from
  anywhere. A page refresh doesn't ask the server "am I still logged
  in" — it simply re-decodes whatever token is already present
  locally.
- **Client-side role checks are UX, not security — worth restating
  plainly.** `AuthContext`'s decoded `user.role` controls what the UI
  *shows*; it enforces nothing. A user could edit that value directly
  in browser dev tools and the backend's `require_role(...)`
  dependency (Day 5) would remain completely unaffected — it's still
  the only real enforcement boundary in the entire system.

---

## Architectural Analysis

Today is the payoff for a sequence of deliberate architectural bets
made across the previous six days, and it's worth tracing the whole
chain explicitly: Day 4 separated `schemas/` from `models/` so an
API's contract could differ from its storage shape; Day 5 proved that
split's value by keeping `hashed_password` off of every response; Day
6 built every frontend component to accept data purely via props,
specifically so its data *source* could change later without touching
the components themselves. Today is where that last bet gets cashed
in: `RobotCard`/`RobotList`/`DiscrepancyCard`/`DiscrepancyList` remain
completely untouched, while an entirely new data-fetching layer
(`RobotDataGrid`, `DiscrepancyDataGrid`) was added alongside them,
free to define its own shape and its own tool (`DataGrid` instead of
cards) without any conflict.

The convergence of both running business questions today is worth
treating as a milestone, not just an incidental fact. Every tool
introduced since Day 1 was deliberately exercised against the *same*
two questions, on the *same* seeded data, producing the *same*
answers every time — not because RoboPulse only has two interesting
questions to ask, but because holding the business logic constant
while changing only the tool is what let each new day's lesson be
about the tool, not about re-learning what a "co-location discrepancy"
even means. From here forward, both questions are simply part of a
working application — there's no more "next layer" left to
demonstrate for either one specifically, though the application itself
will keep growing around them (RBAC-aware UI, cloud deployment, and
polish are all still ahead).

---

## Common Pitfalls & Anti-Patterns

- **Forgetting the CORS middleware, or misconfiguring it.** The
  request still reaches FastAPI (visible in the backend's own
  terminal logs) but the browser blocks the *response* — a genuinely
  confusing symptom for anyone expecting a request to either
  completely succeed or completely fail, since from the backend's
  point of view, nothing went wrong at all.
- **`allow_origins=["*"]` combined with `allow_credentials=True`.**
  Forbidden by the CORS spec itself; browsers reject the combination
  outright rather than silently ignoring one setting.
- **Creating a second Axios instance** instead of reusing `apiClient`
  — bypasses the shared request interceptor entirely, so that
  particular call silently goes out with no `Authorization` header
  attached, even while logged in.
- **An empty or incorrect `useEffect` dependency array.** Leaving it
  as `[]` when a fetch genuinely needs to respond to a changing value
  (Phase B's `priority` filter) means the effect never re-runs — no
  error, just a UI that silently stops responding to user input.
  Conversely, *omitting* the dependency array entirely (not even an
  empty `[]`) makes an effect re-run after **every** render — combined
  with a `setState` call inside that effect, this produces an infinite
  fetch loop, visible as a continuously growing stream of requests in
  the Network tab.
- **Hardcoding the `localStorage` key name in more than one place.**
  `'roboPulseToken'` appears both in `api/client.js`'s interceptor and
  `AuthContext.jsx`'s `login`/`logout` functions — a real DRY
  violation worth flagging: a typo in either location silently breaks
  authentication with no obvious error pointing at the actual cause. A
  small shared constant (exported from one module, imported by both)
  would remove this risk entirely — worth raising as an improvement a
  student might reasonably suggest.
- **Treating the decoded JWT role as authoritative for anything beyond
  UI display.** Restated from the Deep Dive above because it's
  important enough to repeat: real authorization only ever happens
  server-side, via Day 5's `require_role(...)`.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| Browser console: `has been blocked by CORS policy` | `CORSMiddleware` missing from `app/main.py`, misconfigured, or the backend wasn't restarted after adding it | Confirm the middleware block matches Step 1 exactly; restart `fastapi dev` if needed |
| Axios error: `Network Error` (no HTTP status at all) | The FastAPI backend isn't running, or `baseURL` in `api/client.js` points at the wrong port | Confirm the backend terminal shows `fastapi dev` still running; confirm `baseURL: 'http://127.0.0.1:8000'` matches |
| `401 Unauthorized` on a request made while genuinely logged in | The request interceptor isn't attaching a token — often a `localStorage` key name mismatch between `client.js` and `AuthContext.jsx`, or the token has expired (Day 5's 30-minute `exp`) | Check `localStorage.getItem('roboPulseToken')` directly in the browser console to confirm a token is present and matches what the interceptor reads; log in again if expired |
| Network tab shows the same request firing continuously, over and over | `useEffect`'s dependency array was omitted entirely (not even `[]`), and a `setState` call inside the effect is triggering an infinite re-render/re-fetch loop | Add the dependency array back — `[]` for "run once," or `[specificValue]` to re-run only when that value changes |
| Changing the priority dropdown (or any filter) does nothing visible | `useEffect`'s dependency array doesn't include the piece of state the fetch depends on | Add the missing value to the dependency array |
| `DataGrid` renders blank, or throws an error mentioning `id` | No `id` field exists on the row data, and `getRowId` wasn't supplied | Add `getRowId={(row) => row.<actual-unique-field>}` |
| Login form submits successfully (network tab shows `200`), but the page doesn't change to the dashboard | `setToken(...)` was never called inside `login()`, or `AppContent` isn't correctly reading `isAuthenticated` from context | Confirm `login()` calls both `localStorage.setItem(...)` and `setToken(...)`; confirm `AppContent` is rendered inside `<AuthProvider>` |
| `Uncaught SyntaxError` or similar thrown from inside `decodeToken` | A malformed or corrupted value is sitting in `localStorage` under the token's key (often leftover from earlier manual testing) | `localStorage.clear()` in the browser console, then log in again |
| `Objects are not valid as a React child` involving the `user` object | JSX tried to render `{user}` directly somewhere instead of a specific field like `{user.sub}` | Access the specific property needed, not the whole decoded object |
| CORS works for `GET` requests but fails specifically on `POST`/`PATCH` | `allow_methods` was restricted to a subset that doesn't include the method being used | Confirm `allow_methods=["*"]` (or an explicit list that includes every verb actually used) |

---
*RoboPulse Fleet Command Center — Day 7 of 13*
