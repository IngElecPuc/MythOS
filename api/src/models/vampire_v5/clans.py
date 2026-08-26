from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field

from src.models.base import TimestampMixin, EmbeddingMixin

class Clans(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "clans"
    __table_args__ = {"schema": "vampire_v5"}

    clan_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True)
    nicknames: List[str] = Field(sa_column=Column(ARRAY(Text), nullable=False))
    description: str
    who_are_they: str
    prohibitions: Optional[str] = Field(default=None)
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str


class Arquetipes(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "arquetipes"
    __table_args__ = {"schema": "vampire_v5"}

    clan_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("vampire_v5.clans.clan_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    title: str = Field(max_length=255, primary_key=True)
    description: str
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str


class ClanDisciplines(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "clan_disciplines"
    __table_args__ = {"schema": "vampire_v5"}

    clan_id: int = Field(
            sa_column=Column(
                Integer,
                ForeignKey("vampire_v5.clans.clan_id", ondelete="CASCADE"),
                primary_key=True,
            )
        )
    title: str = Field(max_length=255, primary_key=True)
    description: str
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str
