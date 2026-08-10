from fastapi import HTTPException, Path, Request, status
from limits import RateLimitItem, parse
from limits.storage import MemoryStorage, Storage, storage_from_string
from limits.strategies import MovingWindowRateLimiter

from app.core.config import (
    REDIS_URL,
    PUBLIC_RATE_LIMIT_PER_KEY,
    PUBLIC_RATE_LIMIT_PER_IP,
    CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC,
)


def _build_storage() -> Storage:
    if REDIS_URL:
        return storage_from_string(REDIS_URL)
    return MemoryStorage()


# One shared storage + strategy. The two tiers stay independent because
# each hit() call below is namespaced under a different first identifier
# ("clinic-key" vs "ip"), so they land in different buckets even though
# they share one backend -- no need for two separate storage instances.
_storage = _build_storage()
_clinic_availability_limit: RateLimitItem = parse(f"{CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC}/minute")
_strategy = MovingWindowRateLimiter(_storage)
_key_limit: RateLimitItem = parse(f"{PUBLIC_RATE_LIMIT_PER_KEY}/minute")
_ip_limit: RateLimitItem = parse(f"{PUBLIC_RATE_LIMIT_PER_IP}/minute")


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def get_clinic_key_from_request(request: Request) -> str:
    """
    Falls back to `anon:<ip>` if the header is missing/empty rather than
    raising here -- get_clinic_from_public_key (public_auth.py) is what
    actually rejects a missing/bad key with a 401. This just makes sure
    that rejection path still consumes a bucket instead of being an
    unlimited way to hammer the DB lookup.
    """
    key = request.headers.get("X-Clinic-Key")
    return key if key else f"anon:{get_client_ip(request)}"


def enforce_public_rate_limits(request: Request) -> None:
    """
    Single dependency covering both tiers for the public booking surface.
    Mount once as a router-level dependency (see public_booking.py)
    rather than per-route, and rather than stacking multiple decorators --
    see the module docstring above for why the decorator-stacking approach
    doesn't work.

    Primary limiter: generous, scoped to one clinic's key -- the expected
    traffic shape (many end users booking through one embedded widget).

    Backstop limiter: much looser, scoped to the caller's IP regardless of
    which (or whether a valid) key it sent -- exists specifically to slow
    down someone enumerating pk_live_/pk_test_ values, which the per-key
    limiter alone can't catch since each guessed key starts its own fresh
    bucket. Deliberately kept well above the per-key limit (see
    app/core/config.py) so it never binds during ordinary single-key
    traffic.
    """
    clinic_key = get_clinic_key_from_request(request)
    client_ip = get_client_ip(request)

    if not _strategy.hit(_key_limit, "clinic-key", clinic_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this clinic key. Please slow down.",
        )

    if not _strategy.hit(_ip_limit, "ip", client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this IP address. Please slow down.",
        )


def enforce_clinic_availability_rate_limits(request: Request, clinic_id: str = Path(...)) -> None:
    """
    Router-level dependency for /clinics/{clinic_id}/availability (see
    api/routes/clinic_availability.py). Same two-tier shape as
    enforce_public_rate_limits, but the primary tier is scoped to
    clinic_id (from the path) rather than a clinic key -- the closest
    thing this route has to a caller identity, since GET is open. Shares
    the same "ip" bucket as the public surface as a blanket backstop
    against one IP hammering any part of the API, not just this route --
    that's a deliberate reuse, not an accident of copy-paste.
    """
    if not _strategy.hit(_clinic_availability_limit, "clinic-availability", clinic_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this clinic's availability endpoint. Please slow down.",
        )

    if not _strategy.hit(_ip_limit, "ip", get_client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this IP address. Please slow down.",
        )


def reset_public_rate_limits() -> None:
    """Test-only helper -- see tests/_fixtures/rate_limit.py."""
    _storage.reset()
