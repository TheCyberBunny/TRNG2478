# RoboPulse Fleet Command Center

A full-stack fleet management application for **Apex Robotics**,
tracking autonomous inspection rovers and aerial drones across global
facilities — built incrementally as the running demo project for this
course's full-stack curriculum (Python, FastAPI, PostgreSQL,
SQLAlchemy 2.0, React, Material UI, and AWS deployment).

This repository contains both the **complete, working application**
and a **`Materials/` folder** of day-by-day course documents for
students to reference.

\---

## Table of Contents

* [Business Context](#business-context)
* [Tech Stack](#tech-stack)
* [Repository Structure](#repository-structure)
* [Getting Started](#getting-started)
* [Running Tests](#running-tests)
* [Deployment](#deployment)
* [A Note on AWS Costs](#a-note-on-aws-costs)
* [Demo Accounts](#demo-accounts)
* [The Five Business Questions](#the-five-business-questions)
* [Materials Folder](#materials-folder)
* [For Students: Your Own Project](#for-students-your-own-project)

\---

## Business Context

Apex Robotics needed a centralized system to replace scattered
terminal logs and spreadsheets — tracking robot fleets, mission
assignments, diagnostic reports, and real-time operational health
across every facility. RoboPulse answers five specific analytical
questions fleet managers need daily (see
[The Five Business Questions](#the-five-business-questions) below),
secured behind role-based access control, and deployed entirely on
AWS's free-tier-eligible services.

\---

## Tech Stack

|Layer|Technology|
|-|-|
|Backend|Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async)|
|Database|PostgreSQL 16|
|Auth|JWT (`PyJWT`), `bcrypt` password hashing, role-based access control|
|Testing|`pytest`, `pytest-asyncio`, `httpx`|
|Frontend|React (Vite), Material UI (MUI), MUI X Data Grid, Axios|
|Cloud (Backend)|AWS Lambda (via `mangum`), Lambda Function URL|
|Cloud (Database)|AWS RDS (PostgreSQL)|
|Cloud (Frontend)|AWS S3 (static hosting) + AWS CloudFront (CDN)|
|Cloud (Storage)|AWS S3 (private bucket, via `boto3`)|
|Observability|AWS CloudWatch (Lambda logs, CloudFront metrics)|

> \*\*A deliberate deviation from a typical "AWS App Runner" tutorial:\*\*
> this project deploys its backend to \*\*AWS Lambda\*\*, not App Runner.
> App Runner has no free-tier allowance under either of AWS's current
> account models, while Lambda's request allowance is genuinely
> "Always Free," independent of account age. See `Materials/` for the
> full reasoning behind this decision.

\---

## Repository Structure

```
robo-pulse/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/         # Pydantic v2 request/response schemas
│   │   ├── routers/         # FastAPI route definitions
│   │   ├── config.py        # Centralized settings (pydantic-settings)
│   │   ├── database.py      # Async engine/session factory
│   │   ├── security.py      # Password hashing, JWT helpers
│   │   ├── dependencies.py  # Shared FastAPI dependencies (auth, DB session)
│   │   └── main.py          # FastAPI application entrypoint
│   ├── tests/                # pytest suite
│   ├── scripts/               # One-off setup/seed/verification scripts
│   ├── lambda\_handler.py     # AWS Lambda entrypoint (Mangum adapter)
│   ├── requirements.txt       # Full pinned dependencies (local dev)
│   ├── requirements-lambda.txt # Minimal deps for Lambda packaging
│   ├── .env.example           # Committed config template
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/               # Shared Axios client
│   │   ├── context/           # React Context API (auth state)
│   │   ├── components/        # Feature-organized React components
│   │   └── App.jsx
│   └── .env.production        # Points the built frontend at the deployed backend
├── db/
│   └── sql/                   # Raw SQL: schema, seed data, demo queries
├── bin/
│   ├── setup.sh                # One-command project setup
│   ├── seed.sh                 # Seed local or RDS database
│   └── test.sh                 # Run the backend test suite
├── Materials/                  # Course documents — see below
└── README.md
```

\---

## Getting Started

**Prerequisites:** Python 3.10+, Node.js (LTS), PostgreSQL 16, Git
(for Git Bash on Windows), Docker Desktop (only needed for AWS Lambda
packaging, not local development).

**One-command setup**, from the repository root, in Git Bash:

```bash
bash bin/setup.sh
```

This creates the backend virtual environment, installs backend and
frontend dependencies, and creates `backend/.env` from the committed
`.env.example` template if it doesn't already exist.

**Fill in real values in `backend/.env`** before continuing — at
minimum, your local PostgreSQL password and a generated `SECRET\_KEY`:

```powershell
python -c "import secrets; print(secrets.token\_hex(32))"
```

**Seed the database:**

```bash
bash bin/seed.sh local
```

**Run the backend:**

```powershell
cd backend
fastapi dev app/main.py
```

**Run the frontend**, in a second terminal:

```powershell
cd frontend
npm run dev
```

Visit `http://localhost:5173` and log in with one of the
[demo accounts](#demo-accounts) below.

\---

## Running Tests

```bash
bash bin/test.sh
```

This confirms a dedicated `robopulse\_test` database exists (creating
it if not) and runs the full `pytest` suite — entirely local, never
against `robopulse\_dev` or RDS.

\---

## Deployment

The live application is deployed as:

* **Backend:** AWS Lambda (`robopulse-api`), exposed via a Lambda
Function URL — no API Gateway
* **Database:** AWS RDS (PostgreSQL, `db.t3.micro`)
* **Frontend:** Built via `npm run build`, hosted on AWS S3 (static
website hosting), served through AWS CloudFront

Live URLs are account-specific and not included in this README —
see your own AWS Console (Lambda, RDS, and CloudFront) for your
deployment's actual endpoints. Full deployment steps, including the
Lambda packaging process (via Docker, to avoid cross-platform
dependency resolution issues) and the CloudFront/S3 configuration
gotchas encountered along the way, are documented in `Materials/`.

\---

## A Note on AWS Costs

This project is built to stay within AWS's free-tier allowances
wherever possible — but **AWS's free-tier terms are subject to
change**, and depend on your specific account's creation date and
plan. Before deploying:

* Set up an **AWS Budget alert** (Billing and Cost Management →
Budgets) before creating any AWS resources.
* Confirm current terms directly at aws.amazon.com/free rather than
assuming this README's assumptions still hold.
* **Stop the RDS instance** when not actively in use (AWS
auto-restarts a stopped instance after 7 days).
* See `Materials/` for the full reasoning behind every cost-relevant
configuration choice in this project.

\---

## Demo Accounts

Seeded via `backend/scripts/day5\_seed\_users.py` (included in
`bin/seed.sh`). **These are local development/demo credentials only —
never use these patterns in a real production system.**

|Username|Password|Role|
|-|-|-|
|`admin`|`AdminPass123!`|Fleet Admin (full CRUD)|
|`operator`|`OperatorPass123!`|Field Operator (view + trigger mission status changes)|
|`auditor`|`AuditorPass123!`|Auditor (read-only)|

\---

## The Five Business Questions

RoboPulse's analytical endpoints answer the five questions Apex
Robotics' fleet managers need daily:

|#|Question|Endpoint|
|-|-|-|
|1|Which active robots are below 20% battery?|`GET /robots?max\_battery=20`|
|2|Which missions assign a robot and operator at different facilities?|`GET /missions/discrepancies`|
|3|What's the mission success/failure ratio, by robot model?|`GET /missions/reliability`|
|4|Which facilities have >30% of their fleet in maintenance?|`GET /facilities/maintenance-flags`|
|5|How many operators under a given supervisor have active missions?|`GET /facilities/reporting-lines?supervisor\_id=...`|

Questions #1 and #2 are demonstrated repeatedly throughout
`Materials/`, across every layer of the stack (raw SQL, ORM, REST
endpoint, React component, automated test) — the deliberate running
example for the entire course. Questions #3–5 are implemented to the
same standard (a real, RBAC-aware ORM-backed endpoint, verified
against seeded data, plus a minimal frontend view), completed as a
standalone addition directly in this codebase — see
`app/routers/missions.py` (Question #3) and `app/routers/facilities.py`
(Questions #4 and #5), plus their matching components under
`frontend/src/components/analytics/`.

\---

## Materials Folder

```
Materials/
├── \_\_Problem\_Statement\_RoboPulse\_Fleet.txt
├── Day 1/
│   ├── day01\_notes.md
│   └── Day 01 Phase B Student Challenge.txt
├── Day 2/
│   ├── day02\_notes.md
│   └── Day 02 Phase B Student Challenge.txt
├── ...
├── Day 11/
│   ├── day11\_notes.md
│   └── Day 11 Phase B Student Challenge.txt
└── Project/
    ├── Problem\_Statement\_CashCow.md
    ├── Problem\_Statement\_AgriCore.md
    └── Problem\_Statement\_MedFlow.md
```

Each `Day N/` folder contains that unit's **notes** document — concept
deep dives, architectural reasoning, common pitfalls, and a
troubleshooting guide built from real issues encountered while
building this exact application — and that unit's **Phase B student
challenge** on its own. `\_\_Problem\_Statement\_RoboPulse\_Fleet.txt`, at the top level of
`Materials/`, is the original business problem this entire demo
project was built to solve — read it first for the full business
context behind every day's work.

`Project/` contains the three themed problem statements
(CashCow, AgriCore, MedFlow) — **your own actual assignment** is one
of these three, not RoboPulse itself. See
[For Students: Your Own Project](#for-students-your-own-project)
below.

Unit topics, in the order they appear in this repository (note: some
units were taught out of their originally-listed curriculum order —
see each unit's own notes for context):

|Folder|Topics|
|-|-|
|`Day 1`|Modern Python, syntax, data types, functions, flow control, classes \& OOP, pip \& virtual environments, modules|
|`Day 2`|PostgreSQL setup, schema design, primary/foreign keys, CRUD operations, joins \& aggregate queries|
|`Day 3`|Async SQLAlchemy ORM, `create\_all` table generation|
|`Day 4`|FastAPI setup \& routes, path/query parameters, request validation, dependency injection, OpenAPI docs|
|`Day 5`|Security \& RBAC, password hashing, JWT creation, OAuth route protection, protected endpoints, session context|
|`Day 6`|React \& MUI, Node.js \& Vite setup, JSX \& component structure|
|`Day 7`|Full-stack integration, Axios, CORS, MUI DataGrid, React Context API|
|`Day 8`|AWS core services, CLI \& IAM, RDS, S3, Python `boto3`|
|`Day 9`|AWS deployment: Lambda, S3 static hosting, CloudFront, CloudWatch|
|`Day 10`|Advanced FastAPI, database session dependencies, error handling, API endpoint unit testing|
|`Day 11`|Seed \& setup automation, Bash scripting, bug fixing, UI/UX enhancements|

\---

## For Students: Your Own Project

**RoboPulse is the demo project — not your assignment.** Your actual
project is your own assigned variant (CashCow, AgriCore, or MedFlow —
see `Materials/Project/`), built following the same day-by-day
pattern demonstrated here, against your own project's own entities and
business questions.

A guide to completing your own project's remaining analytical
endpoints (Reliability Metrics, Maintenance Flags, and Reporting
Lines) — using the patterns demonstrated throughout this repository —
will be added to `Materials/` separately. Check with your instructor
for evaluation criteria.

\---

*RoboPulse Fleet Command Center — built as the running demo project
for a full-stack Python/FastAPI/React/AWS curriculum.*

