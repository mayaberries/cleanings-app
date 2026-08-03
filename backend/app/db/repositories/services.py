from typing import List, Union
from databases.core import Database

from fastapi.exceptions import HTTPException
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from app.db.repositories.base import BaseRepository
from app.models.service import ServiceCreate, ServicePublic, ServiceUpdate, ServiceInDB
from uuid import uuid4

from app.models.user import UserInDB
from app.db.repositories.users import UsersRepository

CREATE_SERVICE_QUERY = """
    INSERT INTO services (id, name, description, price, service_type, owner)
    VALUES (:id, :name, :description, :price, :service_type, :owner)
    RETURNING id, name, description, price, service_type, owner, created_at ,updated_at;
"""

GET_SERVICE_BY_ID_QUERY = """
    SELECT id, name, description, price, service_type, owner, created_at, updated_at
    FROM services
    WHERE id = :id;
"""

GET_ALL_SERVICES_QUERY = """
    SELECT id, name, description, price, service_type  
    FROM services;  
"""

LIST_ALL_USER_SERVICES_QUERY = """
    SELECT id, name, description, price, service_type, owner, created_at, updated_at
    FROM services
    WHERE owner = :owner;
"""

UPDATE_SERVICE_BY_ID_QUERY = """
    UPDATE services
    SET name         = :name,
        description  = :description,
        price        = :price,
        service_type = :service_type
    WHERE id = :id
    RETURNING id, name, description, price, service_type, owner, created_at, updated_at;  
"""

DELETE_SERVICE_BY_ID_QUERY = """
    DELETE FROM services  
    WHERE id = :id AND owner = :owner
    RETURNING id;  
"""


class ServicesRepository(BaseRepository):
    """"
    All database actions associated with the service resource
    """

    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_service(self, *, new_service: ServiceCreate, requesting_user: UserInDB) -> ServiceInDB:
        service = await self.db.fetch_one(
            query=CREATE_SERVICE_QUERY,
            values={
                **new_service.model_dump(),
                "id": str(uuid4()),
                "owner": requesting_user.id
            }
        )
        return ServiceInDB(**service)

    async def get_service_by_id(
            self, *, id: str, requesting_user: UserInDB, populate: bool = True
    ) -> Union[ServiceInDB, ServicePublic]:
        service_record = await self.db.fetch_one(query=GET_SERVICE_BY_ID_QUERY, values={"id": id})

        if service_record:
            service = ServiceInDB(**service_record)
            if populate:
                return await self.populate_service(service=service, requesting_user=requesting_user)
            return service

    async def list_all_user_services(self, requesting_user: UserInDB) -> List[ServiceInDB]:
        services_records = await self.db.fetch_all(
            query=LIST_ALL_USER_SERVICES_QUERY, values={
                "owner": requesting_user.id}
        )

        return [ServiceInDB(**l) for l in services_records]

    async def get_all_services(self) -> List[ServiceInDB]:
        service_records = await self.db.fetch_all(
            query=GET_ALL_SERVICES_QUERY,
        )
        return [ServiceInDB(**l) for l in service_records]

    async def update_service(
            self, *, service: ServiceInDB, service_update: ServiceUpdate
    ) -> ServiceInDB:
        service_update_params = service.model_copy(
            update=service_update.model_dump(exclude_unset=True))

        if service_update_params.service_type is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid service type. Cannot be None."
            )

        updated_service = await self.db.fetch_one(
            query=UPDATE_SERVICE_BY_ID_QUERY,
            values=service_update_params.model_dump(
                exclude={"owner", "created_at", "updated_at"})
        )

        return ServiceInDB(**updated_service)

    async def delete_service_by_id(self, *, id: str, requesting_user: UserInDB) -> int:
        return await self.db.execute(
            query=DELETE_SERVICE_BY_ID_QUERY,
            values={"id": id, "owner": requesting_user.id},
        )

    async def populate_service(self, *, service: ServiceInDB, requesting_user: UserInDB = None) -> ServicePublic:
        return ServicePublic(
            **service.model_dump(exclude={"owner"}),
            owner=await self.users_repo.get_user_by_id(user_id=service.owner),
        )