from typing import Any, AsyncGenerator

import pytest_asyncio
from asgi_lifespan import LifespanManager
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
