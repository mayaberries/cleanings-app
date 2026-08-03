from pydantic import EmailStr

from app.core.config import JWT_AUDIENCE
from app.models.core import CoreModel


class JWTMeta(CoreModel):
    iss: str = "stitcher.io"
    aud: str = JWT_AUDIENCE
    iat: float
    exp: float


class JWTCreds(CoreModel):
    sub: EmailStr
    username: str


class JWTPayload(JWTMeta, JWTCreds):
    pass


class AccessToken(CoreModel):
    access_token: str
    token_type: str