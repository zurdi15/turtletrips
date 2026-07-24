from datetime import date

from pydantic import BaseModel


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
