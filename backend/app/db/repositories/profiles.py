from uuid import uuid4

from sqlalchemy.sql.expression import true
from app.db.repositories.base import BaseRepository
from app.models.profile import ProfileCreate, ProfileUpdate, ProfileInDB
from app.models.user import UserInDB

CREATE_PROFILE_FOR_USER_QUERY = """
    INSERT INTO profiles (id, full_name, phone_number, bio, image, user_id)
    VALUES (:id, :full_name, :phone_number, :bio, :image, :user_id)
    RETURNING id, full_name, phone_number, bio, image, user_id, created_at, updated_at;
"""

GET_PROFILE_BY_USER_ID_QUERY = """
    SELECT id, full_name, phone_number, bio, image, user_id, created_at, updated_at
    FROM profiles
    WHERE user_id = :user_id;
"""

GET_PROFILE_BY_USERNAME_QUERY = """
    SELECT p.id,
           u.email AS email,
           u.username AS username,
           full_name,
           phone_number,
           bio,
           image,
           user_id,
           p.created_at,
           p.updated_at
    FROM profiles p
        INNER JOIN users u 
        ON p.user_id = u.id
    WHERE user_id = (SELECT id FROM users WHERE username = :username);
"""

UPDATE_PROFILE_QUERY = """
    UPDATE profiles
    SET full_name    = :full_name,
        phone_number = :phone_number,
        bio          = :bio,
        image        = :image
    WHERE user_id = :user_id
    RETURNING id, full_name, phone_number, bio, image, user_id, created_at, updated_at;
"""


class ProfilesRepository(BaseRepository):
    async def create_profile_for_user(self, *, profile_create: ProfileCreate) -> ProfileInDB:
        values = {**profile_create.model_dump(), "id": str(uuid4())}

        if values.get("image") is not None:
            values["image"] = str(values["image"])

        created_profile = await self.db.fetch_one(
            query=CREATE_PROFILE_FOR_USER_QUERY,
            values=values,
        )

        return created_profile

    async def get_profile_by_user_id(self, *, user_id: str) -> ProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USER_ID_QUERY, values={"user_id": user_id})

        if not profile_record:
            return None

        return ProfileInDB(**profile_record)

    async def get_profile_by_username(self, *, username: str) -> ProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USERNAME_QUERY, values={"username": username})

        if profile_record:
            return ProfileInDB(**profile_record)

    async def update_profile(self, *, profile_update: ProfileUpdate, requesting_user: UserInDB) -> ProfileInDB:
        profile = await self.get_profile_by_user_id(user_id=requesting_user.id)

        update_params = profile.model_copy(
            update=profile_update.model_dump(exclude_unset=True))

        values = update_params.model_dump(
            exclude={"id", "created_at", "updated_at", "username", "email"})

        if values.get("image") is not None:
            values["image"] = str(values["image"])

        updated_profile = await self.db.fetch_one(
            query=UPDATE_PROFILE_QUERY,
            values=values,
        )

        return ProfileInDB(**updated_profile)
