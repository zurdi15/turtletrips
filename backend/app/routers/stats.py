from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Expense, Trip, WorldPlace, trip_travelers
from ..schemas.misc import YearStats
from ..services.stats import yearly_stats

router = APIRouter(tags=["stats"])


@router.get("/stats/yearly", response_model=list[YearStats])
def yearly(user: CurrentUser, db: Session = Depends(get_db)):
    """Resumen anual: viajes en los que participas (admin: todos) más las
    entradas del diario mundial de tu familia con fecha de visita (retroactivas)."""
    query = select(Trip)
    if not user.is_admin:
        query = query.join(trip_travelers).where(
            trip_travelers.c.traveler_id == user.traveler_id
        )
    trips = list(db.scalars(query).all())
    trip_ids = [trip.id for trip in trips]
    expenses = (
        list(db.scalars(select(Expense).where(Expense.trip_id.in_(trip_ids))).all())
        if trip_ids
        else []
    )

    world_countries: list[tuple[int, str]] = []
    family_id = user.traveler.family_id if user.traveler else None
    if family_id is not None:
        entries = db.scalars(
            select(WorldPlace).where(
                WorldPlace.family_id == family_id,
                WorldPlace.hidden.is_(False),
                WorldPlace.visited_year.is_not(None),
                WorldPlace.country_code.is_not(None),
            )
        ).all()
        world_countries = [(e.visited_year, e.country_code) for e in entries]

    return yearly_stats(trips, expenses, world_countries)
