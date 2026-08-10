from typing import Optional

from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret


config = Config(".env")

PROJECT_NAME = "Phresh"
VERSION = "1.0.0"
API_PREFIX = "/api"

SECRET_KEY = config("SECRET_KEY", cast=Secret)
ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    cast=int,
    default=7*24*60  # one week
)
JWT_ALGORITHM = config("JWT_ALGORITHM", cast=str, default="HS256")
JWT_AUDIENCE = config("JWT_AUDIENCE", cast=str, default="phresh:auth")
JWT_TOKEN_PREFIX = config("JWT_TOKEN_PREFIX", cast=str, default="Bearer")

POSTGRES_USER = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_SERVER = config("POSTGRES_SERVER", cast=str, default="localhost")
POSTGRES_PORT = config("POSTGRES_PORT", cast=str, default="5432")
POSTGRES_DB = config("POSTGRES_DB", cast=str)


DATABASE_URL = config(
    "DATABASE_URL",
    cast=DatabaseURL,
    default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# --- Public booking widget (clinic-key auth) ---------------------------

# Optional on purpose: unset -> slowapi falls back to in-memory storage,
# which is fine for a single-process MVP deploy. Set this once the app
# runs with more than one worker/process, see app/core/limiter.py.
REDIS_URL: Optional[str] = config("REDIS_URL", cast=str, default=None)

# Requests per minute allowed for a single clinic public key. This is the
# expected-traffic limiter -- sized for "many visitors booking through one
# clinic's embedded widget at once", not for a single visitor's clicks.
PUBLIC_RATE_LIMIT_PER_KEY = config("PUBLIC_RATE_LIMIT_PER_KEY", cast=int, default=120)

# Requests per minute allowed from a single IP against the public surface,
# regardless of which (or whether a valid) key it sent. Backstop against
# key-enumeration attempts, not expected to be hit by real widget traffic.
PUBLIC_RATE_LIMIT_PER_IP = config("PUBLIC_RATE_LIMIT_PER_IP", cast=int, default=600)

PROFILE_CLAIM_AUDIENCE = config("PROFILE_CLAIM_AUDIENCE", cast=str, default="phresh:profile-claim")
PROFILE_CLAIM_TOKEN_EXPIRE_MINUTES = config(
    "PROFILE_CLAIM_TOKEN_EXPIRE_MINUTES", cast=int, default=7 * 24 * 60  # one week
)
# --- Clinic-facing internal API -----------------------------------------

# Requests per minute allowed against a single clinic's availability
# resource. GET on that route carries no auth (mirrors GET
# /clinics/{clinic_id}/ today -- see api/routes/clinic_availability.py),
# so unlike the JWT-authed rest of the staff API there's no caller
# identity to key a limiter on. clinic_id from the path stands in for
# that instead.
CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC = config(
    "CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC", cast=int, default=60
)