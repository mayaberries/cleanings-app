import secrets
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from databases.core import Database
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.models.clinics.clinic import ClinicInDB
from app.models.clinics.clinic_api_key import ClinicAPIKeyCreate, ClinicAPIKeyInDB, ClinicKeyEnvironment
from app.models.auth.user import UserInDB, UserRole

CLINIC_API_KEY_COLUMNS = (
    "id, clinic_id, public_key, environment, label, is_active, "
    "last_used_at, revoked_at, created_at, updated_at"
)

CREATE_CLINIC_API_KEY_QUERY = f"""
    INSERT INTO clinic_api_keys (id, clinic_id, public_key, environment, label)
    VALUES (:id, :clinic_id, :public_key, :environment, :label)
    RETURNING {CLINIC_API_KEY_COLUMNS};
"""

LIST_KEYS_FOR_CLINIC_QUERY = f"""
    SELECT {CLINIC_API_KEY_COLUMNS}
    FROM clinic_api_keys
    WHERE clinic_id = :clinic_id
    ORDER BY created_at DESC;
"""

GET_KEY_BY_ID_QUERY = f"""
    SELECT {CLINIC_API_KEY_COLUMNS}
    FROM clinic_api_keys
    WHERE id = :id;
"""

# Hot path — hit on every public booking-surface request. Matches the
# partial index created in c3f7a2e9d5b1_create_clinic_api_keys.py.
GET_ACTIVE_CLINIC_BY_PUBLIC_KEY_QUERY = """
    SELECT c.id, c.name, c.slug, c.email, c.phone_number, c.address, c.created_at, c.updated_at
    FROM clinic_api_keys k
    INNER JOIN clinics c ON c.id = k.clinic_id
    WHERE k.public_key = :public_key
      AND k.is_active = true
      AND k.revoked_at IS NULL;
"""

TOUCH_LAST_USED_QUERY = """
    UPDATE clinic_api_keys
    SET last_used_at = :last_used_at
    WHERE public_key = :public_key;
"""

REVOKE_KEY_QUERY = f"""
    UPDATE clinic_api_keys
    SET is_active = false, revoked_at = :revoked_at
    WHERE id = :id AND clinic_id = :clinic_id
    RETURNING {CLINIC_API_KEY_COLUMNS};
"""


class ClinicAPIKeysRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)

    @staticmethod
    def generate_public_key(*, environment: ClinicKeyEnvironment) -> str:
        # url-safe, no padding chars, high entropy — mirrors Stripe's
        # pk_live_/pk_test_ shape closely enough to be immediately
        # recognizable to anyone who's integrated a Stripe-like API before.
        return f"pk_{environment.value}_{secrets.token_urlsafe(32)}"

    async def create_key_for_clinic(
            self, *, clinic_id: str, key_create: ClinicAPIKeyCreate, requesting_user: UserInDB
    ) -> ClinicAPIKeyInDB:
        if requesting_user.role != UserRole.clinic_admin or requesting_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the admin of this clinic may create API keys for it.",
            )

        public_key = self.generate_public_key(environment=key_create.environment)

        record = await self.db.fetch_one(
            query=CREATE_CLINIC_API_KEY_QUERY,
            values={
                "id": str(uuid4()),
                "clinic_id": clinic_id,
                "public_key": public_key,
                "environment": key_create.environment.value,
                "label": key_create.label,
            },
        )
        return ClinicAPIKeyInDB(**record)

    async def list_keys_for_clinic(self, *, clinic_id: str) -> List[ClinicAPIKeyInDB]:
        records = await self.db.fetch_all(query=LIST_KEYS_FOR_CLINIC_QUERY, values={"clinic_id": clinic_id})
        return [ClinicAPIKeyInDB(**r) for r in records]

    async def get_key_by_id(self, *, id: str) -> Optional[ClinicAPIKeyInDB]:
        record = await self.db.fetch_one(query=GET_KEY_BY_ID_QUERY, values={"id": id})
        if record:
            return ClinicAPIKeyInDB(**record)

    async def get_active_clinic_by_public_key(self, *, public_key: str) -> Optional[ClinicInDB]:
        record = await self.db.fetch_one(
            query=GET_ACTIVE_CLINIC_BY_PUBLIC_KEY_QUERY, values={"public_key": public_key}
        )
        if not record:
            return None

        # Best-effort usage tracking, not on the critical path for the
        # caller — a failure here should never block a legitimate booking
        # request. Kept synchronous/awaited for simplicity in the MVP; if
        # this ever shows up as a latency contributor, move it to a
        # background task instead.
        await self.db.execute(
            query=TOUCH_LAST_USED_QUERY,
            values={"public_key": public_key, "last_used_at": datetime.now(timezone.utc)},
        )

        return ClinicInDB(**record)

    async def revoke_key(self, *, key_id: str, clinic_id: str, requesting_user: UserInDB) -> ClinicAPIKeyInDB:
        if requesting_user.role != UserRole.clinic_admin or requesting_user.clinic_id != clinic_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the admin of this clinic may revoke its API keys.",
            )

        record = await self.db.fetch_one(
            query=REVOKE_KEY_QUERY,
            values={"id": key_id, "clinic_id": clinic_id, "revoked_at": datetime.now(timezone.utc)},
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No API key found with that id for this clinic.",
            )
        return ClinicAPIKeyInDB(**record)
