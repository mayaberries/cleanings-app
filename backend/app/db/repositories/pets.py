from typing import List
from uuid import uuid4

from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.models.pet_profile import PetProfileCreate, PetProfileUpdate, PetProfileInDB


CREATE_PET_QUERY = """
    INSERT INTO pet_profiles (id, name, species, breed, birth_date, notes, image, owner_profile_id)
    VALUES (:id, :name, :species, :breed, :birth_date, :notes, :image, :owner_profile_id)
    RETURNING id, name, species, breed, birth_date, notes, image, owner_profile_id, created_at, updated_at;
"""

GET_PET_BY_ID_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner_profile_id, created_at, updated_at
    FROM pet_profiles
    WHERE id = :id;
"""

LIST_PET_PROFILES_FOR_OWNER_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner_profile_id, created_at, updated_at
    FROM pet_profiles
    WHERE owner_profile_id = :owner_profile_id;
"""

UPDATE_PET_BY_ID_QUERY = """
    UPDATE pet_profiles
    SET name       = :name,
        species    = :species,
        breed      = :breed,
        birth_date = :birth_date,
        notes      = :notes,
        image      = :image
    WHERE id = :id
    RETURNING id, name, species, breed, birth_date, notes, image, owner_profile_id, created_at, updated_at;
"""

DELETE_PET_BY_ID_QUERY = """
    DELETE FROM pet_profiles
    WHERE id = :id AND owner_profile_id = :owner_profile_id
    RETURNING id;
"""


class PetProfilesRepository(BaseRepository):
    """
    All database actions associated with the pet profile resource.
    Speaks only in terms of owner_profile_id — has no notion of a User/login.
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)

    async def create_pet(self, *, new_pet: PetProfileCreate, owner_profile_id: str) -> PetProfileInDB:
        pet = await self.db.fetch_one(
            query=CREATE_PET_QUERY,
            values={
                **new_pet.model_dump(),
                "id": str(uuid4()),
                "owner_profile_id": owner_profile_id,
            }
        )
        return PetProfileInDB(**pet)

    async def get_pet_by_id(self, *, id: str) -> PetProfileInDB:
        pet_record = await self.db.fetch_one(query=GET_PET_BY_ID_QUERY, values={"id": id})

        if not pet_record:
            return None

        return PetProfileInDB(**pet_record)

    async def list_pet_profiles_for_owner(self, *, owner_profile_id: str) -> List[PetProfileInDB]:
        pet_records = await self.db.fetch_all(
            query=LIST_PET_PROFILES_FOR_OWNER_QUERY, values={"owner_profile_id": owner_profile_id}
        )
        return [PetProfileInDB(**pet_record) for pet_record in pet_records]

    async def update_pet(self, *, pet: PetProfileInDB, pet_update: PetProfileUpdate) -> PetProfileInDB:
        update_params = pet.model_copy(update=pet_update.model_dump(exclude_unset=True))

        updated_pet = await self.db.fetch_one(
            query=UPDATE_PET_BY_ID_QUERY,
            values=update_params.model_dump(exclude={"owner_profile_id", "created_at", "updated_at"}),
        )

        if not updated_pet:
            return None

        return PetProfileInDB(**updated_pet)

    async def delete_pet_by_id(self, *, id: str, owner_profile_id: str) -> str:
        deleted_pet = await self.db.fetch_one(
            query=DELETE_PET_BY_ID_QUERY, values={"id": id, "owner_profile_id": owner_profile_id}
        )

        if not deleted_pet:
            return None

        return deleted_pet["id"]