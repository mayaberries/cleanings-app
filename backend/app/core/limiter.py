from fastapi import HTTPException, Path, Request, status
from limits import RateLimitItem, parse
from limits.storage import MemoryStorage, Storage, storage_from_string
from limits.strategies import MovingWindowRateLimiter

from app.core.config import (
    REDIS_URL,
    PUBLIC_RATE_LIMIT_PER_KEY,
    PUBLIC_RATE_LIMIT_PER_IP,
    CLINIC_AVAILABILITY_READ_RATE_LIMIT_PER_CLINIC,
    CLINIC_AVAILABILITY_WRITE_RATE_LIMIT_PER_CLINIC,
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
_strategy = MovingWindowRateLimiter(_storage)
_key_limit: RateLimitItem = parse(f"{PUBLIC_RATE_LIMIT_PER_KEY}/minute")
_ip_limit: RateLimitItem = parse(f"{PUBLIC_RATE_LIMIT_PER_IP}/minute")
_clinic_availability_read_limit: RateLimitItem = parse(
    f"{CLINIC_AVAILABILITY_READ_RATE_LIMIT_PER_CLINIC}/minute"
)
_clinic_availability_write_limit: RateLimitItem = parse(
    f"{CLINIC_AVAILABILITY_WRITE_RATE_LIMIT_PER_CLINIC}/minute"
)


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


def _enforce_clinic_availability_limit(request: Request, clinic_id: str, limit: RateLimitItem, bucket: str) -> None:
    if not _strategy.hit(limit, bucket, clinic_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this clinic's availability endpoint. Please slow down.",
        )
    # Shared IP backstop across the whole API, GET and PUT and the public
    # surface alike -- deliberately the one bucket that IS shared, since
    # its job is "stop one IP hammering anything," not per-resource budget.
    if not _strategy.hit(_ip_limit, "ip", get_client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this IP address. Please slow down.",
        )


def enforce_clinic_availability_read_rate_limits(request: Request, clinic_id: str = Path(...)) -> None:
    """GET /clinics/{clinic_id}/availability -- unauthenticated, so
    clinic_id from the path is the only identity there is to key on."""
    _enforce_clinic_availability_limit(
        request, clinic_id, _clinic_availability_read_limit, "clinic-availability-read"
    )


# TODO(rate-limit): the write-side limiter is keyed on clinic_id (from the
# path), not on the authenticated caller -- so an unauthenticated request
# with a guessed/known clinic_id still consumes write budget even though
# check_clinic_modification_permissions will 403 it right after. A flood of
# such requests could still exhaust the real admin's write budget before
# the 403 ever gets checked. Fix: key this limiter on current_user.id
# instead, since PUT is JWT-authed anyway -- add
# current_user: UserInDB = Depends(get_current_active_user) to this
# function's signature and hit the bucket with current_user.id.
def enforce_clinic_availability_write_rate_limits(request: Request, clinic_id: str = Path(...)) -> None:
    """PUT /clinics/{clinic_id}/availability -- separate bucket from the
    read tier on purpose, see app/core/config.py, so public read traffic
    can never exhaust the clinic admin's own write budget."""
    _enforce_clinic_availability_limit(
        request, clinic_id, _clinic_availability_write_limit, "clinic-availability-write"
    )


def reset_public_rate_limits() -> None:
    """Test-only helper -- see tests/_fixtures/rate_limit.py."""
    _storage.reset()
