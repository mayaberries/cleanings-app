from typing import List, Union
from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository

from app.models.offer import OfferCreate, OfferPublic, OfferUpdate, OfferInDB
from app.models.service import ServiceInDB
from app.models.user import UserInDB

CREATE_OFFER_FOR_SERVICE_QUERY = """
    INSERT INTO user_offers_for_services (service_id, user_id, status)
    VALUES (:service_id, :user_id, :status)
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

LIST_OFFERS_FOR_SERVICE_QUERY = """
    SELECT service_id, user_id, status, created_at, updated_at
    FROM user_offers_for_services
    WHERE service_id = :service_id;
"""

GET_OFFER_FOR_SERVICE_FROM_USER_QUERY = """
    SELECT service_id, user_id, status, created_at, updated_at
    FROM user_offers_for_services
    WHERE service_id = :service_id AND user_id = :user_id;
"""

ACCEPT_OFFER_QUERY = """
    UPDATE user_offers_for_services
    SET status = 'accepted'
    WHERE service_id = :service_id AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

REJECT_ALL_OTHER_OFFERS_QUERY = """
    UPDATE user_offers_for_services
    SET status = 'rejected'
    WHERE service_id = :service_id
    AND user_id != :user_id
    AND status = 'pending';
"""

CANCEL_OFFER_QUERY = """
    UPDATE user_offers_for_services
    SET status = 'cancelled'
    WHERE service_id = :service_id AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

SET_ALL_OTHER_OFFERS_AS_PENDING_QUERY = """
    UPDATE user_offers_for_services
    SET status = 'pending'
    WHERE service_id = :service_id 
    AND user_id != :user_id 
    AND status = 'rejected'
"""

RESCIND_OFFER_QUERY = """
    DELETE FROM user_offers_for_services
    WHERE service_id = :service_id
    AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

MARK_AS_COMPLETED_QUERY = """
    UPDATE user_offers_for_services
    SET status = 'completed'
    WHERE service_id = :service_id AND user_id = :user_id
"""


class OffersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_offer_for_service(self, *, new_offer: OfferCreate) -> OfferInDB:
        created_offer = await self.db.fetch_one(
            query=CREATE_OFFER_FOR_SERVICE_QUERY,
            values={**new_offer.model_dump(), "status": "pending"}
        )
        return OfferInDB(**created_offer)

    async def list_offers_for_service(
            self, *, service: ServiceInDB, populate: bool = True
    ) -> List[Union[OfferInDB, OfferPublic]]:
        offer_records = await self.db.fetch_all(
            query=LIST_OFFERS_FOR_SERVICE_QUERY,
            values={"service_id": service.id}
        )
        offers = [OfferInDB(**o) for o in offer_records]

        if populate:
            return [await self.populate_offer(offer=offer) for offer in offers]

        return offers

    async def get_offer_for_service_from_user(self, *, service: ServiceInDB, user: UserInDB) -> OfferInDB:
        offer_record = await self.db.fetch_one(
            query=GET_OFFER_FOR_SERVICE_FROM_USER_QUERY,
            values={"service_id": service.id, "user_id": user.id}
        )

        if not offer_record:
            return None

        return OfferInDB(**offer_record)

    async def accept_offer(self, *, offer: OfferInDB) -> OfferInDB:
        async with self.db.transaction():
            accepted_offer = await self.db.fetch_one(
                query=ACCEPT_OFFER_QUERY,
                values={"service_id": offer.service_id,
                        "user_id": offer.user_id}
            )

            await self.db.execute(
                query=REJECT_ALL_OTHER_OFFERS_QUERY,
                values={"service_id": offer.service_id,
                        "user_id": offer.user_id}
            )

            return OfferInDB(**accepted_offer)

    async def cancel_offer(self, *, offer: OfferInDB) -> OfferInDB:
        async with self.db.transaction():
            canceled_offer = await self.db.fetch_one(
                query=CANCEL_OFFER_QUERY,
                values={"service_id": offer.service_id,
                        "user_id": offer.user_id}
            )

            await self.db.execute(
                query=SET_ALL_OTHER_OFFERS_AS_PENDING_QUERY,
                values={"service_id": offer.service_id,
                        "user_id": offer.user_id}
            )

            return OfferInDB(**canceled_offer)

    async def rescind_offer(self, *, offer: OfferInDB) -> OfferInDB:
        rescinded_offer = await self.db.fetch_one(
            query=RESCIND_OFFER_QUERY,
            values={
                "service_id": offer.service_id,
                "user_id": offer.user_id
            }
        )
        return OfferInDB(**rescinded_offer)

    async def mark_as_completed(self, *, service: ServiceInDB, cleaner: UserInDB) -> OfferInDB:
        return await self.db.execute(
            query=MARK_AS_COMPLETED_QUERY,
            values={
                "service_id": service.id,
                "user_id": cleaner.id
            }
        )

    async def populate_offer(self, *, offer: OfferInDB) -> OfferPublic:
        return OfferPublic(
            **offer.model_dump(),
            user=await self.users_repo.get_user_by_id(
                user_id=offer.user_id
            )
        )