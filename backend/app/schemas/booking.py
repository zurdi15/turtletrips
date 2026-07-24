from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..models import BookingType


class BookingBase(BaseModel):
    """Campos opcionales comunes a Create y Update."""

    provider: str | None = None
    confirmation_code: str | None = None
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


class CreateExpenseFromBooking(BaseModel):
    exchange_rate: Decimal | None = Field(default=None, gt=0)
