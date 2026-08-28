# Day 8 — Notes
## Week 3, Monday: AWS Core Services, AWS CLI & IAM, AWS RDS, AWS S3, Python Boto3 SDK

---

## Executive Summary

Weeks 1–2 built RoboPulse entirely on `localhost`. Today it gets a
real cloud foundation: a secured AWS account, a managed PostgreSQL
database (RDS) standing in for the local one, a private file store
(S3), and Python code (`boto3`) that talks to AWS directly for the
first time — specifically to fulfill the problem statement's
diagnostic-log storage requirement, left as an unfulfilled placeholder
since Day 1.

This was also, by a wide margin, the most operationally eventful day
of the course so far — not because the *concepts* were unusually hard,
but because cloud infrastructure introduces a category of failure mode
Weeks 1–2 never had to deal with: **console configuration decisions
that silently succeed while being wrong**, discoverable only later, in
a completely different step. Today's real incidents — a login boundary
mixed up between root and an IAM user, an RDS instance created with no
actual database inside it, an access-key setup that turned out to be
temporary SSO credentials rather than a permanent key, and — for the
third time this course — `DATABASE_URL` silently pointing at the wrong
database — are documented in detail below, both because each is
individually a common real-world AWS mistake, and because together
they reinforce a single lesson worth stating plainly: **in cloud
infrastructure work, "the command didn't error" is never sufficient
confirmation on its own.**

---

## Deep Dive: AWS Core Services

- **RDS, S3, and IAM** are today's three services; **CloudFront**
  arrives Day 9 to front the S3-hosted frontend. **AWS App Runner** —
  the problem statement's original backend host — does not appear in
  this course's plan at all going forward; see the Architectural
  Analysis below for the full reasoning, but the short version is that
  it has no free allowance under either AWS account model, and **AWS
  Lambda** (genuinely "Always Free," regardless of account age) takes
  its place starting Day 9.
- **The "managed service" idea, stated plainly.** RDS isn't just
  "PostgreSQL, but AWS hosts it" — AWS also handles automated backups,
  patching, and (if configured) failover, none of which Day 2's local
  install had to think about at all. This is the general shape of
  every AWS "managed" service this course touches: less manual
  operational work, in exchange for working within that service's
  specific configuration surface (today's RDS console wizard, rather
  than `psql`'s installer).

---

## Deep Dive: AWS CLI & IAM

- **Root vs. IAM user, restated with today's real incident in mind.**
  Root has unrestricted access to everything, including billing — the
  reason Steps 1–2 (MFA, Budget) had to use it, since only root can
  reach the Billing console by default. Every step from Step 4 onward
  was supposed to switch to a dedicated IAM user instead — and today's
  live session initially missed that explicit switch, which is exactly
  why the demo doc now states it directly rather than leaving it
  implied. The general principle: **root should be used as rarely as
  possible, for the smallest number of account-level tasks, and
  nothing else.**
- **Classic IAM users vs. IAM Identity Center — a real, structural
  difference, not just two menus for the same thing.** Today's live
  session surfaced this distinction directly: a **classic IAM user**
  (IAM Console → Users) can have a genuinely **permanent** access key
  — two values, an Access Key ID and a Secret Access Key, that never
  expire on their own. An **IAM Identity Center** user (AWS's newer,
  SSO-based system) can *only* ever be issued **temporary** credentials
  — three values (Access Key ID, Secret Access Key, and a **session
  token**), always time-boxed, by design. These aren't interchangeable
  configurations of the same underlying thing; dropping the session
  token from an Identity Center credential set doesn't make it
  permanent, it just makes it broken.
- **Two separate clocks, easy to conflate.** An Identity Center
  **portal session** (how long you stay logged into the AWS access
  portal itself) and the **permission set's session duration** (how
  long *credentials issued through that portal* remain valid for
  CLI/SDK use) are governed independently — today's live session had
  7+ hours left on the portal side while the actual CLI credentials
  had already expired, because the permission set's session duration
  defaulted to a much shorter window. Raising that duration
  (IAM Identity Center → Permission sets → Settings → Session
  duration) is the fix that actually reduces how often this recurs —
  changing the portal session length would not have helped at all.
- **Credential resolution has a priority order.** `boto3` and the AWS
  CLI check several places for credentials, in a fixed order —
  environment variables (`AWS_ACCESS_KEY_ID`, etc.) are checked
  *before* the `~/.aws/credentials` file, which is checked before an
  attached IAM role. A stale, hardcoded credential sitting in an
  environment variable (or an unintended `[default]` profile) silently
  wins over a correctly-configured SSO profile sitting right next to
  it — today's `ExpiredToken` error was ultimately this exact
  resolution-order issue, not a problem with the SSO setup itself.
  `$env:AWS_PROFILE` is the explicit override that tells both tools
  which *named* profile to use instead of guessing from `default`.

---

## Deep Dive: AWS RDS

- **Free-tier-conscious settings, and why each one matters.**
  `db.t3.micro`/`t4g.micro` (smallest instance class), Single-AZ (not
  Multi-AZ, which roughly doubles cost), `gp3` storage with no
  Provisioned IOPS, and a security group scoped to "My IP" rather than
  `0.0.0.0/0` — every one of these is both a cost-control decision and,
  for the security group specifically, a real security practice
  independent of cost (a database open to the entire internet is a bad
  idea regardless of what it costs to run).
- **A genuinely common, silent-until-later RDS mistake: the "Initial
  database name" field.** Leaving it blank during creation doesn't
  produce any error — the instance provisions successfully either way,
  with only the built-in default `postgres` database inside it. The
  failure only surfaces later, the first time something tries to
  connect to the *named* database that was never actually created
  (today's live `InvalidCatalogNameError`). The fix (`CREATE DATABASE
  robopulse;` against the default `postgres` database) is trivial once
  identified — the harder part is knowing to look there at all, since
  the RDS console gives no warning that the field was left empty.
- **Stopping vs. deleting.** A stopped RDS instance isn't billed for
  compute (only storage), but AWS automatically restarts any stopped
  instance after 7 days — a deliberate design decision on AWS's part
  to prevent a database from being "stopped" indefinitely and quietly
  drifting out of patch/maintenance compliance. This needs to be
  actively re-checked periodically for the rest of this course, not
  set once and forgotten.
- **No built-in way to browse table contents from the Console.**
  AWS's "Query Editor" — a feature that does show live SQL results
  directly in the browser — exists *only* for Aurora clusters with the
  Data API enabled, never for standard "RDS for PostgreSQL" (what
  today's instance actually is). The RDS Console's Monitoring tab
  (`DatabaseConnections`, specifically) offers a lightweight,
  console-native *supplementary* signal that a connection happened,
  but confirming actual data requires a real SQL client — `psql`,
  exactly as Day 2 already established.

---

## Deep Dive: AWS S3

- **Global bucket-name uniqueness.** Bucket names are unique across
  *all* of AWS, not just one account — a plain, obvious name is
  essentially guaranteed to already be taken, which is why today's
  bucket name needed an arbitrary distinguishing suffix.
- **Private by default.** New buckets block all public access
  automatically — today's diagnostic-log bucket needed no additional
  configuration to satisfy the problem statement's "Private Document
  Bucket" requirement; the risk would only appear if that default were
  deliberately changed later.
- **Genuinely, unambiguously free at this course's scale.** Unlike
  RDS, S3 storage up to 5GB is on AWS's "Always Free" list regardless
  of account age or credit balance — the one piece of today's setup
  where "free tier" and "actually free, indefinitely" mean the exact
  same thing.

---

## Deep Dive: Python Boto3 SDK

- **No credentials in code, ever.** `boto3.client("s3")` was created
  today with zero credentials passed explicitly — it resolves them
  automatically through the same priority-ordered lookup described
  above. This mirrors every prior "never hardcode a secret" lesson
  this course has taught (Day 5's `SECRET_KEY`, Day 3's
  `DATABASE_URL`) — extended today to a category of secret (AWS
  credentials) where the consequences of a leak are considerably
  larger.
- **Sync in an async project, and why that's fine.** `boto3` doesn't
  have first-class async support the way `asyncpg` does — today's
  `upload_file(...)` and `list_objects_v2(...)` calls are ordinary
  blocking calls, sitting comfortably alongside `async def` functions
  in the same script, as long as the blocking call isn't made *from
  inside* an `async def` trying to `await` it. Not every I/O operation
  in this project needs to be async — only the ones already wired
  through SQLAlchemy's async engine.
- **Pagination is opt-in, not automatic.** `list_objects_v2` caps out
  at 1,000 results per call; a script that doesn't explicitly use a
  paginator will silently stop seeing results beyond that limit, with
  no error — the same class of "quietly wrong, not loudly broken"
  failure mode as most of today's other real incidents.

---

## Architectural Analysis

Today's single most consequential decision — swapping AWS App Runner
for AWS Lambda, starting Day 9 — was made *before* touching the AWS
Console at all, based on a direct, current-as-of-today search of AWS's
own free-tier terms rather than assumed knowledge. This is worth
naming as a methodology, not just an outcome: AWS's pricing and
free-tier structure genuinely changed in July 2025, materially enough
that a plan based on stale information would have led this course
toward services that no longer behave the way older tutorials
describe. The specific reasoning — Lambda's "Always Free" status is
independent of account age, unlike RDS/EC2/App Runner under the newer
account model — is the kind of decision that needs to be re-verified
against current terms, not assumed to hold indefinitely, if this
course is ever revisited again later.

Step 7's zero-code-change swap of `DATABASE_URL` from local to RDS is
the clearest possible payoff of a bet made all the way back on Day 3.
Three separate days' worth of tooling — Day 2's raw `seed.sql`, Day
3's ORM-driven `create_all`, Day 5's user-seeding script — all worked
unmodified against a brand-new managed database, purely because none
of them ever hardcoded *where* the database lived. It's worth
connecting this directly to today's actual recurring failure mode: the
same design that made the swap effortless is *also* exactly what makes
it easy to silently run a script against the wrong database if the
environment variable isn't re-confirmed in the terminal actually being
used. Flexibility and this specific footgun are two sides of the same
design decision, not unrelated facts.

The Phase B reconciliation script extends a theme first introduced by
Day 2's foreign keys and Day 3's `checkfirst` discussion: **two
independent systems that are each individually correct can still
disagree with each other.** Day 2 solved this within a single
database via foreign key constraints, enforced automatically. Today's
S3-vs-database situation has no equivalent automatic enforcement
mechanism at all — nothing stops a `DiagnosticLog` row and its
matching S3 object from drifting out of sync, which is exactly why a
reconciliation script has to exist as a *separate*, deliberately
written piece of logic. This is a genuinely common shape of problem in
real-world systems that span more than one storage technology, not a
RoboPulse-specific quirk.

---

## Common Pitfalls & Anti-Patterns

- **Doing post-IAM-user-creation console work while still logged in as
  root.** Nothing prevents this technically (root can do anything),
  but it defeats the purpose of creating a narrower user in the first
  place — worth an explicit, deliberate sign-out/sign-in switch, not
  an assumption that it'll happen naturally.
- **Leaving RDS's "Initial database name" field blank.** No error at
  creation time; a confusing `InvalidCatalogNameError` much later, the
  first time anything tries to actually connect.
- **Treating a successful exit code as confirmation of correctness.**
  Restated because it mattered concretely today, twice: Step 6's
  seeding commands would have looked identical whether they landed in
  `robopulse` or nowhere, and today's verify script produced a
  clean, error-free report while quietly querying the wrong database
  entirely.
- **`pip install` (or, on Day 6, `npm install`) run without confirming
  the active environment first.** The same underlying mistake, now
  seen on both halves of this project's stack — a package manager
  installs into whatever environment is currently active, silently,
  with no warning if that's not the one intended.
- **Copy-pasting three-part temporary credentials (access key + secret
  key + session token) and treating them as if they were a permanent
  two-part access key.** They cannot be converted into permanent
  credentials by omitting the session token — a fundamentally
  different, always-temporary credential type by design.
- **Assuming a long portal session means long-lived CLI credentials.**
  Two independently-configured durations; confirm the *permission
  set's* session duration specifically if credentials are expiring
  faster than expected.
- **`$env:DATABASE_URL` (or any `$env:` variable) assumed to persist
  across terminal tabs or sessions.** This is the third time this
  specific mistake has appeared in this course (Day 3, Day 5, and
  today) — worth treating as a standing habit to check first, not a
  surprising outcome each time it happens again.

---

## Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| `asyncpg.exceptions.InvalidCatalogNameError: database "robopulse" does not exist` | RDS's "Initial database name" field was left blank during creation | Connect to the instance's default `postgres` database and run `CREATE DATABASE robopulse;`, then retry |
| `botocore.exceptions.ClientError: ... (ExpiredToken) ...` | Temporary SSO/Identity Center credentials expired, or a stale credential (env var or `[default]` profile) is being picked up ahead of a valid one | Check `Get-Content $HOME\.aws\credentials`/`config` for stale entries; run `aws sso login --profile <name>` for a fresh token; set `$env:AWS_PROFILE` explicitly; confirm with `aws sts get-caller-identity` before retrying the script |
| CLI credentials expire much sooner than the AWS access portal session does | The permission set's session duration (separate from the portal session length) defaults to a short window | IAM Identity Center → Permission sets → Settings → raise Session duration (up to 12 hours) |
| `robopulse-admin` (or any user) doesn't appear anywhere in the IAM Console | The user is an IAM Identity Center user, not a classic IAM user — a different service with a different console page entirely | Check "IAM Identity Center" in the console search bar instead of "IAM" |
| Script runs cleanly, but reports results that don't match what's actually in RDS (e.g., everything shows as Broken/Orphaned unexpectedly) | `DATABASE_URL` wasn't set to the RDS connection string in the terminal the script actually ran in, so it silently queried the local database instead | Run `$env:DATABASE_URL` with no value to print its current setting before running any script; re-set it explicitly if wrong or blank |
| `ModuleNotFoundError: No module named 'boto3'` despite `pip install boto3` reporting success | The venv wasn't active (or the wrong directory was active) at install time, so it installed into the global Python instead | Confirm `(.venv)` in the prompt and `Get-Location` ends in `...\backend` before reinstalling |
| `aws s3 mb` fails with a bucket-already-exists-style error | Bucket names are globally unique across all of AWS, not just this account | Append a more distinguishing suffix and retry |
| `Get-ChildItem Env: \| Where-Object { $_.Name -like "AWS_*" }` throws a syntax error | A dropped underscore (`$_.Name` mistyped or corrupted in copy/paste) | Use the simpler `Get-ChildItem env:AWS*` instead — same result, no `Where-Object` needed |
| RDS Console shows no way to browse actual table data | Expected — the Query Editor feature only exists for Aurora clusters with the Data API enabled, never standard RDS PostgreSQL | Use `psql` (Step 8) for real verification; the Monitoring tab's `DatabaseConnections` graph is a supplementary signal only, not a data browser |

---
*RoboPulse Fleet Command Center — Day 8 of 13*
