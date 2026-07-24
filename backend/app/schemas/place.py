from pydantic import BaseModel, ConfigDict, Field

from ..models import PlaceCategory


class PlaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: PlaceCategory = PlaceCategory.other
    notes: str | None = None
    url: str | None = None
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    visited: bool = False
    priority: int = Field(default=0, ge=0, le=1)


class PlaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: PlaceCategory | None = None
    notes: str | None = None
    url: str | None = None
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    visited: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=1)


class PlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    name: str
    category: PlaceCategory
    notes: str | None
    url: str | None
    address: str | None
    lat: float | None
    lon: float | None
    visited: bool
    priority: int
