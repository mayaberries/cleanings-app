from typing import List, Union
from databases.core import Database

from fastapi.exceptions import HTTPException
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from app.db.repositories.base import BaseRepository
from app.models.cleaning import CleaningCreate, CleaningPublic, CleaningUpdate, CleaningInDB
from uuid import uuid4

from app.models.user import UserInDB
from app.db.repositories.users import UsersRepository

CREATE_CLEANING_QUERY = """
    INSERT INTO cleanings (id, name, description, price, cleaning_type, owner)
    VALUES (:id, :name, :description, :price, :cleaning_type, :owner)
    RETURNING id, name, description, price, cleaning_type, owner, created_at ,updated_at;
"""

GET_CLEANING_BY_ID_QUERY = """
    SELECT id, name, description, price, cleaning_type, owner, created_at, updated_at
    FROM cleanings
    WHERE id = :id;
"""

GET_ALL_CLEANINGS_QUERY = """
    SELECT id, name, description, price, cleaning_type  
    FROM cleanings;  
"""

LIST_ALL_USER_CLEANINGS_QUERY = """
    SELECT id, name, description, price, cleaning_type, owner, created_at, updated_at
    FROM cleanings
    WHERE owner = :owner;
"""

UPDATE_CLEANING_BY_ID_QUERY = """
    UPDATE cleanings
    SET name         = :name,
        description  = :description,
        price        = :price,
        cleaning_type = :cleaning_type
    WHERE id = :id
    RETURNING id, name, description, price, cleaning_type, owner, created_at, updated_at;  
"""

DELETE_CLEANING_BY_ID_QUERY = """
    DELETE FROM cleanings  
    WHERE id = :id AND owner = :owner
    RETURNING id;  
"""


class CleaningsRepository(BaseRepository):
    """"
    All database actions associated with the cleaning resource
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_cleaning(self, *, new_cleaning: CleaningCreate, requesting_user: UserInDB) -> CleaningInDB:
        cleaning = await self.db.fetch_one(
            query=CREATE_CLEANING_QUERY,
            values={
                **new_cleaning.model_dump(),
                "id": str(uuid4()),
                "owner": requesting_user.id
            }
        )
        return CleaningInDB(**cleaning)

    async def get_cleaning_by_id(
            self, *, id: str, requesting_user: UserInDB, populate: bool = True
    ) -> Union[CleaningInDB, CleaningPublic]:
        cleaning_record = await self.db.fetch_one(query=GET_CLEANING_BY_ID_QUERY, values={"id": id})

        if cleaning_record:
            cleaning = CleaningInDB(**cleaning_record)
            if populate:
                return await self.populate_cleaning(cleaning=cleaning, requesting_user=requesting_user)
            return cleaning

    async def list_all_user_cleanings(self, requesting_user: UserInDB) -> List[CleaningInDB]:
        cleanings_records = await self.db.fetch_all(
            query=LIST_ALL_USER_CLEANINGS_QUERY, values={
                "owner": requesting_user.id}
        )

        return [CleaningInDB(**l) for l in cleanings_records]

    async def get_all_cleanings(self) -> List[CleaningInDB]:
        cleaning_records = await self.db.fetch_all(
            query=GET_ALL_CLEANINGS_QUERY,
        )
        return [CleaningInDB(**l) for l in cleaning_records]

    async def update_cleaning(
            self, *, cleaning: CleaningInDB, cleaning_update: CleaningUpdate
    ) -> CleaningInDB:
        cleaning_update_params = cleaning.model_copy(
            update=cleaning_update.model_dump(exclude_unset=True))

        if cleaning_update_params.cleaning_type is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cleaning type. Cannot be None."
            )

        updated_cleaning = await self.db.fetch_one(
            query=UPDATE_CLEANING_BY_ID_QUERY,
            values=cleaning_update_params.model_dump(
                exclude={"owner", "created_at", "updated_at"})
        )

        return CleaningInDB(**updated_cleaning)

    async def delete_cleaning_by_id(self, *, id: str, requesting_user: UserInDB) -> int:
        return await self.db.execute(
            query=DELETE_CLEANING_BY_ID_QUERY,
            values={"id": id, "owner": requesting_user.id},
        )

    async def populate_cleaning(self, *, cleaning: CleaningInDB, requesting_user: UserInDB = None) -> CleaningPublic:
        return CleaningPublic(
            **cleaning.model_dump(exclude={"owner"}),
            owner=await self.users_repo.get_user_by_id(user_id=cleaning.owner),
        )