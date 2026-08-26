from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Column
from sqlalchemy.orm import deferred
from sqlmodel import Field, SQLModel
from pgvector.sqlalchemy import Vector

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
EMBEDDING_DIM = 768

class EmbeddingMixin(SQLModel):
    embedding: Optional[list[float]] = Field(
        default=None,
        sa_column=deferred(Column(Vector(EMBEDDING_DIM), nullable=True)), #deferred es para que no me arrastre la columna con SELECT * a menos que la pide explícitamente
    )
    embedding_model: Optional[str] = Field(default=None, max_length=255)
    embedded_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))