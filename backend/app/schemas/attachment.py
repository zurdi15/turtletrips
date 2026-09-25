from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    booking_id: int | None
    expense_id: int | None
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class AttachmentUpdate(BaseModel):
    """Renombrar un fichero subido: solo cambia el nombre que se enseña y con
    el que se descarga; el fichero en disco (`stored_name`) no se toca."""

    original_name: str = Field(min_length=1, max_length=300)
