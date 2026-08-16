import os
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

pytest_plugins = [
    "tests._fixtures.users",
    "tests._fixtures.database",
    "tests._fixtures.profiles",
    "tests._fixtures.pets",
    "tests._fixtures.services",
    "tests._fixtures.clinic_api_key",
    "tests._fixtures.rate_limit",
]


@pytest_asyncio.fixture
async def client(initialized_app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with AsyncClient(
            transport=ASGITransport(app=initialized_app),
            base_url="http://testserver",
            headers={"Content-Type": "application/json"}
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _infra_smoke_check():
    """
    Runs once, before any other fixture or test in the suite. Checks the
    two things that, when broken, break *every single test* in an
    identical way (bad FastAPI app construction, unreachable test DB) --
    and if either fails, aborts the whole session immediately with one
    clear message instead of letting every test error out individually.

    This is intentionally separate from `apply_migrations`/`app`/`db` in
    tests/_fixtures/database.py -- those are real fixtures tests build on.
    """
    os.environ["TESTING"] = "1"

    try:
        from app.api.server import get_application
        get_application()
    except Exception as exc:
        pytest.exit(
            f"\n\nINFRA SMOKE CHECK FAILED: app could not be built.\n{exc!r}\n",
            returncode=1,
        )

    try:
        from databases import Database
        from app.core.config import DATABASE_URL

        db = Database(str(DATABASE_URL))  # base DB, e.g. postgres_super/postgres — always exists
        await db.connect()
        await db.disconnect()
    except Exception as exc:
        pytest.exit(
            f"\n\nINFRA SMOKE CHECK FAILED: test DB unreachable.\n{exc!r}\n",
            returncode=1,
        )
        
    yield
