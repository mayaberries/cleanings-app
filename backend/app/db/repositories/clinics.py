from typing import List, Optional
from uuid import uuid4
from databases.core import Database
from fastapi import HTTPException, status

from app.db.repositories.base import BaseRepository
from app.models.clinic import ClinicCreate, ClinicUpdate, ClinicInDB
from app.models.user import UserInDB, UserRole

CREATE_CLINIC_QUERY = """
    INSERT INTO clinics (id, name, email, phone_number, address)
    VALUES (:id, :name, :email, :phone_number, :address)
    RETURNING id, name, email, phone_number, address, created_at, updated_at;
"""

GET_CLINIC_BY_ID_QUERY = """
    SELECT id, name, email, phone_number, address, created_at, updated_at
    FROM clinics
    WHERE id = :id;
"""

UPDATE_CLINIC_BY_ID_QUERY = """
    UPDATE clinics
    SET name         = :name,
        email        = :email,
        phone_number = :phone_number,
        address      = :address
    WHERE id = :id
    RETURNING id, name, email, phone_number, address, created_at, updated_at;
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

        clinic_record = await self.db.fetch_one(
            query=CREATE_CLINIC_QUERY,
            values={**new_clinic.model_dump(), "id": str(uuid4())},
        )
        clinic = ClinicInDB(**clinic_record)

        await self.db.fetch_one(
            query=SET_USER_CLINIC_ID_QUERY,
            values={"user_id": requesting_user.id, "clinic_id": clinic.id},
        )

        return clinic

    async def join_clinic_as_staff(self, *, clinic_id: str, requesting_user: UserInDB) -> ClinicInDB:
        if requesting_user.role not in (UserRole.clinic_admin, UserRole.clinic_aux):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only clinic staff may join a clinic.",
            )
        if requesting_user.clinic_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user already belongs to a clinic.",
            )

        clinic = await self.get_clinic_by_id(id=clinic_id)
        if not clinic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No clinic found with that id.",
            )

        await self.db.fetch_one(
            query=SET_USER_CLINIC_ID_QUERY,
            values={"user_id": requesting_user.id, "clinic_id": clinic.id},
        )

        return clinic

    async def get_clinic_by_id(self, *, id: str) -> Optional[ClinicInDB]:
        clinic_record = await self.db.fetch_one(query=GET_CLINIC_BY_ID_QUERY, values={"id": id})
        if clinic_record:
            return ClinicInDB(**clinic_record)

    async def update_clinic(self, *, clinic: ClinicInDB, clinic_update: ClinicUpdate) -> ClinicInDB:
        updated_params = clinic.model_copy(update=clinic_update.model_dump(exclude_unset=True))
        updated_record = await self.db.fetch_one(
            query=UPDATE_CLINIC_BY_ID_QUERY,
            values=updated_params.model_dump(exclude={"created_at", "updated_at"}),
        )
        return ClinicInDB(**updated_record)

    async def list_staff_for_clinic(self, *, clinic_id: str) -> List[UserInDB]:
        records = await self.db.fetch_all(query=LIST_STAFF_FOR_CLINIC_QUERY, values={"clinic_id": clinic_id})
        return [UserInDB(**r) for r in records]