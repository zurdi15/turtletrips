from datetime import date

from pydantic import BaseModel, ConfigDict


class DayJournalUpdate(BaseModel):
    text: str | None = None


class DayJournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    day: date
    text: str | None
    photo_url: str | None  # propiedad calculada del modelo, NO photo_image (como cover_url)
