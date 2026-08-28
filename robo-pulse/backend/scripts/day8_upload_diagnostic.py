"""
Robopulse Command Center
Day 8 - this uploads a diagnostic report file to S3 using boto3 SDK,
then creates a matching DiagnosticLog row (Day 3's async ORM setup)
pointing at the REAL S3 url - thus fulfilling problem statement's storage
architecture for the first time.

Run from backend/ with .venv active:
    python -m scripts.day8_upload_diagnostic.py
"""

import asyncio
import boto3

from app.database import AsyncSessionLocal
from app.models import DiagnosticLog

BUCKET_NAME = "robopulse-diagnostics-km2478"
LOCAL_FILE_PATH = "scripts/sample_diagnostic.txt"
#the s3 key is just a path within the s3 bucket where the file will be stored
S3_KEY = "diagnostics/rx1001-002.txt"

#a function to upload the file to the s3 bucket and return the s3 url
def upload_to_s3() -> str:
    s3_client = boto3.client("s3")
    s3_client.upload_file(LOCAL_FILE_PATH, BUCKET_NAME, S3_KEY)
    return f"s3://{BUCKET_NAME}/{S3_KEY}"

#async function to record the diagnostic log in the database
async def record_diagnostic_log(file_url: str) -> None:
    async with AsyncSessionLocal() as session:
        log = DiagnosticLog(
            mission_id=1,
            file_url=file_url,
            notes="Uploaded via the Day 8 boto3 demo script.",
        )

        session.add(log)
        await session.commit()
        await session.refresh(log)
        print(f"Created DiagnosticLog id={log.id}, file_url={log.file_url}")

#async main function to run the uplaod and record the log
async def main() -> None:
    file_url = upload_to_s3()
    print(f"Uploaded to {file_url}")
    await record_diagnostic_log(file_url)

if __name__ == "__main__":
    asyncio.run(main())