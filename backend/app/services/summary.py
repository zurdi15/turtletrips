from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Expense, Traveler, Trip
from ..schemas.misc import (
    CategoryTotal,
    CurrencyTotal,
    DayTotal,
    PayerTotal,
    TripSummary,
)


def trip_summary(db: Session, trip: Trip) -> TripSummary:
    base_filter = Expense.trip_id == trip.id

    total = db.scalar(select(func.coalesce(func.sum(Expense.amount_base), 0)).where(base_filter))
    count = db.scalar(select(func.count(Expense.id)).where(base_filter)) or 0

    by_category = [
        CategoryTotal(category=cat, total=float(t))
        for cat, t in db.execute(
            select(Expense.category, func.sum(Expense.amount_base))
            .where(base_filter).group_by(Expense.category)
            .order_by(func.sum(Expense.amount_base).desc())
        )
    ]
    by_day = [
        DayTotal(day=d, total=float(t))
        for d, t in db.execute(
            select(Expense.day, func.sum(Expense.amount_base))
            .where(base_filter).group_by(Expense.day).order_by(Expense.day)
        )
    ]
    by_payer = [
        PayerTotal(
            member_id=member_id,
            name=name if name is not None else "Sin asignar",
            total=float(t),
        )
        for member_id, name, t in db.execute(
            select(Traveler.id, Traveler.name, func.sum(Expense.amount_base))
            .select_from(Expense)
            .outerjoin(Traveler, Expense.paid_by_id == Traveler.id)
            .where(base_filter)
            .group_by(Traveler.id, Traveler.name)
            .order_by(func.sum(Expense.amount_base).desc())
        )
    ]
    by_currency = [
        CurrencyTotal(currency=c, amount=float(a))
        for c, a in db.execute(
            select(Expense.currency, func.sum(Expense.amount))
            .where(base_filter).group_by(Expense.currency)
        )
    ]

    total_f = float(total or 0)
    budget = float(trip.budget_amount) if trip.budget_amount is not None else None
    return TripSummary(
        base_currency=trip.base_currency,
        total_base=total_f,
        budget_amount=budget,
        remaining=(budget - total_f) if budget is not None else None,
        expense_count=count,
        by_category=by_category,
        by_day=by_day,
        by_payer=by_payer,
        by_currency=by_currency,
    )
