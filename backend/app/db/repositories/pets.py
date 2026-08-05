from typing import List
from uuid import uuid4

from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.models.pet_profile import PetProfileCreate, PetProfileUpdate, PetProfileInDB
from app.models.user import UserInDB

CREATE_PET_QUERY = """
    INSERT INTO pet_profiles (id, name, species, breed, birth_date, notes, image, owner)
    VALUES (:id, :name, :species, :breed, :birth_date, :notes, :image, :owner)
    RETURNING id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at;
"""

GET_PET_BY_ID_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at
    FROM pet_profiles
    WHERE id = :id;
"""

LIST_ALL_USER_PETS_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at
    FROM pet_profiles
    WHERE owner = :owner;
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
    RETURNING id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at;
"""

DELETE_PET_BY_ID_QUERY = """
    DELETE FROM pet_profiles
    WHERE id = :id AND owner = :owner
    RETURNING id;
"""


class PetProfilesRepository(BaseRepository):
    """
    All database actions associated with the pet profile resource
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)

    async def create_pet(self, *, new_pet: PetProfileCreate, requesting_user: UserInDB) -> PetProfileInDB:
        pet = await self.db.fetch_one(
            query=CREATE_PET_QUERY,
            values={
                **new_pet.dict(),
                "id": str(uuid4()),
                "owner": requesting_user.id
            }
        )
        return PetProfileInDB(**pet)

    async def get_pet_by_id(self, *, id: str, requesting_user: UserInDB) -> PetProfileInDB:
        pet_record = await self.db.fetch_one(query=GET_PET_BY_ID_QUERY, values={"id": id})

        if not pet_record:
            return None

        return PetProfileInDB(**pet_record)

    async def list_all_user_pets(self, *, requesting_user: UserInDB) -> List[PetProfileInDB]:
        pet_records = await self.db.fetch_all(
            query=LIST_ALL_USER_PETS_QUERY, values={"owner": requesting_user.id}
        )
        return [PetProfileInDB(**pet_record) for pet_record in pet_records]

    async def update_pet(self, *, pet: PetProfileInDB, pet_update: PetProfileUpdate) -> PetProfileInDB:
        update_params = pet.model_copy(update=pet_update.model_dump(exclude_unset=True))

        updated_pet = await self.db.fetch_one(
            query=UPDATE_PET_BY_ID_QUERY,
            values=update_params.model_dump(exclude={"owner", "created_at", "updated_at"}),
        )

        if not updated_pet:
            return None

        return PetProfileInDB(**updated_pet)

    async def delete_pet_by_id(self, *, id: str, requesting_user: UserInDB) -> str:
        deleted_pet = await self.db.fetch_one(
            query=DELETE_PET_BY_ID_QUERY, values={"id": id, "owner": requesting_user.id}
        )

        if not deleted_pet:
            return None

        return deleted_pet["id"]
