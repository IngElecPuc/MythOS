from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.config.config import get_settings
from src.integrations.dependencies import SessionDep
from src.schemas.auth import UserRead, Users


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class TokenService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def encode(self, user_id: int, username: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.access_token_expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "username": username,
            "email": email,
            "exp": expire,
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )

    def decode(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.settings.jwt_secret,
            algorithms=[self.settings.jwt_algorithm],
        )


def encode_token(user_id: int, username: str, email: str) -> str:
    return TokenService().encode(user_id, username, email)


def decode_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: SessionDep,
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        data = TokenService().decode(token)
        user_id = data.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    account = db.get(Users, int(user_id))
    if not account:
        raise credentials_exception

    return UserRead.model_validate(account).model_dump()


Token = Annotated[dict, Depends(decode_token)]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))