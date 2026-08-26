from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    pass

class UserReplace(UserCreate):
    pass

class UserUpdate(BaseModel):
    pass

class UserRead(BaseModel):
    pass