# Day 3 — Notes
## Week 1, Friday: Asynch SQLAlchemy ORM, SQLAlchemy, Create_All Table Generation

---

## Executive Summary

Day 1 built the *shape* of RoboPulse's data as plain Python classes.
Day 2 gave that shape a permanent, hand-written home in PostgreSQL.
Today those two threads merge into one: the ORM. `Facility`, `Robot`,
`Mission`, `Operator`, and `DiagnosticLog` become SQLAlchemy 2.0
declarative classes — still Python classes with `__repr__` methods and
business-logic methods like `is_low_battery()`, but each one is now
also a direct, live mapping onto one of Day 2's PostgreSQL tables.
Query them with Python expressions (`Robot.battery_level < 20`), and
SQLAlchemy compiles that expression down into the same SQL Day 2 typed
into `psql` by hand.

Today is also this course's first encounter with `async`/`await` on
the backend, ahead of FastAPI — which is itself an async framework —
so the muscle memory built today (an `AsyncSession`, `await
session.execute(...)`, eager-loading relationships to avoid the
`MissingGreenlet` trap) is not a throwaway lesson. It is exactly the
pattern Monday's FastAPI endpoints will use, dependency-injected via
`Depends`, to talk to this same database.

Business Question #1 (Low Battery Alert) got answered a third time
today — Python list comprehension (Day 1) → SQL `WHERE` clause (Day 2)
→ SQLAlchemy `select().where()` (today) — same two robots every time,
different tool doing the work. The Phase B challenge answered Business
Question #2 (Co-Location Discrepancy) a third time as well, this time
as an async three-table `.join()`, deliberately continuing the same
running example so the *contrast between tools* stays the lesson,
rather than the business logic itself.

---

## Deep Dive: SQLAlchemy 2.0 — Declarative Models

A SQLAlchemy **model** is a Python class that is simultaneously two
things: an ordinary object (with methods, a `__repr__`, whatever else
you'd put on any class) and a description of a database table. This
dual nature is the entire idea of an ORM (Object-Relational Mapper) —
it's the same mental shift as moving from raw JDBC in Java to
something like Hibernate/JPA: you stop writing `SELECT`/`INSERT`
strings by hand and start describing your data as classes, letting the
framework generate the SQL.

Key building blocks used today:

- **`DeclarativeBase`** — every model inherits from a shared `Base`
  class (`app/models/base.py`). This is the 2.0-native replacement for
  the older `declarative_base()` factory function still common in
  pre-2.0 tutorials; functionally similar, but written as a real class
  so type checkers understand your models. Comparable to a JPA
  `@MappedSuperclass`, or simply "the thing every `@Entity` implicitly
  shares" in Java's persistence world.
- **`Mapped[T]` and `mapped_column()`** — `id: Mapped[int] =
  mapped_column(primary_key=True)` does two jobs in one line: it's a
  type-hinted Python attribute (so your editor knows `robot.id` is an
  `int`) *and* it's the column definition SQLAlchemy uses to generate
  `CREATE TABLE` DDL. This paired syntax is specific to SQLAlchemy 2.0
  — older code (`id = Column(Integer, primary_key=True)`) only did the
  second job, leaving type checkers blind to your models' shapes.
- **`__tablename__`** — the one required piece of "plumbing" on every
  model, telling SQLAlchemy which actual PostgreSQL table this class
  maps to (`robots`, `missions`, etc.) — must match Day 2's
  `schema.sql` table names exactly, since today's models map onto
  tables that already exist.
- **`relationship()`** — describes the ORM-level connection between
  two mapped classes (`Robot.facility`, `Facility.robots`), separate
  from (but built on top of) the actual `ForeignKey` column. This is
  what lets you write `robot.facility.name` instead of a second manual
  query — the direct ORM equivalent of what Day 1's `Robot.find_by_id`
  and Day 2's `JOIN` each did by hand, in their own way.
- **`back_populates`** — keeps both sides of a relationship in sync
  with each other (`Robot.facility` and `Facility.robots` both exist
  and stay consistent) without you having to maintain that consistency
  by hand. The string passed to `back_populates` on one side must
  match the *attribute name* on the other side exactly — a common typo
  source (mismatched string vs. attribute name fails silently at
  class-definition time, then raises a confusing error the first time
  the relationship is actually used).

**Why this matters for RoboPulse:** the fields didn't change today —
`Robot.__init__`'s parameters from Day 1 are the same columns Day 2's
`CREATE TABLE robots` declared, which are the same `mapped_column()`
declarations today. What changed is who's responsible for generating
and running the SQL: you (Day 2), or SQLAlchemy (today).

---

## Deep Dive: Solving Circular Imports the SQLAlchemy Way

Day 1 first ran into "the other class isn't fully defined yet" inside
a *single* file (`registry: ClassVar[list["Facility"]]`, a forward
reference in quotes). Today's problem is bigger: `facility.py` needs
to describe a relationship to `Robot`, and `robot.py` needs one back to
`Facility` — each file wanting to import a class from the other,
which Python cannot resolve (`ImportError: cannot import name 'Robot'
from partially initialized module`).

Today's fix has two parts, used together in every rewritten model
file:

1. **`from __future__ import annotations`** — makes every type
   annotation in the file a plain, unevaluated string at
   class-definition time (this is PEP 563, "postponed evaluation of
   annotations"). `Mapped[list["Robot"]]` never actually tries to look
   up `Robot` as a real name while the module is loading.
2. **`if TYPE_CHECKING: from .robot import Robot`** — imports `Robot`
   *only* for your editor/type-checker's benefit. `TYPE_CHECKING` is a
   constant that is always `False` at actual runtime, so this import
   line never executes when the script runs — no circular import ever
   happens in practice.

So how does `relationship(back_populates="facility")` know it's
actually pointing at the real `Robot` class if it's never truly
imported at runtime? SQLAlchemy resolves the string `"Robot"` against
its own **mapper registry** — the shared bookkeeping every class
inheriting from `Base` gets registered into — the first time any query
actually configures its mappers. This is exactly why
`app/models/__init__.py` importing every single model file matters:
it's what guarantees every class has been registered *before* any
relationship needs to resolve a name.

This is a genuinely standard, documented SQLAlchemy 2.0 pattern (it
appears directly in SQLAlchemy's own ORM quickstart for exactly this
scenario) — not a RoboPulse-specific workaround.

---

## Deep Dive: The Enum `values_callable` Gotcha

Day 1's `enums.py` classes (`class RobotStatus(str, Enum): IDLE =
"Idle"`) were reused today completely unchanged — SQLAlchemy maps a
Python `Enum` directly onto a PostgreSQL native `ENUM` column type.
But there's a mismatch buried in how that mapping happens by default:

- SQLAlchemy's default behavior stores the enum member's **name**
  (`IDLE`, `IN_MISSION`) in the database.
- Day 2's `schema.sql` already created the `robot_status` type using
  the member's **value** strings (`'Idle'`, `'In-Mission'`).

Without `values_callable=lambda enum_cls: [member.value for member in
enum_cls]` explicitly telling SQLAlchemy to use `.value` instead of
`.name`, the very first real query against Day 2's seeded data raises
`LookupError: 'Idle' is not among the defined enum values` — because
SQLAlchemy is looking for a value spelled `IDLE`, which doesn't exist
in the actual column data.

This is worth treating as a first-class lesson, not a footnote: it's
the kind of bug that only appears the moment two independently-correct
pieces of code (a schema written by hand on Day 2, a model written by
hand today) meet for the first time — neither file is "wrong" in
isolation, but their defaults disagree.

---

## Deep Dive: `Base.metadata.create_all` and `checkfirst`

`create_all` reads every model's `__tablename__`, columns, and
constraints, and issues the matching `CREATE TYPE`/`CREATE TABLE`
statements — the same DDL Day 2 typed into `schema.sql` by hand,
generated instead.

Two behaviors worth internalizing:

- **It's idempotent by default (`checkfirst=True`).** Before creating
  anything, `create_all` checks PostgreSQL's own catalog
  (`information_schema`, `pg_type`) for what already exists, and skips
  any table or type that's already there. Running it against Day 2's
  already-built `robopulse_dev` produces zero `CREATE` statements and
  doesn't touch existing rows — a genuinely important safety property,
  and the opposite lesson from Day 2's biggest warning (`UPDATE`/
  `DELETE` without `WHERE`): here, the *default* behavior is the safe
  one.
- **It does not detect drift.** `checkfirst` only asks "does this
  table exist?" — never "does this *existing* table's shape match what
  the model currently says?" If a model's column type changed after
  the real table was already created, `create_all` would silently do
  nothing about the mismatch, and the discrepancy would only surface
  later, as a runtime error on the first query that touches it. Real
  projects solve this with a dedicated migration tool that tracks
  schema versions over time — deliberately out of scope for this
  course given the time available, which means schema changes from
  here forward need to be made carefully, by hand, on both the model
  and (if it already exists) the live table.

Today's demo deliberately ran `create_all` **twice** — once against a
disposable scratch database (to actually *watch* it generate DDL from
nothing) and once against the real seeded database (to prove the
idempotent, non-destructive behavior) — specifically so both
properties get witnessed directly rather than just described.

---

## Deep Dive: Async SQLAlchemy — Engine, Session, and the `MissingGreenlet` Trap

- **`create_async_engine(...)`** replaces the plain `create_engine(...)`
  from sync SQLAlchemy. The connection string's driver segment
  (`+asyncpg`) is what actually makes it async — swap it for a sync
  driver (or omit it) and the async engine machinery has nothing async
  to talk to.
- **`async_sessionmaker` / `AsyncSession`** — the async equivalents of
  `sessionmaker`/`Session`. Every database operation through them is
  `await`ed: `await session.execute(statement)`, not
  `session.execute(statement)`.
- **`conn.run_sync(...)`** — the bridge for calling old-style,
  fundamentally synchronous SQLAlchemy APIs (like
  `Base.metadata.create_all`, which predates async SQLAlchemy
  entirely) from inside an async context. You'll see this exact
  pattern reused any time a sync-only API needs to be called from
  async code.
- **Lazy loading vs. eager loading — the `MissingGreenlet` trap.** By
  default, `robot.facility` is a **lazy-loaded** relationship: the
  related row isn't fetched until the exact line of code that touches
  it. In sync SQLAlchemy, that's invisible — it just quietly runs
  another query right there. In async SQLAlchemy, that lazy load would
  need to `await` a new query, but it's often triggered from a spot
  (an f-string inside a plain `print()`, for instance) that has no way
  to `await` anything. The result is
  `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
  can't call await_only() here` — SQLAlchemy's way of saying "I needed
  to do I/O somewhere that can't be awaited." `selectinload(...)`
  fixes this by fetching the related rows **eagerly**, as a second
  query issued immediately alongside the main one, while the session
  can still safely `await`.

This is widely regarded as *the* most common first mistake developers
make picking up async SQLAlchemy for the first time — today's demo
deliberately broke it on purpose (Step 9) specifically so it's a known
quantity before Monday's FastAPI endpoints depend on this exact
session pattern under the hood.

---

## Architectural Analysis

Today did not introduce a single new business concept — every field,
every relationship, every business question answered today already
existed by the end of Day 2. What changed is the *mechanism*: Day 1
was "what does the data look like," Day 2 was "how does it persist,"
and today is "how does application code talk to that persistence
layer without writing raw SQL by hand." That progression — plain
Python → raw SQL → ORM — is deliberate scaffolding, the same way Day
1's notes described the plain-Python classes as scaffolding for Day
2's tables. The ORM was never going to feel like unexplainable magic,
because every piece of DDL it generates today has already been seen,
typed by hand, on Day 2.

The choice to make everything **async** today, a full workday before
FastAPI is introduced, is also deliberate. FastAPI is fundamentally an
async framework; if today had used sync SQLAlchemy, Monday's lesson
would have needed to teach "here's the ORM" and "here's async" as two
new ideas simultaneously, layered on top of "here's a whole new web
framework." Isolating the async-specific gotcha (`MissingGreenlet`) to
a day with no other new framework to learn means Monday can focus
entirely on FastAPI's own concepts, reusing today's `AsyncSessionLocal`
and model classes essentially unchanged, wired in through FastAPI's
`Depends()` system.

Business Question #2 (Co-Location Discrepancy) has now been solved
three times, once per day, deliberately using the same seeded data
each time so the single-row result (`Mission 2`) never changes — only
the tool producing it does. This is intentional repetition, not
padding: the goal isn't teaching the business question a third time,
it's letting students directly compare *how much code* each layer
takes to express the same idea (a dozen-plus lines of manual
`find_by_id()` looping on Day 1, a five-line `JOIN` on Day 2, a
five-line `.join()`/`.where()` chain today) and see, concretely, what
each additional layer of tooling actually buys you.

---

## Common Pitfalls & Anti-Patterns

- **Missing `values_callable` on an `Enum` column.** The single most
  likely first error today — `LookupError: 'Idle' is not among the
  defined enum values` the moment a query touches real seeded data,
  because SQLAlchemy defaults to storing the Python member's `.name`
  instead of `.value`.
- **Forgetting `+asyncpg` in the connection string.** `postgresql://`
  alone defaults toward a sync driver, which an async engine can't use
  — this typically surfaces as an `InvalidRequestError` or an import
  error mentioning a missing sync driver, right when the engine is
  first used.
- **Touching a lazy-loaded relationship attribute without
  `selectinload`.** Produces `MissingGreenlet` the moment code like
  `robot.facility.name` runs inside an async session without having
  eagerly loaded `facility` first.
- **Mismatched `back_populates` strings.** If `Robot.facility`'s
  `back_populates="robots"` doesn't exactly match the attribute name
  actually defined on `Facility` (a typo, or a rename on one side that
  didn't get mirrored on the other), SQLAlchemy raises a mapper
  configuration error the first time any query actually runs — not at
  import time, which can make the root cause harder to trace back to
  the actual typo.
- **Using `session.query(...)` instead of `select(...)`.** Both still
  technically work in SQLAlchemy 2.0 (the legacy `Query` API wasn't
  removed), but mixing styles is inconsistent with this course's
  standardization on the unified `select()` construct starting today —
  worth correcting on sight so the codebase stays uniform for anyone
  using it as a reference later.
- **Filtering in Python instead of in the query.** Fetching every row
  with eager-loaded relationships and then looping in Python to find
  matches *works*, but defeats the entire point of today's ORM lesson
  — the database should do the filtering (via `.where()`), the same
  principle Day 2 taught with raw SQL.
- **Assuming `create_all` will fix a changed model.** If a column
  definition changes after the real table already exists,
  `checkfirst=True` means `create_all` silently does nothing — no
  error, no warning, just an unnoticed mismatch until a query fails
  later.
- **Opening a new session inside a function that should accept one.**
  Mirrors Day 1's exact pitfall (hardcoding `Mission.registry` instead
  of accepting `missions` as a parameter) in async ORM form — makes
  the function untestable against anything but a single global
  session.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `LookupError: '<value>' is not among the defined enum values` | The `Enum` column mapping is missing `values_callable`, so SQLAlchemy is matching against the Python member's `.name` instead of `.value` | Add `values_callable=lambda enum_cls: [member.value for member in enum_cls]` to every `SqlEnum(...)` column definition |
| `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here` | A lazy-loaded relationship attribute (e.g. `robot.facility`) was accessed from a spot that can't `await` — usually inside a plain `print()`/f-string, or after the session's work is otherwise done | Add `.options(selectinload(Robot.facility))` (or the relevant relationship) to the `select()` statement, so it's fetched eagerly instead of lazily |
| `ModuleNotFoundError: No module named 'app'` (or `'scripts'`) | Running the script from the wrong directory | Run from `backend\` (the directory containing `app\`), using `python -m scripts.day3_demo` / `day3_create_tables` / `day3_challenge`, not a bare `python scripts\day3_demo.py` |
| `ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection` (even though `Get-Service` shows the PostgreSQL service running, and the port is confirmed correct) | On Windows, `localhost` can resolve to the IPv6 loopback address (`::1`) first; if PostgreSQL isn't listening there (only on IPv4's `127.0.0.1`), `asyncpg` gets refused even though the service itself is healthy — `psql` doesn't hit this because it falls back differently | Replace `localhost` with `127.0.0.1` explicitly in every `DATABASE_URL` connection string (`app/database.py` and any `$env:DATABASE_URL` line used for the scratch database) |
| `psycopg2`-related `ModuleNotFoundError`, or an error suggesting a sync driver was expected | `+asyncpg` is missing from the connection string, so SQLAlchemy defaulted toward a sync driver that isn't installed (and wouldn't work with the async engine even if it were) | Confirm the connection string reads `postgresql+asyncpg://...`, not `postgresql://...` |
| `create_all` runs with no errors, but a table's columns/constraints don't match what the model defines | `checkfirst=True` only checks whether a table *exists*, not whether its shape matches the model — a known limitation, not a bug | Manually reconcile the model and the live table by hand (`ALTER TABLE` in `psql`, or drop and recreate a scratch table); this course intentionally skips migration tooling given time constraints |
| A relationship (`Robot.facility`, `Mission.robot`, etc.) raises a mapper configuration error the first time a query runs, but the file itself imports fine | `back_populates` string on one side doesn't exactly match the attribute name on the other side of the relationship | Check both sides of the relationship for an exact string match (including underscores/pluralization) |
| `ImportError: cannot import name 'Robot' from partially initialized module 'app.models.robot'` | A model file imported another model directly at the top level (outside `TYPE_CHECKING`), reintroducing the circular import today's pattern was written to avoid | Move the import inside `if TYPE_CHECKING:`, and confirm `from __future__ import annotations` is present at the top of the file |
| `InvalidCatalogNameError` (or similar "database does not exist") when running against the scratch database | The `CREATE DATABASE robopulse_dev_scratch;` command was skipped, failed, or was already cleaned up (`DROP DATABASE`) before the script ran | Re-run `psql -U postgres -c "CREATE DATABASE robopulse_dev_scratch;"` before pointing `$env:DATABASE_URL` at it |
| Script runs against the wrong database without any error at all | `$env:DATABASE_URL` was set in an earlier terminal tab/session and either never got cleared, or was expected to persist into a *new* tab (it won't — `$env:` scoping is per-process) | Run `$env:DATABASE_URL` (with no value) to print its current setting before running any script today; use `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue` to fall back to `database.py`'s hardcoded default |

---
*RoboPulse Fleet Command Center — Day 3 of 13*
