from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class UserBase(SQLModel):
    username: str = Field(index=True, min_length=3, max_length=50)
    email: EmailStr = Field(index=True)


class UserCreateIn(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserCreateOut(SQLModel):
    id: int
    username: str
    email: EmailStr


class UserRead(SQLModel):
    id: int
    username: str
    email: EmailStr


class UserUpdateIn(SQLModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)


class UserReplaceIn(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class Users(UserBase, table=True):
    __table_args__ = {"schema": "accounts"}

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password_hash: str