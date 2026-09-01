# Day 10 — Notes
## Advanced FastAPI, Database Session Dependencies, Error Handling, API Endpoint Unit Testing

---

## Executive Summary

Every prior day added something a user could see or touch. Today adds
nothing visible at all — it adds **proof**. `pytest` now exercises the
real, complete, RBAC-protected application end-to-end: real
authentication, real role checks, real business logic, all verified by
machine-checked assertions instead of a human reading `/docs` output
and judging it correct. Custom exception handlers close a gap left
open since Day 4, translating a raw database-level failure into a
clean, predictable HTTP response instead of a leaked stack trace.

This topic set was deliberately taught out of its original
chronological position — the curriculum originally placed it right
after Day 4's first bare endpoints, before RBAC, before the frontend,
before deployment existed. Teaching it now, against the finished
application, means every test written today exercises something real
and load-bearing (an actual role check, an actual business rule)
rather than a placeholder CRUD operation with nothing yet at stake.

Today was also, true to form for this course's AWS-adjacent days,
genuinely eventful operationally — three real, instructive bugs
(an exception handler placed before its own `app` object existed, a
leftover Lambda-packaging folder confusing `pytest`'s test discovery,
and a classic async-SQLAlchemy-plus-`pytest-asyncio` event-loop
mismatch) are documented in full below, each a common, transferable
lesson well beyond RoboPulse itself.

---

## Deep Dive: Advanced FastAPI — Dependency Overrides

- **The single most important new mechanism today.**
  `app.dependency_overrides[get_db] = override_get_db` tells FastAPI:
  for the life of this override, any endpoint asking for
  `Depends(get_db)` receives this substitute instead. Every router
  written since Day 4 — `robots.py`, `missions.py`, `auth.py` — is
  completely unaware this happened; each still just writes `db:
  AsyncSession = Depends(get_db)` and gets handed a test session
  pointed at `robopulse_test` instead of the real
  `AsyncSessionLocal()` pointed at `robopulse_dev`.
- **This is a direct payoff of an architectural decision made five
  days ago.** Day 4's choice to centralize database access behind a
  single, named dependency — rather than each endpoint constructing
  its own session inline — is *specifically* what makes today's entire
  testing setup possible in a handful of lines. A codebase where every
  route opened its own database connection independently would have no
  single seam to override at all; testing it would require touching
  every route individually.
- **`app.dependency_overrides.clear()` matters as much as setting the
  override.** Overrides are global, mutable state on the `app` object
  itself — left in place, they'd silently affect any test (or, worse,
  any accidental production usage) running afterward. Clearing it
  after each test is what keeps tests isolated from each other.

---

## Deep Dive: Database Session Dependencies

- **A dedicated test database, never `robopulse_dev` or RDS.** Tests
  create and delete rows freely — running them against real data risks
  corrupting it, and running them against a shared database makes
  tests interfere with each other across runs. `robopulse_test` is
  freely, cheaply recreatable at any time.
- **`create_all`/`drop_all` per test, for genuine isolation.**
  `db_session`'s fixture builds every table fresh before each test
  function and tears them down after — no test can be affected by
  data another test left behind, at the cost of some speed (the
  Research Prompts ask what changes if this were session-scoped
  instead).
- **The event-loop-per-test trap, and why `NullPool` fixes it.**
  `pytest-asyncio`'s default (`asyncio_mode = auto`) creates a **new
  `asyncio` event loop for every single test function**. The test
  engine, though, is created once, at module import time — its
  connection pool opens real connections tied to whichever event loop
  happens to be running at that moment. The first test works
  correctly; the instant it finishes, its event loop closes, and every
  pooled connection tied to that now-dead loop becomes silently
  unusable. Every subsequent test inherits broken connections,
  surfacing as `InterfaceError` or an opaque `AttributeError:
  'NoneType' object has no attribute 'send'` — neither of which
  obviously points back at "wrong event loop." `poolclass=NullPool`
  disables pooling for the test engine specifically, so every checkout
  opens a genuinely fresh connection instead of reusing a possibly-dead
  one. This is SQLAlchemy's own documented recommendation for async
  test suites structured this way — not a RoboPulse-specific
  workaround, and a near-guaranteed failure (not an edge case) for
  *any* test suite built this way without it.

---

## Deep Dive: Error Handling

- **The third layer of Day 4's validation story, finally connected.**
  `battery_level` has been checked three separate times since Day 1:
  Pydantic's `Field(ge=0, le=100)` at the API boundary, PostgreSQL's
  `CHECK` constraint at the database, and a plain Python clamp before
  that. What was missing until today was the bridge back to the
  client when a constraint violation *does* reach the database layer —
  without `integrity_error_handler`, a genuine violation (a duplicate
  `serial_number`, `unique=True` since Day 3) surfaced as a raw,
  unhandled `500` with a Python traceback attached.
- **`IntegrityError` → `409 Conflict`**, a semantically correct status
  code for "this request conflicts with the resource's current
  state," matching the same instinct as Day 4's `HTTPException` usage
  — applied here to an error class FastAPI has no built-in translation
  for.
- **A catch-all `Exception` handler is a security control, not just
  tidiness.** Any genuinely unexpected failure — a real bug, not a
  known error condition — now returns a consistent JSON shape instead
  of whatever internal detail (file paths, variable names, library
  internals) a raw stack trace might otherwise leak to a client.

---

## Deep Dive: API Endpoint Unit Testing

- **`httpx.AsyncClient` + `ASGITransport`, not `requests` or a running
  server.** This talks to the FastAPI app directly over its real ASGI
  interface — the same interface Uvicorn and Day 9's `Mangum` adapter
  both speak — with no actual network socket or running process
  involved. Tests run fast and don't depend on anything external being
  up.
- **`auth_header()` bypasses the real login endpoint for most tests,
  deliberately.** Generating a JWT directly via `create_access_token`
  (the same function `POST /auth/token` uses internally) is faster and
  more isolated than logging in fresh for every single test — but Day
  10's Step 5 still tests the *real* login endpoint at least once, so
  the actual mechanism every shortcut assumes works is never left
  completely unverified itself.
- **Testing failure paths is not optional coverage — it's a
  first-class category.** `test_login_fails_with_wrong_password` and
  `test_nonexistent_mission_returns_404` don't test that the app does
  something impressive; they test that it fails in the *specific,
  sanctioned* way, rather than crashing or behaving unpredictably.
  Confirming a system fails correctly is exactly as important as
  confirming it succeeds correctly.
- **Business Question #1, finally machine-verified.** Every prior
  day's version of the low-battery-alert question — Python, SQL, ORM,
  FastAPI endpoint, mock React component, deployed React component —
  was confirmed correct by a human reading output. `test_low_battery_filter`'s
  `assert "LOW-01" in serials` is the first version of this course's
  central running example that will catch a future regression
  automatically, without anyone needing to remember to manually
  re-check it.

---

## Architectural Analysis

Today completes a throughline that's run since Day 4: **centralizing
a cross-cutting concern behind a single, named seam pays off
repeatedly, in ways not fully visible at the moment the decision is
made.** `Depends(get_db)` was introduced purely to avoid repeating
session-opening code across endpoints. Day 5 reused that exact seam to
add authentication (`Depends(get_current_user)`) without touching a
single route. Today reuses the *same* seam a third time, to make
comprehensive automated testing possible with almost no additional
plumbing. None of these three payoffs were the original stated reason
for the pattern — each is a genuine, compounding dividend from having
established it once, correctly, five days before today's need
appeared at all.

Today also closes a loop this course opened explicitly on Days 8 and
9: **"the command didn't error" is never sufficient confirmation on
its own.** Days 8 and 9 demonstrated that lesson through failure —
things that looked successful but silently weren't. Today demonstrates
its constructive counterpart: automated tests are what *deliberate*
verification looks like as a durable, repeatable artifact, rather than
a one-time manual check performed once and then trusted indefinitely.
Every business rule this course has built — RBAC's role boundaries,
Business Question #1's threshold, the referential integrity Day 2's
foreign keys established — now has at least one assertion that will
fail loudly the moment it's ever accidentally broken, rather than
depending on someone happening to notice.

---

## Common Pitfalls & Anti-Patterns

- **Placing `@app.exception_handler(...)` before the line `app =
  FastAPI(...)`.** The decorator needs `app` to already exist —
  placed too early (e.g., near the top of the file alongside imports),
  it fails immediately with `NameError: name 'app' is not defined`,
  before any test or request is even attempted.
- **`pytest`'s default test discovery scanning the entire project,
  including irrelevant directories.** If Day 9 was completed first,
  `backend\package\` (the Lambda packaging staging folder) contains a
  full, unpacked copy of every dependency's own source — including
  files some of those packages name `test_*.py` as part of their own
  normal internal structure. `pytest` happily (and incorrectly) treats
  these as project tests, and can produce a confusing `import file
  mismatch` error when an identically-named file also exists in
  `.venv\`. `testpaths = tests` in `pytest.ini` restricts collection
  to exactly the one folder that should ever contain tests.
- **A module-scoped async engine used across `pytest-asyncio`'s
  per-test event loops, without `NullPool`.** A near-guaranteed
  failure after the very first test, not a rare edge case — see the
  Database Session Dependencies deep dive above for the full
  mechanism.
- **Seeding only one side of a two-foreign-key relationship.**
  `Mission` requires both a `robot_id` and an `operator_id` — omitting
  either produces an `IntegrityError` during fixture setup, which
  today's own `integrity_error_handler` can mask as a clean `409`
  rather than an obvious crash if the mistake happens mid-request
  rather than at fixture-creation time.
- **Confusing `MissionRead`'s `id` field with `DiscrepancyRead`'s
  `mission_id` field.** Two different schemas describe "a mission" for
  two different endpoints, built days apart — reading the wrong one
  produces a `KeyError` unrelated to whatever the test was actually
  trying to verify.
- **A test database name that doesn't match what `conftest.py`'s
  fallback expects.** Easy to hit if a database was created under a
  different name during setup — surfaces as
  `InvalidCatalogNameError`, the same symptom (and same underlying
  cause) as Day 8's original RDS "Initial database name" gotcha,
  reappearing here in a purely local context.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `NameError: name 'app' is not defined` while loading `conftest.py` / collecting tests | An `@app.exception_handler(...)` was placed before `app = FastAPI(...)` in `main.py` | Move the exception handler functions to after `app = FastAPI(...)` (alongside the existing `app.add_middleware`/`app.include_router` lines) |
| `import file mismatch` involving a file inside `backend\package\...` (e.g. `annotated_types/test_cases.py`) | `pytest`'s default discovery scanned the entire project, including Day 9's leftover Lambda packaging folder, and found a same-named file colliding with one in `.venv\` | Add `testpaths = tests` to `pytest.ini` so collection never looks outside the `tests\` folder |
| `asyncpg.exceptions.InvalidCatalogNameError: database "..." does not exist` when running tests | The test database either was never created, or was created under a different name than `conftest.py`'s `TEST_DATABASE_URL` expects | `psql -U postgres -c "CREATE DATABASE robopulse_test;"`, or set `$env:TEST_DATABASE_URL` to match whatever name was actually used |
| First test passes; every test after it fails with `InterfaceError` or `AttributeError: 'NoneType' object has no attribute 'send'` | The test engine's connection pool holds connections tied to a `pytest-asyncio` event loop that closed after the first test | Add `poolclass=NullPool` to `create_async_engine(...)` for the test engine |
| An unexpected `409` appears while writing a new fixture, with no obvious cause | A required foreign key wasn't seeded (e.g. a `Mission` created without both a `Robot` and an `Operator` already existing) | Check that every foreign-key-referenced row exists before the row that depends on it, in dependency order |
| `KeyError` reading a test's response body (e.g. `response.json()["mission_id"]`) | Wrong schema's field name assumed — `MissionRead` uses `id`; `DiscrepancyRead` (a different endpoint's schema) uses `mission_id` | Check which endpoint's schema is actually in play and use its real field names |
| A test using `client.post(..., json={...})` against `/auth/token` fails unexpectedly | `/auth/token` is the one endpoint in the whole app requiring form-encoded data (`data={...}`), not JSON, per Day 5's `OAuth2PasswordRequestForm` | Use `data=`, not `json=`, for this one specific endpoint |

---
*RoboPulse Fleet Command Center*
