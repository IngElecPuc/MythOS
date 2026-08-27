from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Column
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector
from src.config.config import get_settings

def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        nullable=False,
    )

# Ajusta esto a la dimensión real del modelo de embedding que uses.
# embeddinggemma (Ollama) = 768 · bge-m3 = 1024 · multilingual-e5-small = 384
EMBEDDING_DIM = get_settings().embedding_dim

# se debe usar from sqlalchemy.orm import deferred es para que no me arrastre la columna con SELECT * a menos que la pide explícitamente; pero su uso es en la consulta

class EmbeddingMixin(SQLModel):
    embedding: list[float] | None = Field(
        default=None,
        sa_type=Vector(EMBEDDING_DIM),
    )
    embedding_model: str | None = Field(default=None, max_length=255)
    embedded_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )