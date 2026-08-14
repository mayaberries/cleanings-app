from typing import List, Optional
from uuid import uuid4
from databases.core import Database
from fastapi import HTTPException, status

from app.models.clinics.clinic import ClinicCreate, ClinicUpdate, ClinicInDB, slugify
from app.models.auth.user import UserInDB, UserRole
from app.db.repositories.clinic_availability import ClinicAvailabilityRepository
from app.db.repositories.base import BaseRepository

CLINIC_COLUMNS = "id, name, slug, email, phone_number, address, created_at, updated_at"

CREATE_CLINIC_QUERY = f"""
    INSERT INTO clinics (id, name, slug, email, phone_number, address)
    VALUES (:id, :name, :slug, :email, :phone_number, :address)
    RETURNING {CLINIC_COLUMNS};
"""

GET_CLINIC_BY_ID_QUERY = f"""
    SELECT {CLINIC_COLUMNS}
    FROM clinics
    WHERE id = :id;
"""

GET_CLINIC_BY_SLUG_QUERY = f"""
    SELECT {CLINIC_COLUMNS}
    FROM clinics
    WHERE slug = :slug;
"""

# Platform-operator listing (see require_superuser) -- deliberately no
# tenant scoping. Simple offset pagination is enough for the current scale
# (one row per clinic, admin-triggered); revisit if this ever needs to
# serve a UI directly.
LIST_ALL_CLINICS_QUERY = f"""
    SELECT {CLINIC_COLUMNS}
    FROM clinics
    ORDER BY created_at
    LIMIT :limit OFFSET :offset;
"""

UPDATE_CLINIC_BY_ID_QUERY = f"""
    UPDATE clinics
    SET name         = :name,
        email        = :email,
        phone_number = :phone_number,
        address      = :address
    WHERE id = :id
    RETURNING {CLINIC_COLUMNS};
"""

SET_USER_CLINIC_ID_QUERY = """
    UPDATE users
    SET clinic_id = :clinic_id
    WHERE id = :user_id
    RETURNING id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at;
"""

LIST_STAFF_FOR_CLINIC_QUERY = """
    SELECT id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE clinic_id = :clinic_id
    ORDER BY role, username;
"""


class ClinicsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.availability_repo = ClinicAvailabilityRepository(db)

    async def create_clinic_for_admin(self, *, new_clinic: ClinicCreate, requesting_user: UserInDB) -> ClinicInDB:
        if requesting_user.role != UserRole.clinic_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only clinic admins may create a clinic.",
            )
        if requesting_user.clinic_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user already belongs to a clinic.",
            )

        slug = new_clinic.slug or slugify(new_clinic.name)
        if await self.get_clinic_by_slug(slug=slug) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug '{slug}' is already taken by another clinic.",
            )

        # Clinic row + default hours + admin attachment as one unit -- a
        # clinic should never exist without an availability row once this
        # path is the one that created it (get_or_create_availability
        # covers legacy/edge cases, but this is the normal path).
        clinic_record = await self.db.fetch_one(
            query=CREATE_CLINIC_QUERY,
            values={
                "id": str(uuid4()),
                "name": new_clinic.name,
                "slug": slug,
                "email": new_clinic.email,
                "phone_number": new_clinic.phone_number,
                "address": new_clinic.address,
            },
        )
        clinic = ClinicInDB(**clinic_record)

        await self.availability_repo.get_or_create_availability(clinic_id=clinic.id)
        await self.db.execute(
            query=SET_USER_CLINIC_ID_QUERY, values={"clinic_id": clinic.id, "user_id": requesting_user.id}
        )

        return clinic

    async def get_clinic_by_id(self, *, id: str) -> Optional[ClinicInDB]:
        record = await self.db.fetch_one(query=GET_CLINIC_BY_ID_QUERY, values={"id": id})
        if record:
            return ClinicInDB(**record)

    async def get_clinic_by_slug(self, *, slug: str) -> Optional[ClinicInDB]:
        record = await self.db.fetch_one(query=GET_CLINIC_BY_SLUG_QUERY, values={"slug": slug})
        if record:
            return ClinicInDB(**record)

    async def list_all_clinics(self, *, limit: int = 100, offset: int = 0) -> List[ClinicInDB]:
        """Platform-operator only (see require_superuser) -- this is what
        the admin CLI's `clinics list` / `sites generate-all` walk over.
        Not exposed to clinic_admin/aux at all."""
        records = await self.db.fetch_all(
            query=LIST_ALL_CLINICS_QUERY, values={"limit": limit, "offset": offset}
        )
        return [ClinicInDB(**r) for r in records]

    async def update_clinic(self, *, clinic: ClinicInDB, clinic_update: ClinicUpdate) -> ClinicInDB:
        # slug is deliberately not updatable here -- it's the stable
        # identifier the site generator's output folder (and any future
        # subdomain) is keyed on. Changing it would orphan already-built
        # static sites silently.
        update_params = clinic.model_copy(update=clinic_update.model_dump(exclude_unset=True))
        clinic_record = await self.db.fetch_one(
            query=UPDATE_CLINIC_BY_ID_QUERY,
            values={
                "id": update_params.id,
                "name": update_params.name,
                "email": update_params.email,
                "phone_number": update_params.phone_number,
                "address": update_params.address,
            },
        )
        return ClinicInDB(**clinic_record)

    async def join_clinic_as_staff(self, *, clinic_id: str, requesting_user: UserInDB) -> ClinicInDB:
        clinic = await self.get_clinic_by_id(id=clinic_id)
        if not clinic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No clinic found with that id.")
        if requesting_user.clinic_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user already belongs to a clinic.",
            )
        await self.db.execute(
            query=SET_USER_CLINIC_ID_QUERY, values={"clinic_id": clinic.id, "user_id": requesting_user.id}
        )
        return clinic
