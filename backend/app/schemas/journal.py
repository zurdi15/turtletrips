from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class DayJournalUpdate(BaseModel):
    text: str | None = None
    # encuadre de la postal (0-1); subir una foto nueva lo devuelve al centro
    photo_focus_x: float | None = Field(default=None, ge=0, le=1)
    photo_focus_y: float | None = Field(default=None, ge=0, le=1)


class DayJournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    day: date
    text: str | None
    photo_url: str | None  # propiedad calculada del modelo, NO photo_image (como cover_url)
    photo_focus_x: float
    photo_focus_y: float
