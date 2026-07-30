from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..models import BookingType

MAX_SEGMENTS = 20


class BookingSegmentInput(BaseModel):
    """Tramo de un transporte (vuelo con escalas, ida y vuelta)."""

    origin: str | None = Field(default=None, max_length=200)
    destination: str | None = Field(default=None, max_length=200)
    departure_dt: datetime | None = None
    arrival_dt: datetime | None = None
    flight_number: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def _arrival_after_departure(self) -> "BookingSegmentInput":
        if (
            self.departure_dt is not None
            and self.arrival_dt is not None
            and self.arrival_dt < self.departure_dt
        ):
            raise ValueError("La llegada del tramo es anterior a su salida")
        return self

    def is_empty(self) -> bool:
        return not any(
            (
                self.origin,
                self.destination,
                self.departure_dt,
                self.arrival_dt,
                self.flight_number,
            )
        )


class BookingSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    origin: str | None
    destination: str | None
    departure_dt: datetime | None
    arrival_dt: datetime | None
    flight_number: str | None


class BookingBase(BaseModel):
    """Campos opcionales comunes a Create y Update."""

    provider: str | None = None
    confirmation_code: str | None = None
    flight_number: str | None = Field(default=None, max_length=20)
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    origin: str | None = None
    destination: str | None = None
    address: str | None = None
    lat: float | None = None
    lon: float | None = None
    cost_amount: Decimal | None = Field(default=None, ge=0)
    cost_currency: str | None = Field(default=None, min_length=3, max_length=3)
    notes: str | None = None
    paid_by_id: int | None = None
    paid_by_common: bool = False
    # ausente = no tocar; [] = sin tramos; lista = REEMPLAZA el conjunto entero
    segments: list[BookingSegmentInput] | None = Field(default=None, max_length=MAX_SEGMENTS)

    @field_validator("segments")
    @classmethod
    def _drop_empty_segments(
        cls, v: list[BookingSegmentInput] | None
    ) -> list[BookingSegmentInput] | None:
        if v is None:
            return None
        return [s for s in v if not s.is_empty()]


class BookingCreate(BookingBase):
    type: BookingType = BookingType.other
    title: str = Field(min_length=1, max_length=300)


class BookingUpdate(BookingBase):
    type: BookingType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    type: BookingType
    title: str
    provider: str | None
    confirmation_code: str | None
    flight_number: str | None
    start_dt: datetime | None
    end_dt: datetime | None
    origin: str | None
    destination: str | None
    address: str | None
    lat: float | None
    lon: float | None
    cost_amount: float | None
    cost_currency: str | None
    notes: str | None
    place_id: int | None
    paid_by_id: int | None
    paid_by_common: bool
    segments: list[BookingSegmentRead] = []


class CreateExpenseFromBooking(BaseModel):
    exchange_rate: Decimal | None = Field(default=None, gt=0)
