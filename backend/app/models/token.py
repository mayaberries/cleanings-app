from datetime import datetime, timezone, timedelta
from pydantic import EmailStr

from app.core.config import JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.core import CoreModel


class JWTMeta(CoreModel):
    iss: str = "stitcher.io"
    aud: str = JWT_AUDIENCE
    iat: float = datetime.timestamp(datetime.now(timezone.utc))
    exp: float = datetime.timestamp(
        datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


class JWTCreds(CoreModel):
    sub: EmailStr
    username: str


class JWTPayload(JWTMeta, JWTCreds):
    pass


class AccessToken(CoreModel):
    access_token: str
    token_type: str