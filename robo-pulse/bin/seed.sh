#! /usr/bin/env bash
#this file handles seeding our app data in the database or rds in the correct order
#(schema first, then business data, then user accounts)
#To run this file, we have 2 commands:
# bash bin/seed.sh local (this is the default if no argument is given)
# bash bin/seed.sh rds


# $1 is referring to the first argument typed after the script name
TARGET="{$1:local}"

#answers the question, which db are we seeding?
if [ "$TARGET" == "local" ]; then

    ##TODO: Replace the details in the db url below with YOUR details
    export DATABASE_URL="postgresql+asyncpg://postgres:<your-password>@127.0.0.1:5432/robopulse_dev"
    PSQL_HOST="127.0.0.1"
    PSQL_DB="robopulse_dev"
elif [ "$TARGET" == "rds" ]; then

    ##TODO: Replace the details in the db url with YOUR REMOTE RDS details
    export DATABASE_URL="postgresql+asyncpg://<user>:<password>@<your-rds-endpoint>:5432/robopulse"
    PSQL_HOST="<your-rds-endpoint>"
    PSQL_DB="robopulse"

else 
#anything other than local or rds gets handled
    echo "Usage: bin/seed.sh [local|rds]"
    exit 1
fi

echo "Seeding target: $TARGET"

cd backend

#step 1: creating the db tables
python -m scripts.day3_create_tables

#step 2: load the core business data
psql -h "$PSQL_HOST" -U postgres -d "$PSQL_DB" -f ../db/sql/seed.sql

#step 3: load the RBAC demo users
python -m scripts.day5_seed_users

echo "Seed complete for $TARGET"