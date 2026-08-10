import pytest
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.profiles.owner_profile import OwnerProfileInDB
from app.models.auth.user import UserInDB, UserPublic
from app.services import auth_service

pytestmark = pytest.mark.asyncio


class TestClaimOwnerProfile:
    async def test_owner_can_claim_profile_with_valid_token(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        token = auth_service.create_profile_claim_token(profile_id=guest_owner_profile.id)

        new_user = {
            "email": "guest-owner@sample.io",
            "username": "guest_owner",
            "password": "guestOwnerPass123",
        }

        response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": token},
            json=new_user,
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_user = UserPublic(**response.json())
        assert created_user.email == new_user["email"]
        assert created_user.access_token is not None
        assert created_user.profile is not None
        assert created_user.profile.id == guest_owner_profile.id
        assert created_user.profile.full_name == guest_owner_profile.full_name

        profiles_repo = OwnerProfilesRepository(db)
        linked_profile = await profiles_repo.get_profile_by_id(id=guest_owner_profile.id)
        assert linked_profile.user_id == created_user.id

    async def test_claim_fails_with_garbage_token(
            self, app: FastAPI, client: AsyncClient,
    ) -> None:
        new_user = {
            "email": "nope@sample.io",
            "username": "nope_user",
            "password": "nopeUserPass123",
        }

        response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": "not-a-real-token"},
            json=new_user,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_claim_fails_with_expired_token(
            self,
            app: FastAPI,
            client: AsyncClient,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        expired_token = auth_service.create_profile_claim_token(
            profile_id=guest_owner_profile.id, expires_in=-1
        )

        new_user = {
            "email": "late@sample.io",
            "username": "late_user",
            "password": "lateUserPass123",
        }

        response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": expired_token},
            json=new_user,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_claim_fails_for_profile_already_linked_to_a_user(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database,
            user_client_one: UserInDB,
    ) -> None:
        profiles_repo = OwnerProfilesRepository(db)
        linked_profile = await profiles_repo.get_profile_by_user_id(user_id=user_client_one.id)

        token = auth_service.create_profile_claim_token(profile_id=linked_profile.id)

        new_user = {
            "email": "second-claim@sample.io",
            "username": "second_claim",
            "password": "secondClaimPass123",
        }

        response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": token},
            json=new_user,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_claim_fails_when_email_already_taken(
            self,
            app: FastAPI,
            client: AsyncClient,
            guest_owner_profile: OwnerProfileInDB,
            user_client_one: UserInDB,
    ) -> None:
        token = auth_service.create_profile_claim_token(profile_id=guest_owner_profile.id)

        new_user = {
            "email": user_client_one.email,
            "username": "brand_new_username",
            "password": "brandNewPass123",
        }

        response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": token},
            json=new_user,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_cannot_claim_same_profile_twice(
            self,
            app: FastAPI,
            client: AsyncClient,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        first_token = auth_service.create_profile_claim_token(profile_id=guest_owner_profile.id)

        first_response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": first_token},
            json={
                "email": "first-claim@sample.io",
                "username": "first_claim",
                "password": "firstClaimPass123",
            },
        )
        assert first_response.status_code == status.HTTP_201_CREATED

        # A fresh token for the same, now-claimed profile must still be rejected
        second_token = auth_service.create_profile_claim_token(profile_id=guest_owner_profile.id)

        second_response = await client.post(
            app.url_path_for("users:claim-profile"),
            params={"token": second_token},
            json={
                "email": "second-claim@sample.io",
                "username": "second_claim",
                "password": "secondClaimPass123",
            },
        )

        assert second_response.status_code == status.HTTP_400_BAD_REQUEST