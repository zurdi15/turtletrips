from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExpenseCreate(BaseModel):
    day: date
    category: str = Field(default="Otros", min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=300)
    amount: Decimal = Field(gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    paid_by_id: int | None = None
    booking_id: int | None = None
    place_id: int | None = None
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    day: date | None = None
    category: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=300)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    paid_by_id: int | None = None
    booking_id: int | None = None
    place_id: int | None = None
    notes: str | None = None


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    booking_id: int | None
    place_id: int | None
    day: date
    category: str
    description: str
    amount: float
    currency: str
    exchange_rate: float
    amount_base: float
    paid_by_id: int | None
    notes: str | None


class ImportRowError(BaseModel):
    row: int
    error: str


class ImportPreviewRow(BaseModel):
    row: int
    day: date
    category: str
    description: str
    amount: float
    currency: str
    exchange_rate: float
    amount_base: float
    paid_by: str | None
    place: str | None = None
    notes: str | None = None


class ImportResult(BaseModel):
    dry_run: bool
    valid_rows: list[ImportPreviewRow]
    errors: list[ImportRowError]
    imported: int
