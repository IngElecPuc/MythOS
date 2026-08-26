from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, Text, ForeignKey, Integer, ForeignKeyConstraint, SmallInteger
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field

from src.models.base import TimestampMixin, EmbeddingMixin

class Disciplines(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "disciplines"
    __table_args__ = {"schema": "vampire_v5"}

    discipline_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True)
    nicknames: List[str] = Field(sa_column=Column(ARRAY(Text), nullable=False))
    description: str
    characteristics: Optional[str] = Field(default=None)
    type: str
    threat: str
    resonance: str
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str


class Powers(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "powers"
    __table_args__ = {"schema": "vampire_v5"}

    discipline_id: int = Field(
            sa_column=Column(
                Integer,
                ForeignKey("vampire_v5.disciplines.discipline_id", ondelete="CASCADE"),
                primary_key=True,
            )
        )
    title: str = Field(max_length=255, primary_key=True)
    level: int = Field(ge=1, le=5, nullable=False)
    description: str
    cost: str
    dice_pool: Optional[str] = Field(default=None)
    system: str
    duration: str
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str

class Requirements(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "requirements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["discipline_id", "title"],
            ["vampire_v5.powers.discipline_id", "vampire_v5.powers.title"],
        ),
        ForeignKeyConstraint(
            ["discipline_id", "requirement"],
            ["vampire_v5.powers.discipline_id", "vampire_v5.powers.title"],
        ),
        {"schema": "vampire_v5"},
    )

    discipline_id: int = Field(primary_key=True)
    title: str = Field(max_length=255, primary_key=True)
    requirement: str = Field(max_length=255)
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str

class Amalgamations(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "amalgamations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["discipline_id", "title"],
            ["vampire_v5.powers.discipline_id", "vampire_v5.powers.title"],
        ),
        {"schema": "vampire_v5"},
    )

    discipline_id: int = Field(primary_key=True)
    title: str = Field(max_length=255, primary_key=True)
    discipline_req: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("vampire_v5.disciplines.discipline_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    level: int = Field(sa_column=Column(SmallInteger, nullable=False), ge=1, le=5)
    source: Optional[str] = Field(default="Casera")
    created_by: str
    updated_by: str


class Rituals(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "rituals"
    __table_args__ = {"schema": "vampire_v5"}

    ritual_id: int = Field(primary_key=True)
    title: str = Field(max_length=255, unique=True)
    level: int = Field(ge=1, le=5)
    description: str
    ingredients: str
    process: Optional[str] = Field(default=None)
    system: Optional[str] = Field(default=None)
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str


class BloodAlquemy(TimestampMixin, EmbeddingMixin, table=True):
    __tablename__ = "blood_alquemy"
    __table_args__ = {"schema": "vampire_v5"}

    potion_id: int = Field(primary_key=True)
    title: str = Field(max_length=255, unique=True)
    level: int = Field(ge=1, le=5)
    description: str
    ingredients: str
    cost: Optional[str] = Field(default=None)
    dice_pool: Optional[str] = Field(default=None)
    system: str
    duration: str
    athanor_corporis: Optional[str] = Field(default=None)
    calcinatio: Optional[str] = Field(default=None)
    source: str = Field(default="Casera")
    created_by: str
    updated_by: str