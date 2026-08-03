from typing import List, Union
from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository

from app.models.offer import OfferCreate, OfferPublic, OfferUpdate, OfferInDB
from app.models.cleaning import CleaningInDB
from app.models.user import UserInDB

CREATE_OFFER_FOR_CLEANING_QUERY = """
    INSERT INTO user_offers_for_cleanings (cleaning_id, user_id, status)
    VALUES (:cleaning_id, :user_id, :status)
    RETURNING cleaning_id, user_id, status, created_at, updated_at;
"""

LIST_OFFERS_FOR_CLEANING_QUERY = """
    SELECT cleaning_id, user_id, status, created_at, updated_at
    FROM user_offers_for_cleanings
    WHERE cleaning_id = :cleaning_id;
"""

GET_OFFER_FOR_CLEANING_FROM_USER_QUERY = """
    SELECT cleaning_id, user_id, status, created_at, updated_at
    FROM user_offers_for_cleanings
    WHERE cleaning_id = :cleaning_id AND user_id = :user_id;
"""

ACCEPT_OFFER_QUERY = """
    UPDATE user_offers_for_cleanings
    SET status = 'accepted'
    WHERE cleaning_id = :cleaning_id AND user_id = :user_id
    RETURNING cleaning_id, user_id, status, created_at, updated_at;
"""

REJECT_ALL_OTHER_OFFERS_QUERY = """
    UPDATE user_offers_for_cleanings
    SET status = 'rejected'
    WHERE cleaning_id = :cleaning_id
    AND user_id != :user_id
    AND status = 'pending';
"""

CANCEL_OFFER_QUERY = """
    UPDATE user_offers_for_cleanings
    SET status = 'cancelled'
    WHERE cleaning_id = :cleaning_id AND user_id = :user_id
    RETURNING cleaning_id, user_id, status, created_at, updated_at;
"""

SET_ALL_OTHER_OFFERS_AS_PENDING_QUERY = """
    UPDATE user_offers_for_cleanings
    SET status = 'pending'
    WHERE cleaning_id = :cleaning_id 
    AND user_id != :user_id 
    AND status = 'rejected'
"""

RESCIND_OFFER_QUERY = """
    DELETE FROM user_offers_for_cleanings
    WHERE cleaning_id = :cleaning_id
    AND user_id = :user_id
    RETURNING cleaning_id, user_id, status, created_at, updated_at;
"""

MARK_AS_COMPLETED_QUERY = """
    UPDATE user_offers_for_cleanings
    SET status = 'completed'
    WHERE cleaning_id = :cleaning_id AND user_id = :user_id
"""


class OffersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_offer_for_cleaning(self, *, new_offer: OfferCreate) -> OfferInDB:
        created_offer = await self.db.fetch_one(
            query=CREATE_OFFER_FOR_CLEANING_QUERY,
            values={**new_offer.model_dump(), "status": "pending"}
        )
        return OfferInDB(**created_offer)

    async def list_offers_for_cleaning(
            self, *, cleaning: CleaningInDB, populate: bool = True
    ) -> List[Union[OfferInDB, OfferPublic]]:
        offer_records = await self.db.fetch_all(
            query=LIST_OFFERS_FOR_CLEANING_QUERY,
            values={"cleaning_id": cleaning.id}
        )
        offers = [OfferInDB(**o) for o in offer_records]

        if populate:
            return [await self.populate_offer(offer=offer) for offer in offers]

        return offers

    async def get_offer_for_cleaning_from_user(self, *, cleaning: CleaningInDB, user: UserInDB) -> OfferInDB:
        offer_record = await self.db.fetch_one(
            query=GET_OFFER_FOR_CLEANING_FROM_USER_QUERY,
            values={"cleaning_id": cleaning.id, "user_id": user.id}
        )

        if not offer_record:
            return None

        return OfferInDB(**offer_record)

    async def accept_offer(self, *, offer: OfferInDB) -> OfferInDB:
        async with self.db.transaction():
            accepted_offer = await self.db.fetch_one(
                query=ACCEPT_OFFER_QUERY,
                values={"cleaning_id": offer.cleaning_id,
                        "user_id": offer.user_id}
            )

            await self.db.execute(
                query=REJECT_ALL_OTHER_OFFERS_QUERY,
                values={"cleaning_id": offer.cleaning_id,
                        "user_id": offer.user_id}
            )

            return OfferInDB(**accepted_offer)

    async def cancel_offer(self, *, offer: OfferInDB) -> OfferInDB:
        async with self.db.transaction():
            canceled_offer = await self.db.fetch_one(
                query=CANCEL_OFFER_QUERY,
                values={"cleaning_id": offer.cleaning_id,
                        "user_id": offer.user_id}
            )

            await self.db.execute(
                query=SET_ALL_OTHER_OFFERS_AS_PENDING_QUERY,
                values={"cleaning_id": offer.cleaning_id,
                        "user_id": offer.user_id}
            )

            return OfferInDB(**canceled_offer)

    async def rescind_offer(self, *, offer: OfferInDB) -> OfferInDB:
        rescinded_offer = await self.db.fetch_one(
            query=RESCIND_OFFER_QUERY,
            values={
                "cleaning_id": offer.cleaning_id,
                "user_id": offer.user_id
            }
        )
        return OfferInDB(**rescinded_offer)

    async def mark_as_completed(self, *, cleaning: CleaningInDB, cleaner: UserInDB) -> OfferInDB:
        return await self.db.execute(
            query=MARK_AS_COMPLETED_QUERY,
            values={
                "cleaning_id": cleaning.id,
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