# Day 5 — Notes
## Week 2, Wednesday: Security & RBAC, Password Hashing, JWT Token Creation, OAuth Route Protection, Protected API Endpoints, User Session Context

---

## Executive Summary

Every endpoint built on Day 4 was wide open — anyone who could reach
the server could create robots or read fleet data. Today closes that
gap entirely, introducing a fifth entity the original ERD never listed
(`User`) and a full authentication/authorization layer on top of it:
passwords are hashed, never stored in the clear; logging in exchanges
a username/password for a signed JWT; and every existing endpoint now
declares, explicitly, exactly who's allowed to call it — anyone
authenticated, or specifically a Fleet Admin, via the same
`Depends(...)` mechanism Day 4 introduced for the database session.

Nothing about *how* FastAPI wires dependencies changed today — that
was Day 4's lesson, fully reused. What's new is *what* gets
dependency-injected: instead of just a database session, an endpoint
can now also require a verified, role-checked `User`, and FastAPI will
refuse the request entirely (with the correct 401 or 403) before the
endpoint's own code ever runs if that requirement isn't met.

The chapter closes with a genuinely important architectural idea:
**User Session Context** in a JWT-based API is nothing like a
traditional Java `HttpSession` — there is no server-side memory of who
is logged in at all. Every request reconstructs identity from scratch,
from the token alone. That statelessness is the entire reason this
approach scales cleanly to multiple server instances without any
shared session store — and it's also the reason a JWT, once issued,
can't be revoked early the way a server-side session can simply be
deleted.

---

## Deep Dive: RBAC and the New `User` Entity

- **Why `User` isn't in the original ERD.** The problem statement's
  data architecture diagram (Facility → Robot → Mission →
  DiagnosticLog) describes what RoboPulse tracks operationally. `User`
  describes who's allowed to *do things to* that data — a different
  kind of entity, introduced only once the system needs to answer
  "who is asking?" This mirrors Day 1's `Operator` addition: implied
  by the problem statement's RBAC section, but not spelled out as a
  formal entity until the day the system actually needed it.
- **Three roles, one enum.** `UserRole` reuses the exact `(str, Enum)`
  pattern and the exact `values_callable` fix from Day 3's
  `RobotStatus`/`MissionPriority`/`MissionStatus` — by this point in
  the course, mapping a new enum onto a PostgreSQL column should feel
  like a completely mechanical, repeatable step rather than new
  material.
- **RBAC as a *layered* concept, not a single check.** Today's system
  actually has two distinct layers working together: **authentication**
  ("is this a real, currently-valid identity?" — `get_current_user`)
  and **authorization** ("is this specific identity allowed to do this
  specific thing?" — `require_role(...)`). They're deliberately
  separate functions in `dependencies.py`, and that separation is
  itself a best practice: authentication logic never needs to know
  anything about which roles exist or what any particular endpoint
  requires.

---

## Deep Dive: Password Hashing

- **Hashing, not encryption.** Encryption is reversible (given the
  right key); a cryptographic hash is deliberately **one-way** — there
  is no `decrypt_password()` function anywhere in this codebase,
  because bcrypt makes one impossible by design. `verify_password`
  never recovers the original password; it re-hashes the *attempt*
  and compares hash output to hash output.
- **Salting defeats precomputed attacks.** `bcrypt.gensalt()` bakes a
  random salt directly into each hash's output, so identical passwords
  across different users produce entirely different stored hashes.
  Without this, an attacker with database access could precompute
  hashes for every password in a common wordlist once, then match
  against every stored row instantly (a "rainbow table" attack) —
  salting makes that precomputation worthless, since the attacker
  would need a separate rainbow table per unique salt.
- **The bcrypt 72-byte quirk.** bcrypt only uses the first 72 bytes of
  whatever input it's given; anything beyond that is silently ignored,
  not an error. Not a practical concern for ordinary passwords, but a
  real, documented property worth knowing exists rather than
  discovering by surprise.
- **Why this course uses `bcrypt` directly instead of `passlib`.**
  `passlib` has been effectively unmaintained since 2020 and has a
  known, currently-unresolved break against `bcrypt` 4.x
  (`AttributeError: module 'bcrypt' has no attribute '__about__'`).
  Calling `bcrypt.hashpw`/`bcrypt.checkpw` directly sidesteps an entire
  category of environment problems that a lot of still-circulating
  FastAPI tutorials would walk students straight into.

---

## Deep Dive: JWT Token Creation

- **Structure: `header.payload.signature`.** Three base64-encoded
  segments joined by dots. The header identifies the algorithm
  (`HS256` here). The payload carries claims — today, `sub` (the
  username) and `role`, plus an automatically-added `exp` (expiration
  timestamp). The signature is computed from the header and payload
  using `SECRET_KEY`, and is what `decode_access_token` verifies on
  every subsequent request.
- **Signed, not encrypted — a distinction with real consequences.**
  Anyone holding a JWT can base64-*decode* its payload and read it
  directly, with no key required at all — this was demonstrated
  hands-on in today's Phase B research prompts. The signature only
  proves the payload **wasn't tampered with** after issuing; it proves
  nothing about *confidentiality*. This is exactly why a password (or
  any other sensitive value) must never appear inside a JWT payload,
  even though a username and role safely can.
- **`HS256`** is a *symmetric* algorithm — the same `SECRET_KEY`
  both signs new tokens and verifies existing ones. This is simpler
  than an asymmetric scheme (like `RS256`, which uses a private key to
  sign and a separate public key to verify) but means anything holding
  `SECRET_KEY` can mint valid tokens for any user — reinforcing why
  that value can never be committed to source control in a real
  deployment, even though today's course keeps it as a simple env-var
  fallback for local development speed.
- **`exp` is enforced by the *decoding* library, not by this
  project's own code.** `jwt.decode(...)` in `decode_access_token`
  automatically raises `jwt.ExpiredSignatureError` (a subclass of
  `jwt.InvalidTokenError`, already caught in `get_current_user`) the
  moment the current time passes the token's `exp` claim — RoboPulse
  never wrote its own expiration-checking logic; PyJWT does it as part
  of `decode`.

---

## Deep Dive: OAuth Route Protection

- **`OAuth2PasswordBearer`** is configuration, not validation logic —
  it declares *where* login happens (`tokenUrl="auth/token"`, which is
  what makes `/docs`'s Authorize button send credentials to the right
  place) and tells FastAPI to expect and extract a Bearer token from
  the `Authorization` header on any endpoint that depends on it.
- **`OAuth2PasswordRequestForm`** is the one deliberate break from the
  JSON-body pattern every endpoint has followed since Day 4. The
  OAuth2 "password flow" specification requires credentials sent as
  `application/x-www-form-urlencoded` form data, not JSON — a genuine
  spec requirement, not a RoboPulse-specific inconsistency. This is
  also why `python-multipart` (bundled via Day 4's `fastapi[standard]`
  install) had to already be present — form parsing needs it, JSON
  parsing doesn't.
- **The "Authorize" flow in `/docs` isn't magic** — it's Swagger UI
  reading the `OAuth2PasswordBearer` configuration and building a
  small login form around it automatically, then attaching the
  returned token to every subsequent "Try it out" request for the rest
  of the browser session. This is the OpenAPI docs story from Day 4
  continuing directly: nothing here was hand-written either.

---

## Deep Dive: Protected API Endpoints

- **Dependencies compose — today's payoff for Day 4's foreshadowing.**
  `require_role(...)` itself depends on `get_current_user`, which
  itself depends on `get_db` — a three-level chain, and an endpoint
  using `Depends(require_role(UserRole.FLEET_ADMIN))` triggers the
  entire chain automatically, in order, with zero repeated code across
  endpoints.
- **The dependency *factory* pattern.** `require_role(*allowed_roles)`
  is a function that *returns* a dependency, rather than being one
  itself. This is what lets `create_robot` and today's Phase B status
  endpoint each declare a different, specific set of allowed roles
  using the exact same underlying authorization logic, with no
  duplicated comparison code and no need to write a separate
  `require_admin_role`/`require_admin_or_operator_role` function for
  each combination.
- **401 vs. 403 is a real distinction, not two flavors of "no."**
  `401 Unauthorized` means *"I don't know who you are"* — no token, a
  malformed token, an expired token, or a token for a user that no
  longer exists. `403 Forbidden` means *"I know exactly who you are,
  and the answer is still no"* — a fully valid, currently-logged-in
  Auditor calling an admin-only endpoint. Conflating these is a common
  real-world API mistake; today's implementation keeps them cleanly
  separated across two different functions (`get_current_user` raises
  401; `role_checker` inside `require_role` raises 403).
- **The `_: User = Depends(...)` convention.** The underscore signals
  "this dependency must run and must be satisfied, but its return
  value isn't needed inside this function body" — distinct from
  `get_current_user`'s own internal use of `db: AsyncSession =
  Depends(get_db)`, where the returned session genuinely is used.

---

## Deep Dive: User Session Context

| | Traditional (Java `HttpSession`) | Today (Stateless JWT) |
|---|---|---|
| **Where state lives** | Server-side memory (or a shared session store) | Nowhere on the server — entirely inside the token itself |
| **What identifies a request** | A session ID, usually in a cookie | The JWT itself, sent in the `Authorization` header |
| **Multi-server / load-balanced deployments** | Needs a shared session store (e.g. Redis) so any server instance can recognize the session | Works immediately across any number of stateless server instances — any of them can verify the signature independently |
| **Revoking access early** | Trivial — delete the server-side session | Not directly possible — a valid, unexpired token remains valid until it expires, full stop |
| **What "logging in" actually does** | Allocates and stores server-side state | Issues a signed, self-contained credential; the server does no further bookkeeping |

This tradeoff — simplicity and horizontal scalability, at the cost of
no built-in early revocation — is a deliberate, well-understood
industry-wide design decision, not a limitation specific to today's
implementation. (Real-world systems that need early revocation on top
of JWTs typically add a short-lived access token plus a separate,
server-tracked refresh token — out of scope for this course, but worth
knowing the term for.)

---

## Architectural Analysis

Today validates a decision made back on Day 4: the `schemas/` vs.
`models/` split existed specifically so a field like
`hashed_password` could live safely on the ORM model — where the
database genuinely needs it — while `UserRead` guarantees it can never
leave the API, structurally, not by convention or code review
discipline. This is the clearest possible demonstration of why that
split mattered, and it's worth pointing back to Day 4's notes
explicitly: the architectural bet made two days ago paid off exactly
as predicted.

The `POST /auth/register` bootstrapping puzzle (an endpoint that
requires a Fleet Admin to call it, with no Fleet Admin able to exist
until someone calls it) is intentional, not an oversight — it forces a
direct confrontation with a genuinely common real-world deployment
question: how does a secured system's *very first* privileged account
get created? Today's answer (a one-time seed script that writes
directly to the database, bypassing the API layer entirely) is a
standard, legitimate pattern — many real systems bootstrap their first
admin this way, sometimes via a CLI command or a one-time setup wizard
rather than a script, but the underlying idea (privileged accounts
can't self-provision through the normal authenticated flow) is the
same.

Looking ahead: the JWT issued today doesn't just protect the FastAPI
backend — Day 6 introduces React, and the frontend's authentication
state (who's logged in, what role they hold, whether to show or hide
UI elements) will be built by storing and re-sending this exact same
token on every request, managed through React's Context API. Nothing
about today's token format or claims needs to change for that to
work — `sub` and `role` are already exactly what a frontend auth
context needs to know.

---

## Common Pitfalls & Anti-Patterns

- **Reaching for `passlib`/`python-jose` instead of `bcrypt`/`PyJWT`.**
  Both older libraries are still referenced constantly online;
  `passlib` specifically has a known, unresolved compatibility break
  with modern `bcrypt` versions.
- **Putting anything sensitive inside a JWT payload.** The payload is
  readable by anyone holding the token, with no key required —
  signing proves integrity, not confidentiality.
- **Confusing 401 and 403.** Returning 403 for "you're not logged in
  at all," or 401 for "you're logged in but not allowed to do this,"
  is a common, confusing real-world API inconsistency — today's
  implementation deliberately keeps these separated by which function
  raises which.
- **An open, unauthenticated user-registration endpoint.** Letting
  anyone self-register with any role (including Fleet Admin) defeats
  RBAC before it starts — today's `POST /auth/register` is
  deliberately Fleet-Admin-only, with the bootstrapping problem that
  creates solved by a seed script instead.
- **Sending JSON to `POST /auth/token`.** This is the one endpoint in
  the whole project that expects form-encoded data
  (`OAuth2PasswordRequestForm`), not JSON — a very easy mistake to
  make purely out of habit, since every other endpoint so far has
  been JSON.
- **Hardcoding `SECRET_KEY` and committing it.** Today's fallback
  string is a placeholder for local development speed, explicitly
  flagged as something that needs to move into a real, uncommitted
  `.env` file (Week 3's `bin/setup.sh`) before this project is
  anything more than a local classroom exercise.
- **Calling `mark_completed()`/`mark_failed()` inconsistently** (Phase
  B) — bypassing them with a direct `.status = ...` assignment
  produces an identical result today, but quietly discards the one
  place future side effects (timestamps, notifications) would belong.
- **Forgetting `await db.refresh(...)` after a commit.** Doesn't
  always visibly break anything for a simple field update, but is the
  correct habit for guaranteeing a returned object reflects what's
  actually persisted, not just in-memory state.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `422 Unprocessable Entity` calling `POST /auth/token` with a JSON body | `OAuth2PasswordRequestForm` expects `application/x-www-form-urlencoded` data, not JSON — the one deliberate exception to this project's usual JSON-everywhere pattern | Send `username`/`password` as form fields, not JSON; using `/docs`'s Authorize button handles this automatically |
| `401 Unauthorized`, `detail: "Not authenticated"` | No `Authorization` header sent at all | Log in via `/docs`'s Authorize button (or send `Authorization: Bearer <token>` manually) before calling a protected endpoint |
| `401 Unauthorized`, `detail: "Could not validate credentials"` | The token is malformed, was signed with a different `SECRET_KEY` than the one currently configured (e.g. the server restarted with a different env var value), or has expired | Log in again to get a fresh token; confirm `SECRET_KEY` hasn't changed between when the token was issued and now |
| `403 Forbidden`, `detail: "Role '...' is not permitted to perform this action"` | Correctly authenticated, but the current user's role isn't in the endpoint's `require_role(...)` allow-list | Expected behavior for the wrong role — log in as a user with a permitted role to proceed, or double-check the endpoint's `require_role(...)` call actually includes the roles it should |
| `AttributeError: module 'bcrypt' has no attribute '__about__'` | `passlib` was installed/used instead of this course's direct `bcrypt` usage, and it's hitting its known incompatibility with modern `bcrypt` | Use `bcrypt.hashpw`/`bcrypt.checkpw` directly, as shown in `app/security.py` — don't reintroduce `passlib` |
| `sqlalchemy.exc.ProgrammingError: relation "users" does not exist` | Day 3's `create_all` script wasn't re-run after adding the new `User` model, so the `users` table was never actually created | Run `python -m scripts.day3_create_tables` again — it will create `users`/`user_role` specifically, leaving every existing table untouched |
| `POST /auth/register` always returns `403`, even when logged in as `admin` | The very first admin account doesn't exist yet, so there's no way to authenticate as one to call this endpoint in the first place | Run `python -m scripts.day5_seed_users` once to bootstrap the demo accounts directly, bypassing the API |
| A newly registered user (via `POST /auth/register`) can't log in afterward | `hash_password(payload.password)` was skipped somewhere, and the plain password was stored directly, which then fails `bcrypt.checkpw`'s comparison against a non-bcrypt string | Confirm `User(... hashed_password=hash_password(payload.password) ...)` — never store `payload.password` directly |
| `jwt.exceptions.InvalidTokenError` or similar immediately on every request, even right after logging in | `SECRET_KEY`'s env var fallback differs between two running instances (e.g. one terminal tab's `$env:SECRET_KEY` set, another not) issuing and verifying with different keys | Confirm both are using the same `SECRET_KEY` value — check with `$env:SECRET_KEY` in each terminal tab, same reasoning as Day 3's `DATABASE_URL` scoping gotcha |

---
*RoboPulse Fleet Command Center — Day 5 of 13*
