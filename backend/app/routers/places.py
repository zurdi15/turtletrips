from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Place, PlaceCategory
from ..schemas.place import PlaceCreate, PlaceRead, PlaceUpdate
from .common import (
    delete_trip_scoped,
    ensure_trip_member,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["places"])


@router.get("/trips/{trip_id}/places", response_model=list[PlaceRead])
def list_places(
    trip_id: int,
    user: CurrentUser,
    visited: bool | None = None,
    category: PlaceCategory | None = None,
    db: Session = Depends(get_db),
):
    ensure_trip_member(db, user, trip_id)
    query = select(Place).where(Place.trip_id == trip_id)
    if visited is not None:
        query = query.where(Place.visited == visited)
    if category is not None:
        query = query.where(Place.category == category.value)
    return db.scalars(query.order_by(Place.priority.desc(), Place.name)).all()


@router.post("/trips/{trip_id}/places", response_model=PlaceRead, status_code=201)
def create_place(
    trip_id: int, payload: PlaceCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    return save_new(db, Place(trip_id=trip_id), payload.model_dump())


@router.patch("/places/{place_id}", response_model=PlaceRead)
def update_place(
    place_id: int, payload: PlaceUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    place = get_trip_scoped(db, user, Place, place_id)
    return save_updates(db, place, payload.model_dump(exclude_unset=True))


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    delete_trip_scoped(db, user, Place, place_id)
