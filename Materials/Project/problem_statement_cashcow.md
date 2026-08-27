# Problem Statement: "CashCow" Branch Operations Command Center

---

## 1. Business Context

**Meridian Trust Bank** operates a network of retail branches, each equipped with a shared pool of ATMs used for customer cash withdrawals and deposits. Currently, cash reserve levels, maintenance schedules, technician assignments, and service records are scattered across paper logs and spreadsheet files kept at each branch.

Branch operations leadership cannot easily answer crucial operational questions, making cash replenishment planning and maintenance scheduling difficult. As part of an operations modernization initiative, Meridian Trust Bank needs a **centralized, full-stack Command Center** to track ATM inventories, manage service call assignments, upload diagnostic reports, and monitor real-time ATM health across all branch locations.

---

## 2. Key Business Questions

The new system must allow operations admins and field technicians to easily answer the following analytical questions:

* **Low Cash Alert:** *Which active ATMs are operating below a 20% cash reserve across all branches?*
* **Co-Location Discrepancy:** *How many ATMs are assigned to field technicians who are NOT co-located at the same physical branch?*
* **Reliability Metrics:** *What is the service call completion/failure ratio broken down by ATM model?*
* **Maintenance Flags:** *Which branches have more than 30% of their ATMs currently flagged for maintenance?*
* **Reporting Lines:** *How many technicians reporting to a specific Regional Operations Supervisor have active service calls assigned to them?*

---

## 3. Data Architecture & Core Entities

```
+------------------+         +------------------+         +------------------+
|      Branch      | 1 --- * |        ATM       | 1 --- * |   Service Call   |
+------------------+         +------------------+         +------------------+
| id               |         | id               |         | id               |
| name             |         | serial_number    |         | title            |
| location_region  |         | model            |         | priority         |
| capacity         |         | status           |         | status           |
| supervisor_id    |         | cash_level       |         | atm_id           |
+------------------+         | branch_id        |         | technician_id    |
                             +------------------+         +------------------+
                                                                   | 1
                                                                   |
                                                                   * |
                                                          +------------------+
                                                          | Diagnostic Report|
                                                          +------------------+
                                                          | id               |
                                                          | file_url (S3)    |
                                                          | notes            |
                                                          | timestamp        |
                                                          +------------------+

```

### Entity Specifications

1. **Branches:** Physical sites housing ATM pools (`id`, `name`, `location_region`, `capacity`, `supervisor_id`).
2. **ATMs:** Individual cash machine units (`id`, `serial_number`, `model`, `status`: *Operational* | *Low-Cash* | *Maintenance* | *Offline*, `cash_level`, `facility_id`).
3. **Service Calls:** Refill/repair tasks assigned to ATMs (`id`, `title`, `priority`: *Low* | *Medium* | *Critical*, `status`: *Pending* | *In-Progress* | *Completed* | *Failed*, `atm_id`, `technician_id`).
4. **Diagnostic Reports:** Maintenance attachments and inspection files (`id`, `service_call_id`, `file_url`, `notes`, `created_at`).

---

## 4. Technical Requirements & System Features

### A. Role-Based Access Control (RBAC)

The application must secure endpoints and UI components using JWT-based authentication and role authorization:

* **Operations Admin:** Full CRUD permissions across branches, ATMs, service calls, and user accounts.
* **Field Technician:** Can view assigned ATMs, trigger service call status changes, and attach diagnostic reports.
* **Auditor (Read-Only):** Can view analytics dashboards, inspect data grids, and search system logs without write permissions.

### B. RESTful API & Analytics Layer (FastAPI + PostgreSQL)

* Implement clean REST endpoints following standard HTTP verbs and status codes.
* Design specific analytical endpoints executing SQL aggregation queries to answer the core business questions.
* Validate all request payloads and response bodies using **Pydantic v2** models.

### C. Responsive User Interface (React + Material UI)

* Build a clean UI using **Material UI (MUI)** layout components (`Grid`, `Box`, `Card`, `Container`).
* Utilize **MUI DataGrid** to display ATM and service call listings with support for live sorting, search filtering, and pagination.
* Provide an interactive dashboard displaying aggregated metric cards and status badges.
* Manage authentication and global session state using the React Context API.

### D. Cloud File & Document Management (AWS S3)

* Support diagnostic report attachments (images or `.txt`/`.pdf` logs).
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
cashcow/
├── backend/            # FastAPI app, SQLAlchemy models, Pydantic schemas
├── frontend/           # React + Vite + Material UI app
├── bin/
│   ├── setup.sh        # Dependency installation & environment initialization
│   └── seed.sh         # Script to seed PostgreSQL with mock branches, ATMs & users
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
2. **RBAC Walkthrough:** Demonstrating role restrictions (e.g., logging in as an *Operations Admin* to modify ATM assets vs. a *Field Technician* uploading an S3 diagnostic report).
3. **Data Grid & Analytical Dashboard:** Demonstrating live filtering, searching, and accurate metrics addressing the business questions.
4. **Codebase Architecture Tour:** A brief walk-through of Pydantic validation schemas, FastAPI dependencies (`Depends`), SQLAlchemy database sessions, and MUI state management.
