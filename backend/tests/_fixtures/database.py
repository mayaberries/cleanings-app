import os
import warnings
from typing import Any, AsyncGenerator

import alembic
import pytest_asyncio
from alembic.config import Config
from asgi_lifespan import LifespanManager
from databases import Database
from fastapi import FastAPI


@pytest_asyncio.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


@pytest_asyncio.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application
    return get_application()


@pytest_asyncio.fixture
async def initialized_app(app: FastAPI) -> AsyncGenerator[FastAPI, Any]:
    """
    Runs the app's startup/shutdown handlers (app/core/tasks.py) -- this is
    what actually populates app.state._db, not the bare `app` fixture
    above. `db` and `client` both depend on this now (instead of `client`
    being the only thing that ever started the lifespan), so requesting
    either one alone is enough to get a working database connection.
    pytest caches this fixture per test, so even though both `db` and
    `client` request it, LifespanManager(app) is only ever entered once --
    connect_to_db() (app/db/tasks.py) assigns a fresh Database to
    app.state._db on every call, so entering it twice per test would leak
    a connection pool and silently replace the first one.
    """
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture
def db(initialized_app: FastAPI) -> Database:
    return initialized_app.state._db