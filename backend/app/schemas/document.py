from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    traveler_id: int
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class DocumentUpdate(BaseModel):
    """Renombrar (o mover a otro viajero de la familia) un documento."""

    original_name: str | None = Field(default=None, min_length=1, max_length=300)
    traveler_id: int | None = None
