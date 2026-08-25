# Day 4 — Notes
## Week 2, Monday: FastAPI Setup & Routes, Path & Query Parameters, Request Bodies & Validation, Dependency Injection, OpenAPI Docs

---

## Executive Summary

Days 1–3 built RoboPulse's data layer from the inside out — plain
Python, then raw SQL, then an async ORM — but every single piece of
that work only ever ran from a terminal, one script invocation at a
time. Today the project became reachable over HTTP for the first
time. FastAPI sits directly on top of Day 3's async SQLAlchemy models,
translating incoming HTTP requests into the exact same `select()` /
`AsyncSession` calls those standalone scripts were already making by
hand — the ORM layer didn't change today, only who's driving it.

Five ideas arrived together, and they're genuinely inseparable in
FastAPI's design: **routes** are just Python functions decorated with
an HTTP verb and path; **path and query parameters** are inferred
automatically from a function's signature, no annotations required;
**request bodies** are validated by Pydantic before your code ever
runs; **dependency injection** (`Depends(get_db)`) is how a database
session (or, starting Day 5, an authenticated user) gets handed to an
endpoint without that endpoint constructing it itself; and **OpenAPI
docs** are not a separate thing you write — they're a live reflection
of the same type hints and Pydantic schemas already written for the
other four reasons.

Business Question #1 (Low Battery Alert) and Business Question #2
(Co-Location Discrepancy) were both answered for a fourth time today —
now as real HTTP endpoints (`GET /robots?max_battery=20` and
`GET /missions/discrepancies`) — continuing the throughline from every
prior day: same question, same seeded data, same single-row or
two-row answers, one more layer of tooling on top.

---

## Deep Dive: FastAPI Setup & Routes

- **ASGI vs. WSGI.** Flask and Django classically run on WSGI (Web
  Server Gateway Interface) — synchronous, one request per worker
  thread at a time. FastAPI runs on **ASGI** (Asynchronous Server
  Gateway Interface), which is what actually makes it possible for an
  endpoint to `await` Day 3's `AsyncSession` mid-request without
  blocking the whole server. This is also *why* Day 3 deliberately
  taught async SQLAlchemy's gotchas a full workday before FastAPI
  showed up — the database layer FastAPI leans on was already
  async-ready.
- **`fastapi[standard]`** bundles Uvicorn (the actual ASGI server
  process that runs your app), the `fastapi` CLI, and a few supporting
  libraries (`python-multipart`, `httpx`) in one install — comparable
  to how a single Spring Boot starter dependency pulls in an embedded
  Tomcat server plus everything else needed to run a web app.
- **`APIRouter`** lets related endpoints live together in their own
  file (`routers/robots.py`, `routers/missions.py`) instead of every
  route being crammed into `main.py`. This is the closest FastAPI
  equivalent to a Spring `@RestController` class — a self-contained
  group of endpoints, wired into the main app at startup via
  `app.include_router(...)`. `prefix="/robots"` means every route
  inside that file automatically gets `/robots` prepended, so
  individual route decorators (`@router.get("")`,
  `@router.get("/{robot_id}")`) never repeat it.
- **`fastapi dev app/main.py`** vs. `uvicorn app.main:app --reload` —
  functionally similar (both start the same server with auto-reload),
  but `fastapi dev` is the newer, more ergonomic entry point bundled
  with the `[standard]` extra. Both need to be run from the directory
  that contains `app/` (i.e. `backend\`) for import resolution to work
  correctly — see the Troubleshooting Guide below for what happens
  when that assumption breaks.

---

## Deep Dive: Path & Query Parameters

FastAPI decides *where* each parameter in an endpoint's signature
comes from purely by inspecting how it's declared — there's no
`@PathVariable`/`@RequestParam` annotation the way Spring requires:

- **Path parameters** — any name that appears inside `{}` in the
  route string (`"/{robot_id}"`) is matched against a same-named
  function parameter. The type hint (`robot_id: int`) isn't just
  documentation — FastAPI actively converts and validates the URL
  segment against it. A request to `/robots/abc` never reaches your
  function body at all; it's rejected with a `422` automatically,
  before any of your own code (including any database call) runs.
- **Query parameters** — any parameter *not* found in the path string
  and given a default becomes part of the URL's query string instead
  (`?max_battery=20`). Wrapping the default in `Query(...)` (instead of
  a bare `= None`) adds the same kind of validation `Field(...)`
  provides on a Pydantic model — `Query(default=None, ge=0, le=100)`
  is functionally the same rule as `Field(ge=0, le=100)` from Step 2 of
  today's demo, just applied to a URL value instead of a JSON body
  field.
- **The "no annotation needed" tradeoff.** This is a genuinely
  different mental model from Spring/JAX-RS, where every parameter
  source is explicit and unambiguous by annotation. FastAPI's inferred
  approach is less boilerplate, but it means *where a parameter comes
  from* is a fact you have to hold in your head about the route
  string, not something visibly marked on the parameter itself — worth
  calling out explicitly to anyone coming from an annotation-heavy
  Java background, since the omission itself can read as a missing
  step rather than a deliberate design choice.

---

## Deep Dive: Request Bodies & Validation (Pydantic v2)

- **A Pydantic `BaseModel` type hint means "this comes from the
  request body."** `payload: RobotCreate` in `create_robot` is what
  tells FastAPI to parse the incoming JSON, validate it against every
  rule declared on `RobotCreate` (and anything it inherits from
  `RobotBase`), and only then call the endpoint function — with
  `payload` already a fully validated Python object, not a raw dict
  you'd need to check by hand.
- **Validation happens in three places today, on purpose.** Day 1's
  `Robot._validate_battery()` clamped `battery_level` in plain Python.
  Day 2's `CHECK (battery_level BETWEEN 0 AND 100)` enforced it at the
  database. Today, `Field(ge=0, le=100)` on `RobotBase.battery_level`
  enforces the same rule a third time, at the API boundary. This isn't
  redundant by accident — a `CHECK` violation surfaces as an opaque,
  `500`-level database error deep in a stack trace; Pydantic's
  validation surfaces as a clean `422 Unprocessable Entity` with a
  specific field-level message, and it happens *before* any database
  round-trip at all.
- **`RobotCreate` vs. `RobotRead`.** Splitting "what a client is
  allowed to send" from "what the API returns" — even when they
  currently look nearly identical — matters because they represent
  different contracts. `RobotCreate` has no `id` field, because a
  client doesn't get to choose one (PostgreSQL's `SERIAL` still does,
  same as every prior day). This split will matter a lot more starting
  Day 5, once RBAC means not every field a client can *read* is one
  they should be allowed to *write*.
- **`ConfigDict(from_attributes=True)`** — Pydantic v2's renamed
  version of Pydantic v1's `orm_mode = True` (same behavior, new name;
  worth recognizing both if searching for help online). It tells a
  schema it's allowed to read its fields from an object's *attributes*
  (`robot.id`, `robot.serial_number`, ...) rather than only from a
  plain dict — required any time a `response_model` is being built
  directly from a SQLAlchemy ORM instance, which is exactly what
  `get_robot` and `create_robot` both do today.
- **`response_model` is a contract, not just a serialization hint.**
  Declaring `response_model=RobotRead` means FastAPI converts whatever
  the function actually returns through that schema before sending
  JSON back — even if a route accidentally returned extra internal
  fields on the ORM object, only what `RobotRead` declares would ever
  actually leave the API. This is a real security/data-hygiene
  property, not just documentation.

---

## Deep Dive: Dependency Injection

- **The core idea, transplanted from Java.** A piece of code declares
  *what it needs* (`db: AsyncSession = Depends(get_db)`), and the
  framework is responsible for constructing and handing that value
  over — the same fundamental idea as `@Autowired`/`@Inject` in
  Spring. FastAPI's version is function-based rather than
  annotation-based: `get_db` is a plain Python function, not a bean
  registered in some separate configuration class.
- **Generator dependencies (`yield`, not `return`).** `get_db` uses
  `yield` specifically so FastAPI can guarantee cleanup. Everything
  *before* the `yield` runs first (opening the session); the yielded
  value gets handed to the endpoint; and once the endpoint finishes —
  whether it succeeded or raised an exception — FastAPI resumes
  `get_db` right after the `yield`, letting the `async with` block
  close the session. This is conceptually identical to Java's
  try-with-resources: cleanup is guaranteed by the framework, not left
  to the endpoint to remember.
- **What this actually replaced.** Every one of Day 3's scripts
  manually wrote `async with AsyncSessionLocal() as session:` at the
  top of `main()`. `Depends(get_db)` is what removes that repetition
  from every single endpoint — the session-opening logic now lives in
  exactly one place (`app/dependencies.py`), used by every route that
  needs it.
- **Dependencies compose.** Nothing about today's `get_db` hints at
  this yet, but `Depends(...)` can itself depend on other
  `Depends(...)`-decorated functions — Day 5's authentication work
  (`get_current_user`) will build directly on top of today's pattern,
  likely depending on `get_db` itself to look up the authenticated
  user's record.

---

## Deep Dive: OpenAPI Docs

- **Nothing on `/docs` is hand-written.** The interactive Swagger UI
  page at `/docs` (and the alternate ReDoc-style page at `/redoc`) is
  generated entirely from the same type hints, `Field(...)`/`Query(...)`
  constraints, and docstrings already written for validation and
  routing purposes. There is no separate "write the API docs" step in
  a FastAPI project the way there often is elsewhere.
- **`FastAPI(title=..., description=..., version=...)`** in `main.py`
  sets the top-level metadata shown on the docs page itself — the
  RoboPulse project name, a short description, and a version string,
  all visible before a single endpoint is expanded.
- **This is a genuine practical tool, not just a demo page.** The
  "Try it out" button on `/docs` sends real requests against the
  running server — today's demo used it directly to confirm
  `GET /robots?max_battery=20` returns the same two robots every prior
  day's version of this question already found. This is worth treating
  as a standard first debugging step going forward, before reaching
  for `curl` or a separate API client.

---

## Architectural Analysis

Today's `schemas/` vs. `models/` split is the single most important
architectural decision made so far this course, and it's worth being
explicit about why. `app/models/Robot` (Day 3) describes a row in
PostgreSQL — SQLAlchemy needs it to include foreign keys,
`CheckConstraint`s, and enum-mapping quirks like `values_callable`,
none of which a client calling this API should ever need to know
about. `app/schemas/RobotRead` (today) describes what crosses the
wire — and as RBAC, JWT auth, and role-based field visibility get
introduced starting Day 5, that second contract is going to diverge
from the first in ways that would be actively harmful to conflate.
Projects that skip this split and hand SQLAlchemy models directly to
FastAPI's `response_model` tend to either leak internal fields by
accident, or hit a wall the first time "what the database stores" and
"what an API client should see" need to be different — which, for
RoboPulse, starts almost immediately (an `Operator`'s missions might
be visible to an Auditor role but a `Facility`'s `supervisor_id` might
not be, for example). Today's models/schemas boundary is what makes
that kind of policy addable later without reworking the data layer
itself.

The choice to answer both running business questions a fourth time —
rather than introducing new ones — continues the same deliberate
repetition established since Day 1: the questions themselves aren't
the lesson anymore, the tool producing the answer is. `GET
/robots?max_battery=20` took roughly the same number of lines as Day
3's ORM version, but it's now something a browser, a frontend
application, or `curl` can call directly — the entire point of
introducing FastAPI in the first place. Notably, the Phase B challenge
endpoint (`/missions/discrepancies`) deliberately selected only the
four specific columns its response needed, rather than reusing Day 3's
`find_colocation_discrepancies_orm` (which returns full `Mission`
objects) unchanged — a small but real lesson in tailoring a query to
what an API response actually requires, instead of over-fetching data
that then has to be picked apart after the fact.

---

## Common Pitfalls & Anti-Patterns

- **A missing `app/__init__.py`.** This is the single most disruptive
  mistake possible today, and it happened in this very class's dry
  run: `fastapi dev` walks upward from `app/main.py` looking for the
  topmost directory that's still a proper Python package (has an
  `__init__.py`) to determine what belongs on `sys.path`. If
  `app/__init__.py` is missing, `fastapi dev` mistakenly treats `app\`
  itself as the root — imports *within* `app/` (like `main.py`
  importing `routers`) can still work, while anything explicitly
  written as `from app.something import X` (like `robots.py`
  importing `from app.dependencies import get_db`) fails with
  `ModuleNotFoundError: No module named 'app'`. The traceback's own
  `WARNING  Ensure all the package directories have an __init__.py
  file` line is the direct clue — worth teaching students to actually
  read that warning line rather than only the final exception.
- **Conflating ORM models and Pydantic schemas.** Passing
  `app.models.Robot` directly as a `response_model`, or building
  `RobotCreate`/`RobotRead` as thin wrappers that just re-export the
  ORM class, defeats the entire purpose of today's `schemas/` package
  — see the Architectural Analysis above for why this matters more
  than it might first appear.
- **Writing a new router file but forgetting to register it in
  `main.py`.** `app.include_router(missions.router)` is easy to skip —
  the symptom isn't an error, it's silence: the endpoint simply never
  appears anywhere, not even as a `404` (a `404` would at least
  confirm the app is aware the path should exist). Absence from
  `/docs` entirely is the tell.
- **Making an intended-optional query parameter accidentally
  required.** Omitting a default (or omitting `Query(default=None,
  ...)` entirely) turns a parameter required — every existing call
  that previously worked without it now fails with a `422`. Worth
  double-checking any new query parameter by calling the endpoint both
  with and without it.
- **Reaching for `.scalars()` out of habit on a multi-column
  `select()`.** Every endpoint in `robots.py` returns whole `Robot`
  objects and uses `result.scalars().all()`. The moment a query
  selects individual labeled columns instead (as
  `/missions/discrepancies` does), `.scalars()` doesn't produce the
  right shape — `.mappings()` is what turns a multi-column row into
  something dict-like. This is an easy copy-paste mistake precisely
  because the earlier pattern was so consistent.
- **An unrelated `app` package installed in the venv shadowing the
  project's own `app/` folder.** There's a real, unrelated package on
  PyPI literally named `app` — if it's ever accidentally installed
  (`pip show app` to check), it can shadow the project's local `app/`
  directory during import resolution, producing a confusingly similar
  `ModuleNotFoundError` to the missing-`__init__.py` case above but
  with an entirely different root cause.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'`, but only once execution reaches a file *inside* `app/` (e.g. `routers/robots.py`'s `from app.dependencies import get_db`) — while `app/main.py` itself seemed to load fine | `app/__init__.py` is missing, so `fastapi dev`'s root-detection treats `app\` itself as the package root instead of `backend\` | Confirm with `Test-Path app\__init__.py`; if `False`, recreate it: `New-Item -ItemType File -Force -Path app\__init__.py \| Out-Null`, then re-run `fastapi dev app/main.py` |
| `ModuleNotFoundError: No module named 'app'`, and `app\__init__.py` genuinely exists | An unrelated PyPI package literally named `app` is installed in the venv and shadowing the project's own folder | `pip show app` to check; if it returns real package info (not "not found"), run `pip uninstall app` |
| A new endpoint doesn't appear at all in `/docs`, with no error anywhere | The router was written correctly but never registered — `app.include_router(...)` missing from `main.py` | Check `app/main.py` for the missing `include_router` call |
| `422 Unprocessable Entity` on a request that looks correct | A `Field(...)`/`Query(...)` constraint rejected the value (out-of-range number, wrong type, missing required field) *before* the endpoint function ran | Check the response body — FastAPI includes exactly which field failed and why; cross-reference against the schema's `Field(...)` definitions |
| A GET request that previously worked now returns `422` after adding a new query parameter | The new parameter was declared without a default (or without `Query(default=None, ...)`), making it unintentionally required | Give it an explicit default so it's genuinely optional |
| `AttributeError` or unexpected shape when trying to loop over a multi-column `select()` result | `.scalars().all()` was used on a query that selected individual labeled columns instead of whole ORM objects | Use `.mappings().all()` instead, and convert each row with `dict(row)` if a plain dict is needed |
| A `POST` request returns `500` instead of a clean validation error | Something is bypassing Pydantic validation — e.g. constructing the ORM object from unvalidated raw data instead of from the validated `payload` object | Confirm the endpoint builds the ORM instance from `payload.model_dump()` (the validated schema), not from `request.json()` or similar |
| `fastapi dev app/main.py` fails immediately, unrelated to any import | Wrong working directory, or venv not activated | Run `Get-Location` (should end in `...\backend`) and confirm `(.venv)` shows in the prompt; re-activate with `.\.venv\Scripts\Activate.ps1` if needed |
| Server starts, but every database-backed endpoint fails with a connection error | PostgreSQL service stopped, or the `localhost` vs. `127.0.0.1` IPv6-resolution issue from Day 3 (`ConnectionRefusedError: [WinError 1225]`) | See Day 3's notes Troubleshooting Guide — the fix (service check, or swapping `localhost` for `127.0.0.1` in `DATABASE_URL`) is unchanged today, since `app/database.py` itself didn't change |
| `OSError: [WinError 10048] ... address already in use` (or similar) when starting the server | Another `fastapi dev`/`uvicorn` process is still running from an earlier terminal tab, holding port 8000 | Close the earlier terminal tab/process, or start this one on a different port: `fastapi dev app/main.py --port 8001` |

---
*RoboPulse Fleet Command Center — Day 4 of 13*
