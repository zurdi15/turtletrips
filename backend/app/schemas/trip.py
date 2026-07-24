from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..models import TripStatus


class TravelerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = None


class TravelerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = None


class TravelerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str | None


def _validate_countries(codes: list[str]) -> list[str]:
    cleaned = []
    for code in codes:
        code = code.strip().upper()
        if len(code) != 2 or not code.isalpha():
            raise ValueError(f"Código de país inválido: {code!r}")
        if code not in cleaned:
            cleaned.append(code)
    return cleaned


class TripCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    countries: list[str] = []
    start_date: date | None = None
    end_date: date | None = None
    status_override: TripStatus | None = None
    base_currency: str = Field(default="EUR", min_length=3, max_length=3)
    budget_amount: Decimal | None = Field(default=None, ge=0)
    album_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    traveler_ids: list[int] = []

    @field_validator("countries")
    @classmethod
    def check_countries(cls, v: list[str]) -> list[str]:
        return _validate_countries(v)


class TripUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    countries: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    status_override: TripStatus | None = None
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    budget_amount: Decimal | None = Field(default=None, ge=0)
    album_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    traveler_ids: list[int] | None = None

    @field_validator("countries")
    @classmethod
    def check_countries(cls, v: list[str] | None) -> list[str] | None:
        return _validate_countries(v) if v is not None else None


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    countries: list[str]
    cover_url: str | None
    start_date: date | None
    end_date: date | None
    status: TripStatus
    status_override: TripStatus | None
    base_currency: str
    budget_amount: float | None
    album_url: str | None
    ics_token: str | None
    notes: str | None
    travelers: list[TravelerRead] = []
    # True si hay liquidaciones registradas y los saldos quedan a cero
    debts_settled: bool
    created_at: datetime
    updated_at: datetime
