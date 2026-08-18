from __future__ import annotations

from enum import Enum
from math import ceil
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PageMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)


class Page(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    items: list[T]
    meta: PageMeta

    @classmethod
    def build(
        cls,
        *,
        items: list[T],
        total: int,
        params: PaginationParams,
    ) -> "Page[T]":
        pages = ceil(total / params.page_size) if total else 0
        return cls(
            items=items,
            meta=PageMeta(
                page=params.page,
                page_size=params.page_size,
                total=total,
                pages=pages,
            ),
        )
