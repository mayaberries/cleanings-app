import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.owner_profile import OwnerProfileInDB
from app.models.pet_profile import PetProfileInDB, PetProfilePublic
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestCreateClinicPet:
    async def test_clinic_staff_can_create_pet_for_registered_owner(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            owner_registered_with_clinic_a: OwnerProfileInDB,
    ) -> None:
        new_pet = {"name": "Bella", "species": "dog", "owner_profile_id": owner_registered_with_clinic_a.id}

        response = await clinic_a_admin_client.post(app.url_path_for("clinic_pets:create-pet"), json=new_pet)

        assert response.status_code == status.HTTP_201_CREATED

        created_pet = PetProfilePublic(**response.json())
        assert created_pet.name == "Bella"
        assert created_pet.owner_profile_id == owner_registered_with_clinic_a.id

    async def test_clinic_staff_cannot_create_pet_for_owner_not_registered_with_their_clinic(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            owner_registered_with_clinic_b: OwnerProfileInDB,
    ) -> None:
        new_pet = {"name": "Rex", "species": "dog", "owner_profile_id": owner_registered_with_clinic_b.id}

        response = await clinic_a_admin_client.post(app.url_path_for("clinic_pets:create-pet"), json=new_pet)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_regular_client_cannot_create_clinic_pet(
            self,
            app: FastAPI,
            create_authorized_client,
            user_client_one: UserInDB,
            owner_registered_with_clinic_a: OwnerProfileInDB,
    ) -> None:
        client_user = create_authorized_client(user=user_client_one)
        new_pet = {"name": "Milo", "species": "cat", "owner_profile_id": owner_registered_with_clinic_a.id}

        response = await client_user.post(app.url_path_for("clinic_pets:create-pet"), json=new_pet)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_unauthenticated_cannot_create_clinic_pet(
            self,
            app: FastAPI,
            client: AsyncClient,
            owner_registered_with_clinic_a: OwnerProfileInDB,
    ) -> None:
        new_pet = {"name": "Milo", "species": "cat", "owner_profile_id": owner_registered_with_clinic_a.id}

        response = await client.post(app.url_path_for("clinic_pets:create-pet"), json=new_pet)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListClinicPets:
    async def test_clinic_staff_can_list_all_pets_for_their_clinic(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(app.url_path_for("clinic_pets:list-pets"))

        assert response.status_code == status.HTTP_200_OK
        pets = [PetProfilePublic(**p) for p in response.json()]
        assert any(p.id == clinic_a_pet.id for p in pets)

    async def test_clinic_pet_list_excludes_other_clinics_pets(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
            clinic_b_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(app.url_path_for("clinic_pets:list-pets"))

        assert response.status_code == status.HTTP_200_OK
        pet_ids = [p["id"] for p in response.json()]
        assert clinic_a_pet.id in pet_ids
        assert clinic_b_pet.id not in pet_ids

    async def test_clinic_staff_can_filter_pets_by_owner(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
            owner_registered_with_clinic_a: OwnerProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic_pets:list-pets"),
            params={"owner_profile_id": owner_registered_with_clinic_a.id},
        )

        assert response.status_code == status.HTTP_200_OK
        pets = [PetProfilePublic(**p) for p in response.json()]
        assert all(p.owner_profile_id == owner_registered_with_clinic_a.id for p in pets)
        assert any(p.id == clinic_a_pet.id for p in pets)

    async def test_filtering_by_owner_not_registered_with_clinic_is_rejected(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            owner_registered_with_clinic_b: OwnerProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic_pets:list-pets"),
            params={"owner_profile_id": owner_registered_with_clinic_b.id},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetUpdateDeleteClinicPet:
    async def test_clinic_staff_can_get_pet_by_id(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic_pets:get-pet-by-id", pet_id=clinic_a_pet.id)
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == clinic_a_pet.id

    async def test_clinic_staff_cannot_get_another_clinics_pet(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_b_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic_pets:get-pet-by-id", pet_id=clinic_b_pet.id)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_clinic_staff_can_update_pet(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic_pets:update-pet-by-id", pet_id=clinic_a_pet.id),
            json={"notes": "Recovering from surgery, monitor appetite."},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["notes"] == "Recovering from surgery, monitor appetite."

    async def test_clinic_staff_cannot_update_another_clinics_pet(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_b_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic_pets:update-pet-by-id", pet_id=clinic_b_pet.id),
            json={"notes": "should not apply"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_clinic_staff_can_delete_pet(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_a_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for("clinic_pets:delete-pet-by-id", pet_id=clinic_a_pet.id)
        )

        assert response.status_code == status.HTTP_200_OK

        follow_up = await clinic_a_admin_client.get(
            app.url_path_for("clinic_pets:get-pet-by-id", pet_id=clinic_a_pet.id)
        )
        assert follow_up.status_code == status.HTTP_404_NOT_FOUND

    async def test_clinic_staff_cannot_delete_another_clinics_pet(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_b_pet: PetProfileInDB,
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for("clinic_pets:delete-pet-by-id", pet_id=clinic_b_pet.id)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND