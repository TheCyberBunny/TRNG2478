# Problem Statement: "AgriCore" Farm Operations Command Center

---

## 1. Business Context

**Prairie Crest Agricultural Cooperative** operates a network of member farms and grain elevator sites that share a common pool of heavy equipment — tractors, combines, sprayers, and irrigation pumps. Currently, equipment usage logs, maintenance schedules, farmhand assignments, and field job records are scattered across paper logs and spreadsheet files kept at each site.

Cooperative operations leadership cannot easily answer crucial operational questions, making equipment utilization and maintenance planning difficult. As part of an operations modernization initiative, Prairie Crest Agricultural Cooperative needs a **centralized, full-stack Command Center** to track equipment inventories, manage field job assignments, upload service/diagnostic reports, and monitor real-time equipment health across all member farm sites.

---

## 2. Key Business Questions

The new system must allow farm operations admins and field hands to easily answer the following analytical questions:

* **Low Fuel Alert:** *Which active equipment units are operating below a 20% fuel level across all farms?*
* **Co-Location Discrepancy:** *How many equipment units are assigned to farmhands who are NOT co-located at the same physical farm?*
* **Reliability Metrics:** *What is the field job completion/failure ratio broken down by equipment model?*
* **Maintenance Flags:** *Which farms have more than 30% of their equipment currently flagged for maintenance?*
* **Reporting Lines:** *How many farmhands reporting to a specific Regional Agronomy Supervisor have active field jobs assigned to them?*

---

## 3. Data Architecture & Core Entities

```
+------------------+         +------------------+         +------------------+
|       Farm       | 1 --- * |     Equipment    | 1 --- * |    Field Job     |
+------------------+         +------------------+         +------------------+
| id               |         | id               |         | id               |
| name             |         | serial_number    |         | title            |
| location_region  |         | model            |         | priority         |
| capacity         |         | status           |         | status           |
| supervisor_id    |         | fuel_level       |         | equipment_id     |
+------------------+         | facility_id      |         | operator_id      |
                             +------------------+         +------------------+
                                                                   | 1
                                                                   |
                                                                   * |
                                                          +------------------+
                                                          |  Service Report  |
                                                          +------------------+
                                                          | id               |
                                                          | file_url (S3)    |
                                                          | notes            |
                                                          | timestamp        |
                                                          +------------------+

```

### Entity Specifications

1. **Farms:** Physical sites housing equipment pools (`id`, `name`, `location_region`, `capacity`, `supervisor_id`).
2. **Equipment:** Individual heavy machinery units (`id`, `serial_number`, `model`, `status`: *Idle* | *In-Use* | *Maintenance* | *Retired*, `fuel_level`, `facility_id`).
3. **Field Jobs:** Planting, spraying, and harvest tasks assigned to equipment (`id`, `title`, `priority`: *Low* | *Medium* | *Critical*, `status`: *Pending* | *In-Progress* | *Completed* | *Failed*, `equipment_id`, `operator_id`).
4. **Service Reports:** Maintenance attachments and inspection files (`id`, `field_job_id`, `file_url`, `notes`, `created_at`).

---

## 4. Technical Requirements & System Features

### A. Role-Based Access Control (RBAC)

The application must secure endpoints and UI components using JWT-based authentication and role authorization:

* **Farm Operations Admin:** Full CRUD permissions across farms, equipment, field jobs, and user accounts.
* **Field Hand:** Can view assigned equipment, trigger field job status changes, and attach service reports.
* **Auditor (Read-Only):** Can view analytics dashboards, inspect data grids, and search system logs without write permissions.

### B. RESTful API & Analytics Layer (FastAPI + PostgreSQL)

* Implement clean REST endpoints following standard HTTP verbs and status codes.
* Design specific analytical endpoints executing SQL aggregation queries to answer the core business questions.
* Validate all request payloads and response bodies using **Pydantic v2** models.

### C. Responsive User Interface (React + Material UI)

* Build a clean UI using **Material UI (MUI)** layout components (`Grid`, `Box`, `Card`, `Container`).
* Utilize **MUI DataGrid** to display equipment and field job listings with support for live sorting, search filtering, and pagination.
* Provide an interactive dashboard displaying aggregated metric cards and status badges.
* Manage authentication and global session state using the React Context API.

### D. Cloud File & Document Management (AWS S3)

* Support service report attachments (images or `.txt`/`.pdf` logs).
* Upload files directly to an **AWS S3** bucket using Python's `boto3` SDK from the FastAPI backend and store secure media S3 URLs in PostgreSQL.

---

## 5. Technology Stack & Deployment Architecture

| Tier | Required Technology | Deployment Target |
| --- | --- | --- |
| **Frontend** | React (Vite) + Material UI (MUI) | **AWS S3** (Static Hosting) + **AWS CloudFront** (CDN) |
| **Backend** | Python 3.10+ + FastAPI + Pydantic v2 | **AWS EC2** (application server) + **AWS Lambda** (serverless functions) |
| **Database** | PostgreSQL + SQLAlchemy 2.0 | **AWS RDS** (Managed PostgreSQL) |
| **Storage** | Python `boto3` SDK | **AWS S3** (Private Document Bucket) |

---

## 6. Repository Automation & Helper Scripts

Participants must organize their project repository with standard automation scripts in a `bin/` directory:

```text
agricore/
├── backend/            # FastAPI app, SQLAlchemy models, Pydantic schemas
├── frontend/           # React + Vite + Material UI app
├── bin/
│   ├── setup.sh        # Dependency installation & environment initialization
│   └── seed.sh         # Script to seed PostgreSQL with mock farms, equipment & users
└── README.md           # Setup and API documentation

```

### Script Requirements

* **`bin/setup.sh`**: Initializes the Python virtual environment (`venv`), installs `requirements.txt` and `npm` packages, and prepares local `.env` files.
* **`bin/seed.sh`**: Seeds the target database (local or AWS RDS) with realistic initial mock data for testing.

-------------------------------------------------------------------------------------------------
## 7. Deliverables & Day 13 Showcase Expectations

By the conclusion of the workshop, participants must present a working deployment during the Day 13 final showcase. Each participant will have a **10-minute time slot** to present their solution.

### Showcase Evaluation Criteria

1. **Live Cloud URL:** Walking through the application hosted live on AWS CloudFront connected to the backend on AWS EC2/Lambda and AWS RDS.
2. **RBAC Walkthrough:** Demonstrating role restrictions (e.g., logging in as a *Farm Operations Admin* to modify equipment assets vs. a *Field Hand* uploading an S3 service report).
3. **Data Grid & Analytical Dashboard:** Demonstrating live filtering, searching, and accurate metrics addressing the business questions.
4. **Codebase Architecture Tour:** A brief walk-through of Pydantic validation schemas, FastAPI dependencies (`Depends`), SQLAlchemy database sessions, and MUI state management.
