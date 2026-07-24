import unicodedata
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Expense, Place, Trip
from ..schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate, ImportResult
from ..services import csv_io
from ..services.rates import RateUnavailableError, get_rate
from .common import apply_updates, get_or_404

router = APIRouter(tags=["expenses"])

TWO_PLACES = Decimal("0.01")


def _validate_place(db: Session, trip_id: int, place_id: int | None) -> None:
    if place_id is None:
        return
    place = db.get(Place, place_id)
    if place is None or place.trip_id != trip_id:
        raise HTTPException(status_code=400, detail="El sitio no pertenece a este viaje")


async def resolve_rate(
    db: Session, base_currency: str, currency: str, day: date, provided: Decimal | None
) -> Decimal:
    if provided is not None:
        return provided
    try:
        rate, _ = await get_rate(db, currency, base_currency, day)
    except RateUnavailableError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No hay tipo de cambio {currency}->{base_currency} disponible; "
            "indícalo manualmente en exchange_rate",
        ) from exc
    return rate


@router.get("/trips/{trip_id}/expenses", response_model=list[ExpenseRead])
def list_expenses(
    trip_id: int,
    category: str | None = None,
    day: date | None = None,
    paid_by_id: int | None = None,
    db: Session = Depends(get_db),
):
    get_or_404(db, Trip, trip_id)
    query = select(Expense).where(Expense.trip_id == trip_id)
    if category is not None:
        query = query.where(Expense.category == category)
    if day is not None:
        query = query.where(Expense.day == day)
    if paid_by_id is not None:
        query = query.where(Expense.paid_by_id == paid_by_id)
    return db.scalars(query.order_by(Expense.day.desc(), Expense.id.desc())).all()


@router.post("/trips/{trip_id}/expenses", response_model=ExpenseRead, status_code=201)
async def create_expense(trip_id: int, payload: ExpenseCreate, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    _validate_place(db, trip_id, payload.place_id)
    currency = (payload.currency or trip.base_currency).upper()
    rate = await resolve_rate(db, trip.base_currency, currency, payload.day, payload.exchange_rate)

    expense = Expense(trip_id=trip_id)
    data = payload.model_dump(exclude={"currency", "exchange_rate"})
    apply_updates(expense, data)
    expense.currency = currency
    expense.exchange_rate = rate
    expense.amount_base = (payload.amount * rate).quantize(TWO_PLACES)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.patch("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db)):
    expense = get_or_404(db, Expense, expense_id)
    trip = db.get(Trip, expense.trip_id)
    data = payload.model_dump(exclude_unset=True)
    if "place_id" in data:
        _validate_place(db, expense.trip_id, data["place_id"])

    currency_changed = "currency" in data and data["currency"].upper() != expense.currency
    if currency_changed and "exchange_rate" not in data:
        data["exchange_rate"] = await resolve_rate(
            db,
            trip.base_currency,
            data["currency"].upper(),
            data.get("day", expense.day),
            None,
        )
    if "currency" in data:
        data["currency"] = data["currency"].upper()
    apply_updates(expense, data)
    expense.amount_base = (
        Decimal(str(expense.amount)) * Decimal(str(expense.exchange_rate))
    ).quantize(TWO_PLACES)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = get_or_404(db, Expense, expense_id)
    db.delete(expense)
    db.commit()


@router.get("/trips/{trip_id}/expenses/export.csv")
def export_expenses(trip_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    content = csv_io.export_csv(db, trip)
    # los headers HTTP solo admiten ASCII
    safe_name = (
        unicodedata.normalize("NFKD", trip.name)
        .encode("ascii", "ignore")
        .decode()
        .replace(" ", "_")[:50]
        or "viaje"
    )
    filename = f"gastos-{safe_name}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/trips/{trip_id}/expenses/import", response_model=ImportResult)
async def import_expenses(
    trip_id: int,
    file: UploadFile,
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    trip = get_or_404(db, Trip, trip_id)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV demasiado grande (máx 5 MB)")
    return csv_io.import_csv(db, trip, content, dry_run=dry_run)
