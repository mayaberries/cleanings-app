from typing import List
from uuid import uuid4

from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.models.pet import PetCreate, PetUpdate, PetInDB
from app.models.user import UserInDB


CREATE_PET_QUERY = """
    INSERT INTO pets (id, name, species, breed, birth_date, notes, image, owner)
    VALUES (:id, :name, :species, :breed, :birth_date, :notes, :image, :owner)
    RETURNING id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at;
"""

GET_PET_BY_ID_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at
    FROM pets
    WHERE id = :id;
"""

LIST_ALL_USER_PETS_QUERY = """
    SELECT id, name, species, breed, birth_date, notes, image, owner, created_at, updated_at
    FROM pets
    WHERE owner = :owner;
"""

UPDATE_PET_BY_ID_QUERY = """
    UPDATE pets
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
    DELETE FROM pets
    WHERE id = :id AND owner = :owner
    RETURNING id;
"""


class PetsRepository(BaseRepository):
    """
    All database actions associated with the pet resource
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)

    async def create_pet(self, *, new_pet: PetCreate, requesting_user: UserInDB) -> PetInDB:
        pet = await self.db.fetch_one(
            query=CREATE_PET_QUERY,
            values={
                **new_pet.dict(),
                "id": str(uuid4()),
                "owner": requesting_user.id
            }
        )
        return PetInDB(**pet)

    async def get_pet_by_id(self, *, id: str, requesting_user: UserInDB) -> PetInDB:
        pet_record = await self.db.fetch_one(query=GET_PET_BY_ID_QUERY, values={"id": id})

        if pet_record:
            return PetInDB(**pet_record)

    async def list_all_user_pets(self, requesting_user: UserInDB) -> List[PetInDB]:
        pet_records = await self.db.fetch_all(
            query=LIST_ALL_USER_PETS_QUERY, values={"owner": requesting_user.id}
        )

        return [PetInDB(**p) for p in pet_records]

    async def update_pet(self, *, pet: PetInDB, pet_update: PetUpdate) -> PetInDB:
        pet_update_params = pet.model_copy(update=pet_update.dict(exclude_unset=True))

        updated_pet = await self.db.fetch_one(
            query=UPDATE_PET_BY_ID_QUERY,
            values=pet_update_params.model_dump(
                exclude={"owner", "created_at", "updated_at"})
        )

        return PetInDB(**updated_pet)

    async def delete_pet_by_id(self, *, id: str, requesting_user: UserInDB) -> int:
        return await self.db.execute(
            query=DELETE_PET_BY_ID_QUERY,
            values={"id": id, "owner": requesting_user.id},
        )