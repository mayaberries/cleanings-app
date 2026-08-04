from typing import Any, AsyncGenerator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

pytest_plugins = [
    "tests._fixtures.users",
    "tests._fixtures.database",
    "tests._fixtures.services"
]


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with LifespanManager(app):
        async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
                headers={"Content-Type": "application/json"}
        ) as client:
            yield client

