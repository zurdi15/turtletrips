from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..models import SplitMode


class ExpenseShareInput(BaseModel):
    traveler_id: int
    # None en modo equal (solo participación); importe o porcentaje en los demás
    value: Decimal | None = Field(default=None, ge=0)


class ExpenseShareRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    traveler_id: int
    value: float | None


class ExpenseBase(BaseModel):
    """Campos opcionales comunes a Create y Update."""

    currency: str | None = Field(default=None, min_length=3, max_length=3)
    exchange_rate: Decimal | None = Field(default=None, gt=0)
    paid_by_id: int | None = None
    # pagado del fondo común (excluyente con paid_by_id; el router lo garantiza)
    paid_by_common: bool = False
    booking_id: int | None = None
    place_id: int | None = None
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    day: date
    category: str = Field(default="Otros", min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=300)
    amount: Decimal = Field(gt=0)
    split_mode: SplitMode = SplitMode.equal
    shares: list[ExpenseShareInput] = []


class ExpenseUpdate(ExpenseBase):
    day: date | None = None
    category: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=300)
    amount: Decimal | None = Field(default=None, gt=0)
    split_mode: SplitMode | None = None
    # None = no tocar; [] + equal = volver al reparto implícito entre todos
    shares: list[ExpenseShareInput] | None = None


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
    paid_by_common: bool
    split_mode: str
    shares: list[ExpenseShareRead]
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
