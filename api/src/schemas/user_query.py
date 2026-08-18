from __future__ import annotations

from enum import Enum

from fastapi import Query

from src.core.pagination import SortOrder


class UserSortField(str, Enum):
    ID = "id"
    USERNAME = "username"
    EMAIL = "email"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class UserFilterParams:
    def __init__(
        self,
        q: str | None = Query(default=None, min_length=1, max_length=100),
        is_active: bool | None = Query(default=None),
        sort_by: UserSortField = Query(default=UserSortField.ID),
        sort_order: SortOrder = Query(default=SortOrder.ASC),
    ) -> None:
        self.q = q
        self.is_active = is_active
        self.sort_by = sort_by
        self.sort_order = sort_order
