from typing import List, Optional, Union
from databases.core import Database

from fastapi.exceptions import HTTPException
from starlette import status
from app.db.repositories.base import BaseRepository
from app.models.clinics.clinic import ClinicPublic
from app.models.services.service import ServiceCreate, ServicePublic, ServiceUpdate, ServiceInDB
from uuid import uuid4

from app.models.auth.user import UserInDB
from app.db.repositories.clinics import ClinicsRepository

CREATE_SERVICE_QUERY = """
    INSERT INTO services (id, name, description, price, category, duration_minutes, clinic_id)
    VALUES (:id, :name, :description, :price, :category, :duration_minutes, :clinic_id)
    RETURNING id, name, description, price, category, duration_minutes, clinic_id, created_at, updated_at;
"""

GET_SERVICE_BY_ID_QUERY = """
    SELECT id, name, description, price, category, duration_minutes, clinic_id, created_at, updated_at
    FROM services
    WHERE id = :id;
"""

GET_ALL_SERVICES_QUERY = """
    SELECT id, name, description, price, category, duration_minutes
    FROM services;
"""

LIST_ALL_CLINIC_SERVICES_QUERY = """
    SELECT id, name, description, price, category, duration_minutes, clinic_id, created_at, updated_at
    FROM services
    WHERE clinic_id = :clinic_id;
"""

UPDATE_SERVICE_BY_ID_QUERY = """
    UPDATE services
    SET name              = :name,
        description       = :description,
        price             = :price,
        category          = :category,
        duration_minutes  = :duration_minutes
    WHERE id = :id
    RETURNING id, name, description, price, category, duration_minutes, clinic_id, created_at, updated_at;
"""

DELETE_SERVICE_BY_ID_QUERY = """
    DELETE FROM services
    WHERE id = :id AND clinic_id = :clinic_id
    RETURNING id;
"""


class ServicesRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.clinics_repo = ClinicsRepository(db)

    async def create_service(self, *, new_service: ServiceCreate, requesting_user: UserInDB) -> ServicePublic:
        if not requesting_user.clinic_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must belong to a clinic to create a service.",
            )

        service = await self.db.fetch_one(
            query=CREATE_SERVICE_QUERY,
            values={
                **new_service.model_dump(),
                "id": str(uuid4()),
                "clinic_id": requesting_user.clinic_id,
            },
        )
        return await self.populate_service(service=ServiceInDB(**service))

    async def get_service_by_id(
            self, *, id: str, requesting_user: UserInDB, populate: bool = True
    ) -> Union[ServiceInDB, ServicePublic]:
        service_record = await self.db.fetch_one(query=GET_SERVICE_BY_ID_QUERY, values={"id": id})

        if service_record:
            service = ServiceInDB(**service_record)
            if populate:
                return await self.populate_service(service=service)
            return service

    async def list_all_clinic_services(self, requesting_user: UserInDB) -> List[ServicePublic]:
        if not requesting_user.clinic_id:
            return []
        return await self.list_services_by_clinic_id(clinic_id=requesting_user.clinic_id)

    async def list_services_by_clinic_id(self, *, clinic_id: str) -> List[ServicePublic]:
        """
        Same query as list_all_clinic_services, split out to take a bare
        clinic_id instead of a UserInDB. Used by the public booking surface
        (app/api/routes/public_booking.py), where the clinic comes from a
        resolved public API key rather than a logged-in user -- there is no
        UserInDB in that request path at all.
        """
        records = await self.db.fetch_all(
            query=LIST_ALL_CLINIC_SERVICES_QUERY, values={"clinic_id": clinic_id}
        )
        return [await self.populate_service(service=ServiceInDB(**r)) for r in records]

    async def get_service_by_id_for_clinic(self, *, id: str, clinic_id: str) -> Optional[ServiceInDB]:
        """
        Used by the public booking surface (public_booking.py) to confirm
        the requested service actually belongs to the key-resolved clinic
        before anything is booked against it -- a key for clinic A can
        never book, or even confirm the existence of, clinic B's services.
        Returns the bare ServiceInDB (not populated/ServicePublic) since
        callers here just need duration_minutes and id, not a nested
        clinic object they already have.
        """
        service_record = await self.db.fetch_one(query=GET_SERVICE_BY_ID_QUERY, values={"id": id})
        if not service_record:
            return None

        service = ServiceInDB(**service_record)
        if service.clinic_id != clinic_id:
            return None

        return service

    async def get_all_services(self) -> List[ServiceInDB]:
        service_records = await self.db.fetch_all(query=GET_ALL_SERVICES_QUERY)
        return [ServiceInDB(**l) for l in service_records]

    async def update_service(self, *, service: ServicePublic, service_update: ServiceUpdate) -> ServicePublic:
        service_update_params = service.model_copy(update=service_update.model_dump(exclude_unset=True))

        if service_update_params.category is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid service type. Cannot be None."
            )

        updated_service = await self.db.fetch_one(
            query=UPDATE_SERVICE_BY_ID_QUERY,
            values=service_update_params.model_dump(exclude={"clinic", "created_at", "updated_at"})
        )
        return await self.populate_service(service=ServiceInDB(**updated_service))

    async def delete_service_by_id(self, *, id: str, requesting_user: UserInDB) -> int:
        return await self.db.execute(
            query=DELETE_SERVICE_BY_ID_QUERY,
            values={"id": id, "clinic_id": requesting_user.clinic_id},
        )

    async def populate_service(self, *, service: ServiceInDB) -> ServicePublic:
        clinic = await self.clinics_repo.get_clinic_by_id(id=service.clinic_id)
        return ServicePublic(
            **service.model_dump(exclude={"clinic_id"}),
            clinic=ClinicPublic(**clinic.model_dump()) if clinic else service.clinic_id,
        )