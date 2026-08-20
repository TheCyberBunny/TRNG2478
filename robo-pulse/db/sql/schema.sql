-- Robopulse Command Center - Day 2 Schema

--this file exists because on Day 1 we modeled our facility, robot, mission, diagnostic log
--plans as plain python living only in local memory. The second the script ended, the data
--was gone. Today, we will give that data the same shape and give it a permanent home in
--Postgresql.
-- to Run: \i schema.sql

--Enums
CREATE TYPE robot_status AS ENUM ('Idle', 'In-Mission', 'Maintenance', 'Offline');
CREATE TYPE mission_priority AS ENUM ('Low', 'Medium', 'Critical');
CREATE TYPE mission_status AS ENUM ('Pending', 'In-Progress', 'Completed', 'Failed');

--Facilities Table
CREATE TABLE facilities (
    id SERIAL PRIMARY KEY, --auto-incrementing integer that Postgres will assign for us
    name VARCHAR(100) NOT NULL, --name may be reserved
    location_region VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    supervisor_id INTEGER NOT NULL
);

--Operators Table
CREATE TABLE operators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    facility_id INTEGER NOT NULL REFERENCES facilities(id) --FOREGIN KEY: every operator belongs to exactly one facility
);

--Robots table
CREATE TABLE robots (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50) NOT NULL UNIQUE, --UNIQUE: the database now enforces the 'no two robots share a serial number' as a rule
    model VARCHAR(100) NOT NULL,
    status robot_status NOT NULL DEFAULT 'Idle', --same as with vanilla python
    battery_level NUMERIC(5,2) NOT NULL CHECK (battery_level BETWEEN 0 AND 100), -- CHECK constraint is the database-level version of Day 1's robot._validate_battry()
    facility_id INTEGER NOT NULL REFERENCES facilities(id)
);

--Missions table
CREATE TABLE missions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    priority mission_priority NOT NULL,
    status mission_status NOT NULL DEFAULT 'Pending',
    robot_id INTEGER NOT NULL REFERENCES robots(id),
    operator_id INTEGER NOT NULL REFERENCES operators(id)
);

--Diagnostic logs table
CREATE TABLE diagnostic_logs (
    id SERIAL PRIMARY KEY,
    mission_id INTEGER NOT NULL REFERENCES missions(id),
    file_url TEXT NOT NULL, --TEXT: has no length cap, unlike VARCHAR, s3 bucket urls can be quite long
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW() --NOw() is re-evaluated at every INSERT
);

