from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class ItineraryItemCreate(BaseModel):
    day: date
    end_day: date | None = None  # para estancias de varios días
    start_time: time | None = None
    end_time: time | None = None
    order_index: int = 0
    title: str = Field(min_length=1, max_length=300)
    notes: str | None = None
    place_id: int | None = None
    booking_id: int | None = None


class ItineraryItemUpdate(BaseModel):
    day: date | None = None
    end_day: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    order_index: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    notes: str | None = None
    place_id: int | None = None
    booking_id: int | None = None


class ItineraryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    day: date
    end_day: date | None
    start_time: time | None
    end_time: time | None
    order_index: int
    title: str
    notes: str | None
    place_id: int | None
    booking_id: int | None


class ReorderEntry(BaseModel):
    id: int
    day: date
    order_index: int


class ReorderRequest(BaseModel):
    items: list[ReorderEntry]
