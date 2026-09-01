"""
Robopulse Command Center
Day 10 - shared pytest fixture: an isolated test database, a dependency-overriden FastAPI test client
and JWT helpers for testing each RBAC role without hitting any real /auth/token endpoints on every test
"""

import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.dependencies import get_db
from app.main import app
from app.models import Base, Facility, User, UserRole
from app.security import create_access_token, hash_password

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:password@127.0.0.1:5432/robopulse_test"
)

#a separate async engine/session factory just for tests
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

"""
runs once per test function that requests it. It builds a fresh, empty schema before
each test runs, yields a session for the test body to use, then tears the schema back
down afterward; this way, every test starts from a guaranteed clean and identical db
state with no leftover rows from the previous test.
"""
@pytest_asyncio.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

"""
This function depends on the db_session and it swaps out the app's real get_db
dependency for one that always returns the test session.
"""
@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    #ASGITransport lets AsyncClient speak directly to the FastAPI app in-process,
    #over a real ASGI interface with no actual network socket (no running server required)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

"""
Creates one User ber RBAC role directly via the ORM, that way the tests have real
accounts with generated tokens without needing a working /auth/register call for 
each one
"""    
@pytest_asyncio.fixture
async def seeded_users(db_session):
    users = {
        "admin" : User(username="test_admin", hashed_password=hash_password("pw"), role=UserRole.FLEET_ADMIN),
        "operator" : User(username="test_operator", hashed_password=hash_password("pw"), role=UserRole.FIELD_OPERATOR),
        "auditor" : User(username="test_auditor", hashed_password=hash_password("pw"), role=UserRole.AUDITOR),
    }
    for user in users.values():
        db_session.add(user)
    await db_session.commit()
    for user in users.values():
       await db_session.refresh(user)
    return users

"""
Here I will create a miniman Facility row - many endpoints (creating a robot) require a valid
facility_id in order to satisfy our foreign key constraints. 
"""
@pytest_asyncio.fixture
async def seeded_facility(db_session):
    facility = Facility(name="Test Facility", location_region="Test Region", capacity=10, supervisor_id=1)
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    return facility

"""
A plain helper function that builds a real JWT for a given seeded user using the same create_access_token
function that we use in /auth/token, this way any test can simulate a 'logged in user as role' without
actually making a login request each time
"""
def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": user.username, "role":user.role.value})
    return {"Authorization" : f"Bearer {token}"}