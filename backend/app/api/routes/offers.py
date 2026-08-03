from typing import List
from fastapi import APIRouter, Path, Body, status, HTTPException
from fastapi.param_functions import Depends

from app.models.offer import OfferCreate, OfferUpdate, OfferInDB, OfferPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

from app.api.dependencies.services import get_service_by_id_from_path
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.offers import (
    check_offer_acceptance_permissions,
    check_offer_cancel_permissions,
    check_offer_create_permissions,
    check_offer_get_permissions,
    check_offer_list_permissions,
    get_offer_for_service_from_current_user,
    get_offer_for_service_from_user_by_path,
    list_offers_for_service_by_id_from_path,
    check_offer_rescind_permissions
)

from app.db.repositories.offers import OffersRepository


router = APIRouter()


@router.post(
    "/",
    response_model=OfferPublic,
    name="offers:create-offer",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_offer_create_permissions)]
)
async def create_offer(
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    offers_repo: OffersRepository = Depends(get_repository(OffersRepository))
) -> OfferPublic:
    return await offers_repo.create_offer_for_service(
        new_offer=OfferCreate(service_id=service.id, user_id=current_user.id)
    )


@router.get(
    "/",
    response_model=List[OfferPublic],
    name="offers:list-offers-for-service",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_offer_list_permissions)]
)
async def list_offer_for_service(
    offers: List[OfferInDB] = Depends(list_offers_for_service_by_id_from_path)
) -> List[OfferPublic]:
    return offers


@router.get(
    "/{username}",
    response_model=OfferPublic,
    name="offers:get-offer-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_offer_get_permissions)]
)
async def get_offer_from_user(
    offer: OfferInDB = Depends(get_offer_for_service_from_user_by_path)
) -> OfferPublic:
    return offer


@router.put(
    "/{username}",
    response_model=OfferPublic,
    name="offers:accept-offer-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_offer_acceptance_permissions)]
)
async def accept_offer_from_user(
    offer: OfferInDB = Depends(get_offer_for_service_from_user_by_path),
    offers_repo: OffersRepository = Depends(get_repository(OffersRepository))
) -> OfferPublic:
    return await offers_repo.accept_offer(
        offer=offer
    )


@router.put(
    "/",
    response_model=OfferPublic,
    name="offers:cancel-offer-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_offer_cancel_permissions)]
)
async def cancel_offer_from_user(
    offer: OfferInDB = Depends(get_offer_for_service_from_current_user),
    offers_repo: OffersRepository = Depends(get_repository(OffersRepository))
) -> OfferPublic:
    return await offers_repo.cancel_offer(
        offer=offer,
    )


@router.delete(
    "/",
    response_model=OfferPublic,
    name="offers:rescind-offer-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_offer_rescind_permissions)]
)
async def rescind_offer_from_user(
    offer: OfferInDB = Depends(get_offer_for_service_from_current_user),
    offers_repo: OffersRepository = Depends(get_repository(OffersRepository))
) -> OfferPublic:
    rescinded_offer = await offers_repo.rescind_offer(offer=offer)
    return await offers_repo.populate_offer(offer=rescinded_offer)