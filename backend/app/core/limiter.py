from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import REDIS_URL, PUBLIC_RATE_LIMIT_PER_KEY, PUBLIC_RATE_LIMIT_PER_IP


def get_clinic_key_from_request(request: Request) -> str:
    """
    Key func for the per-key limiter. Falls back to `anon:<ip>` if the
    header is missing/empty rather than raising here -- get_clinic_from_public_key
    (public_auth.py) is what actually rejects a missing/bad key with a 401.
    This just makes sure *that* rejection path still consumes a bucket
    instead of being an unlimited way to hammer the DB lookup.
    """
    key = request.headers.get("X-Clinic-Key")
    return key if key else f"anon:{get_remote_address(request)}"


# In-memory storage is fine for a single MVP instance. Set REDIS_URL once
# this runs behind more than one process/worker, or the per-key/per-IP
# counters will be scoped per-worker instead of globally and the effective
# limit becomes (configured limit) x (worker count).
_storage_uri = REDIS_URL or "memory://"

# Primary limiter: generous, scoped to one clinic's key. This is the
# expected traffic shape -- many different end users booking through the
# same embedded widget, all sharing one clinic's key.
key_limiter = Limiter(key_func=get_clinic_key_from_request, storage_uri=_storage_uri)

# Backstop limiter: tighter, scoped to the caller's IP regardless of which
# key (if any) they sent. Exists specifically to slow down someone trying
# to enumerate valid pk_live_/pk_test_ values, which the per-key limiter
# alone can't catch since each guessed key starts its own fresh bucket.
ip_limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri)

# Deliberately NOT using Limiter(default_limits=[...]) + SlowAPIMiddleware
# here. That combination applies limits to every route in the app
# automatically, and this app also serves the JWT-authenticated dashboard
# routes which shouldn't share a rate-limit budget with the public surface.
# Limits are instead applied explicitly per-route with
# @key_limiter.limit(...) / @ip_limiter.limit(...) on the public_booking
# router (see app/api/routes/public_booking.py).
