from pydantic import BaseModel, ConfigDict, Field


class WorldPlaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: str = Field(default="place", pattern="^(country|city|place)$")
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    lat: float | None = None
    lon: float | None = None
    note: str | None = None
    visited_year: int | None = Field(default=None, ge=1900, le=2100)
    visited_month: int | None = Field(default=None, ge=1, le=12)


class WorldPlaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    kind: str | None = Field(default=None, pattern="^(country|city|place)$")
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    lat: float | None = None
    lon: float | None = None
    note: str | None = None
    visited_year: int | None = Field(default=None, ge=1900, le=2100)
    visited_month: int | None = Field(default=None, ge=1, le=12)


class WorldPlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    country_code: str | None
    lat: float | None
    lon: float | None
    note: str | None
    visited_year: int | None
    visited_month: int | None
    photo_url: str | None
    auto: bool
    origin: str | None
