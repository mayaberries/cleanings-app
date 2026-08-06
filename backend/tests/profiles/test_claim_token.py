import pytest
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.core.config import SECRET_KEY
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.owner_profile import OwnerProfileInDB
from app.models.token import ProfileClaimTokenResponse
from app.models.user import UserInDB
from app.services import auth_service

pytestmark = pytest.mark.asyncio


class TestCreateProfileClaimToken:
    async def test_clinic_admin_can_create_claim_token_for_unclaimed_profile(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("profiles:create-claim-token", profile_id=guest_owner_profile.id)
        )

        assert response.status_code == status.HTTP_200_OK

        token_response = ProfileClaimTokenResponse(**response.json())
        assert token_response.token_type == "profile_claim"

        profile_id = auth_service.get_profile_id_from_claim_token(
            token=token_response.token, secret_key=str(SECRET_KEY)
        )
        assert profile_id == guest_owner_profile.id

    async def test_clinic_aux_can_create_claim_token(
            self,
            app: FastAPI,
            create_authorized_client,
            user_clinic_a_aux: UserInDB,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        aux_client = create_authorized_client(user=user_clinic_a_aux)

        response = await aux_client.post(
            app.url_path_for("profiles:create-claim-token", profile_id=guest_owner_profile.id)
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_regular_client_cannot_create_claim_token(
            self,
            app: FastAPI,
            create_authorized_client,
            user_client_one: UserInDB,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        client_user = create_authorized_client(user=user_client_one)

        response = await client_user.post(
            app.url_path_for("profiles:create-claim-token", profile_id=guest_owner_profile.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_unauthenticated_request_is_rejected(
            self,
            app: FastAPI,
            client: AsyncClient,
            guest_owner_profile: OwnerProfileInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("profiles:create-claim-token", profile_id=guest_owner_profile.id)
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_404_for_nonexistent_profile(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient,
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("profiles:create-claim-token", profile_id="00000000-0000-0000-0000-000000000000")
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_400_when_profile_already_linked_to_a_user(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            user_client_one: UserInDB,
            db: Database,
    ) -> None:
        profiles_repo = OwnerProfilesRepository(db)
        linked_profile = await profiles_repo.get_profile_by_user_id(user_id=user_client_one.id)

        response = await clinic_a_admin_client.post(
            app.url_path_for("profiles:create-claim-token", profile_id=linked_profile.id)
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
