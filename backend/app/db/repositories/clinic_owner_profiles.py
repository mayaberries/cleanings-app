from typing import Optional
from uuid import uuid4

from databases.core import Database
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.clinic_owner_profile import (
    ClinicOwnerProfileInDB,
    ClinicOwnerProfilePublic,
    ClinicOwnerProfileRegistration,
    ClinicOwnerProfileStatus,
    ClinicOwnerProfileUpdate,
)
from app.models.owner_profile import OwnerProfilePublic

CREATE_CLINIC_OWNER_PROFILE_QUERY = """
    INSERT INTO clinic_owner_profiles (id, clinic_id, owner_profile_id, notes, status, referred_by)
    VALUES (:id, :clinic_id, :owner_profile_id, :notes, :status, :referred_by)
    RETURNING id, clinic_id, owner_profile_id, notes, status, first_seen_at, referred_by, created_at, updated_at;
"""

GET_PIVOT_BY_CLINIC_AND_OWNER_QUERY = """
    SELECT id, clinic_id, owner_profile_id, notes, status, first_seen_at, referred_by, created_at, updated_at
    FROM clinic_owner_profiles
    WHERE clinic_id = :clinic_id AND owner_profile_id = :owner_profile_id;
"""

GET_PIVOT_BY_ID_QUERY = """
    SELECT id, clinic_id, owner_profile_id, notes, status, first_seen_at, referred_by, created_at, updated_at
    FROM clinic_owner_profiles
    WHERE id = :id;
"""

UPDATE_CLINIC_OWNER_PROFILE_QUERY = """
    UPDATE clinic_owner_profiles
    SET notes       = :notes,
        status      = :status,
        referred_by = :referred_by
    WHERE id = :id
    RETURNING id, clinic_id, owner_profile_id, notes, status, first_seen_at, referred_by, created_at, updated_at;
"""


class ClinicOwnerProfilesRepository(BaseRepository):
    """
    All database actions associated with the clinic <-> owner_profile pivot:
    a clinic-scoped view onto a (possibly cross-clinic) owner profile, so
    one clinic's notes/status on an owner never leak to, or get affected
    by, another clinic the same owner has also used.
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.owner_profiles_repo = OwnerProfilesRepository(db)

    async def get_pivot_by_id(self, *, id: str) -> Optional[ClinicOwnerProfileInDB]:
        record = await self.db.fetch_one(query=GET_PIVOT_BY_ID_QUERY, values={"id": id})
        if record:
            return ClinicOwnerProfileInDB(**record)

    async def get_pivot_for_clinic_and_owner(
            self, *, clinic_id: str, owner_profile_id: str
    ) -> Optional[ClinicOwnerProfileInDB]:
        record = await self.db.fetch_one(
            query=GET_PIVOT_BY_CLINIC_AND_OWNER_QUERY,
            values={"clinic_id": clinic_id, "owner_profile_id": owner_profile_id},
        )
        if record:
            return ClinicOwnerProfileInDB(**record)

    async def register_owner_profile_with_clinic(
            self, *, clinic_id: str, registration: ClinicOwnerProfileRegistration
    ) -> ClinicOwnerProfileInDB:
        """
        Links an owner profile to a clinic.

        - registration.new_owner_profile set -> creates a brand-new,
          account-less OwnerProfile first (a walk-in the clinic is seeing
          for the first time anywhere on the platform).
        - registration.owner_profile_id set  -> reuses an existing,
          already-deduplicated OwnerProfile (matched by phone/email
          elsewhere, or one the owner has already claimed with a login).

        Idempotent: registering the same owner with the same clinic twice
        just returns the existing pivot row rather than erroring or
        creating a duplicate — the unique (clinic_id, owner_profile_id)
        constraint backs this up at the DB level too.
        """
        if registration.owner_profile_id is not None:
            owner_profile = await self.owner_profiles_repo.get_profile_by_id(
                id=registration.owner_profile_id
            )
            if not owner_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No owner profile found with that id.",
                )
        else:
            owner_profile = await self.owner_profiles_repo.create_owner_profile(
                profile_create=registration.new_owner_profile
            )

        existing_pivot = await self.get_pivot_for_clinic_and_owner(
            clinic_id=clinic_id, owner_profile_id=owner_profile.id
        )
        if existing_pivot:
            return existing_pivot

        pivot_record = await self.db.fetch_one(
            query=CREATE_CLINIC_OWNER_PROFILE_QUERY,
            values={
                "id": str(uuid4()),
                "clinic_id": clinic_id,
                "owner_profile_id": owner_profile.id,
                "notes": registration.notes,
                "status": ClinicOwnerProfileStatus.active.value,
                "referred_by": registration.referred_by,
            },
        )

        return ClinicOwnerProfileInDB(**pivot_record)

    async def update_pivot(
            self, *, pivot: ClinicOwnerProfileInDB, pivot_update: ClinicOwnerProfileUpdate
    ) -> ClinicOwnerProfileInDB:
        """Only ever touches notes/status/referred_by — clinic_id,
        owner_profile_id and first_seen_at are immutable here by
        construction, since they're excluded from the update query."""
        update_params = pivot.model_copy(update=pivot_update.model_dump(exclude_unset=True))

        updated_pivot = await self.db.fetch_one(
            query=UPDATE_CLINIC_OWNER_PROFILE_QUERY,
            values={
                "id": update_params.id,
                "notes": update_params.notes,
                "status": update_params.status.value,
                "referred_by": update_params.referred_by,
            },
        )

        if not updated_pivot:
            return None

        return ClinicOwnerProfileInDB(**updated_pivot)

    async def populate_pivot(self, *, pivot: ClinicOwnerProfileInDB) -> ClinicOwnerProfilePublic:
        """The composed read: one call gets you the clinic's local
        notes/status *and* the owner's shared identity, without letting a
        write to one accidentally reach the other."""
        owner_profile = await self.owner_profiles_repo.get_profile_by_id(id=pivot.owner_profile_id)

        return ClinicOwnerProfilePublic(
            **pivot.model_dump(exclude={"owner_profile_id"}),
            owner_profile_id=OwnerProfilePublic(
                **owner_profile.model_dump()) if owner_profile else pivot.owner_profile_id,
        )
