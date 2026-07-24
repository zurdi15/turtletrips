from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float


class RateRead(BaseModel):
    base: str
    quote: str
    day: date
    rate: float
    source: str  # "cache" | "api" | "identity"


class CategoryTotal(BaseModel):
    category: str
    total: float


class DayTotal(BaseModel):
    day: date
    total: float


class PayerTotal(BaseModel):
    member_id: int | None
    name: str
    total: float


class CurrencyTotal(BaseModel):
    currency: str
    amount: float


class TripSummary(BaseModel):
    base_currency: str
    total_base: float
    budget_amount: float | None
    remaining: float | None
    expense_count: int
    by_category: list[CategoryTotal]
    by_day: list[DayTotal]
    by_payer: list[PayerTotal]
    by_currency: list[CurrencyTotal]


class TravelerBalance(BaseModel):
    traveler_id: int
    name: str
    color: str | None
    paid_base: float
    owed_base: float
    net_base: float  # paid - owed; >0 le deben, <0 debe


class SettlementTransfer(BaseModel):
    from_id: int
    from_name: str
    to_id: int
    to_name: str
    amount_base: float


class SettlementCreate(BaseModel):
    from_id: int
    to_id: int
    amount_base: Decimal = Field(gt=0)


class PaidSettlement(BaseModel):
    id: int
    from_id: int
    from_name: str
    to_id: int
    to_name: str
    amount_base: float
    created_at: datetime


class TripBalances(BaseModel):
    base_currency: str
    balances: list[TravelerBalance]
    settlements: list[SettlementTransfer]
    # pagos ya registrados y si con ellos las deudas quedan saldadas
    paid_settlements: list[PaidSettlement]
    debts_settled: bool
    # gastos sin pagador: fuera del cálculo, se avisa en la UI
    unassigned_count: int
    unassigned_total_base: float
    # gastos del fondo común: fuera del cálculo por diseño (info, no aviso)
    common_count: int
    common_total_base: float
