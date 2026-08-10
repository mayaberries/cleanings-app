from fastapi import Depends, APIRouter, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from app.api.dependencies.database import get_repository
from app.api.dependencies.profiles import get_profile_from_claim_token
from app.models.auth.user import UserCreate, UserInDB, UserPublic
from app.models.profiles.owner_profile import OwnerProfileInDB

from app.db.repositories.users import UsersRepository
from app.models.auth.token import AccessToken
from app.services import auth_service
from app.api.dependencies.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=UserPublic, name="users:register-new-user", status_code=HTTP_201_CREATED)
async def register_new_user(
        new_user: UserCreate = Body(..., embed=False),
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    created_user = await user_repo.register_new_user(new_user=new_user)

    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user),
        token_type="bearer"
    )

    return created_user.model_copy(update={"access_token": access_token})


@router.post("/claim/", response_model=UserPublic, name="users:claim-profile", status_code=HTTP_201_CREATED)
async def claim_owner_profile(
        new_user: UserCreate = Body(..., embed=False),
        profile: OwnerProfileInDB = Depends(get_profile_from_claim_token),
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    """Turns an account-less owner profile (created by a clinic, or through
    the embeddable widget) into a real login — the ?token= query param is
    what proves the caller was the intended recipient of that profile."""
    created_user = await user_repo.register_user_for_existing_profile(
        new_user=new_user, existing_profile_id=profile.id
    )

    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=created_user),
        token_type="bearer"
    )

    return created_user.model_copy(update={"access_token": access_token})


@router.post("/login/token", response_model=AccessToken, name="users:login-email-and-password")
async def user_login_with_email_and_password(
        user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
) -> AccessToken:
    user = await user_repo.authenticate_user(email=form_data.username, password=form_data.password)

    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = AccessToken(
        access_token=auth_service.create_access_token_for_user(user=user),
        token_type="bearer"
    )

    return access_token


@router.get("/me/", response_model=UserPublic, name="users:get-current-user")
async def get_currently_authenticated_user(current_user: UserInDB = Depends(get_current_active_user)) -> UserPublic:
    return current_user
