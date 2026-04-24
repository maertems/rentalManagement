import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.main import app
from app.core.database import get_db, Base
from app.core.security import hash_password
from app.models import (  # noqa: F401 — ensures all tables are registered
    User, Owner, Place, PlacesUnit, PlacesUnitsRoom,
    Tenant, Rent, RentsFee, RentReceipt, RentReceiptsDetail,
)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "mysql+asyncmy://rental:rental@mysql:3306/rental_test"
)

_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
_session_factory = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin1234"


async def override_get_db():
    async with _session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_database():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_tables():
    yield
    async with _session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"DELETE FROM `{table.name}`"))
        await session.commit()


async def _seed_admin() -> User:
    async with _session_factory() as session:
        admin = User(
            email=ADMIN_EMAIL,
            passwordHash=hash_password(ADMIN_PASSWORD),
            isAdmin=1,
            verified=1,
            name="Test Admin",
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        return admin


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session")
async def authedClient(client: AsyncClient):
    """An AsyncClient pre-authenticated as the seeded admin (cookies stored in the client's jar)."""
    await _seed_admin()
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return client
