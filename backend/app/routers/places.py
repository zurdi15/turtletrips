from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Place, PlaceCategory, Trip
from ..schemas.place import PlaceCreate, PlaceRead, PlaceUpdate
from .common import delete_by_id, get_or_404, save_new, save_updates

router = APIRouter(tags=["places"])


@router.get("/trips/{trip_id}/places", response_model=list[PlaceRead])
def list_places(
    trip_id: int,
    visited: bool | None = None,
    category: PlaceCategory | None = None,
    db: Session = Depends(get_db),
):
    get_or_404(db, Trip, trip_id)
    query = select(Place).where(Place.trip_id == trip_id)
    if visited is not None:
        query = query.where(Place.visited == visited)
    if category is not None:
        query = query.where(Place.category == category.value)
    return db.scalars(query.order_by(Place.priority.desc(), Place.name)).all()


@router.post("/trips/{trip_id}/places", response_model=PlaceRead, status_code=201)
def create_place(trip_id: int, payload: PlaceCreate, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    return save_new(db, Place(trip_id=trip_id), payload.model_dump())


@router.patch("/places/{place_id}", response_model=PlaceRead)
def update_place(place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    place = get_or_404(db, Place, place_id)
    return save_updates(db, place, payload.model_dump(exclude_unset=True))


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, Place, place_id)
