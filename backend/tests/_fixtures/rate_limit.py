import pytest_asyncio

from app.core.limiter import reset_public_rate_limits


@pytest_asyncio.fixture(autouse=True)
def reset_public_rate_limiters():
    """
    The rate limiter's storage backend (app/core/limiter.py) is a
    module-level singleton -- imported once per test process, not
    recreated by the `app` fixture on every test despite that fixture
    rebuilding the FastAPI app itself. Without this reset, rate-limit
    counters would accumulate across the whole test session instead of
    per test, and unrelated tests could start failing with 429s purely
    from suite ordering/count rather than anything they actually did
    wrong.
    """
    reset_public_rate_limits()
    yield