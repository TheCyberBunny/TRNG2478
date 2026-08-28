"""
Robopulse Command Center
Day 8 - phase b answer key
reconcile diagnostic_logs against what acually exists in s3. Two independent
sources of truch (the db claim, and the s3 reality) can drift; this script
finds where they disagree

Run from /backend with .venv active, DATABASE_URL pointed at RDS
    python -m scripts.day8_verify_diagnostics
"""

import asyncio
import boto3
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import DiagnosticLog

BUCKET_NAME = "robopulse-diagnostics-km2478"
DIAGNOSTICS_PREFIX = "diagnostics/"

def extract_s3_key(file_url: str) -> str:
    """
    s3://bucket-name/diagnostics/rx1001-002.txt -> diagnostics/rx1001-002.txt

    Strips the scheme and bucket name, keeping only the actual object key aka the part
    that has a match what list_objects_v2 returns
    """
    without_scheme = file_url.removeprefix("s3://")
    #the _ is the bucket name, the second _ is the slash after the bucket name, and the key is the rest
    _, _, key = without_scheme.partition("/")
    return key

def list_s3_keys(bucket_name: str, prefix: str) -> set[str]:
    s3_client = boto3.client("s3")

    """
    uses a paginator rather than a single list_objects_v2() call -
    list_objects_v2 caps out at 1,000 keys per response; a paginator
    automatically follows the continuation token for anything beyond that,
    so this stays correct even as a bucket grows
    """
    paginator = s3_client.get_paginator("list_objects_v2")

    #accumulate all the keys in a set so we can do operations later
    keys: set[str] = set()
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.add(obj["Key"])
    return keys

#async function to fetch all diagnostic logs from the db
async def fetch_diagnostic_logs() -> list[DiagnosticLog]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DiagnosticLog))
        return list(result.scalars().all())

#a function to compare the s3 keys against the database rows and print the results
async def main() -> None:
    s3_keys = list_s3_keys(BUCKET_NAME, DIAGNOSTICS_PREFIX)
    logs = await fetch_diagnostic_logs()

    healthy: list[DiagnosticLog] = []
    broken: list[DiagnosticLog] = []
    referenced_keys: set[str] = set()

    for log in logs:
        key = extract_s3_key(log.file_url)
        referenced_keys.add(key)
        if key in s3_keys:
            healthy.append(log)
        else:
            broken.append(log)

    orphaned_keys = s3_keys - referenced_keys

    print("== Healthy (database row + matching s3 file)==")
    if not healthy:
        print(" None Found ")
    for log in healthy:
        print(f"DiagnosticLog {log.id}: {log.file_url}")

    print("== Broken (database row, no matching file) ==")
    if not broken:
        print(" None Found ")
    for log in broken:
        print(f"DiagnosticLog {log.id}: {log.file_url}")

    #Bonus section, per the research prompts - not strictly required
    print("== Orphaned (file in s3, but no matching database row) == ")
    if not orphaned_keys:
        print("None found")
    for key in orphaned_keys:
        print(f"s3://{BUCKET_NAME}/{key}")

if __name__ == "__main__":
    asyncio.run(main())


