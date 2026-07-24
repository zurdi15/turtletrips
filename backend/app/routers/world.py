from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import WorldPlace
from ..schemas.worldmap import WorldPlaceCreate, WorldPlaceRead, WorldPlaceUpdate
from ..services.worldmap import ensure_country_entry, sync_world_places
from .common import get_or_404, save_new, save_updates

router = APIRouter(tags=["world"])


@router.get("/world-places", response_model=list[WorldPlaceRead])
def list_world_places(db: Session = Depends(get_db)):
    sync_world_places(db)
    return db.scalars(
        select(WorldPlace).where(WorldPlace.hidden == False).order_by(WorldPlace.name)  # noqa: E712
    ).all()


@router.post("/world-places", response_model=WorldPlaceRead, status_code=201)
def create_world_place(payload: WorldPlaceCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if data.get("country_code"):
        data["country_code"] = data["country_code"].upper()
    # una ciudad/sitio nuevo arrastra su país al diario (save_new hace commit)
    if data.get("kind") != "country":
        ensure_country_entry(db, data.get("country_code"))
    return save_new(db, WorldPlace(), data)


@router.patch("/world-places/{place_id}", response_model=WorldPlaceRead)
def update_world_place(place_id: int, payload: WorldPlaceUpdate, db: Session = Depends(get_db)):
    place = get_or_404(db, WorldPlace, place_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("country_code"):
        data["country_code"] = data["country_code"].upper()
    if data.get("kind", place.kind) != "country":
        ensure_country_entry(db, data.get("country_code"))
    return save_updates(db, place, data)


@router.delete("/world-places/{place_id}", status_code=204)
def delete_world_place(place_id: int, db: Session = Depends(get_db)):
    place = get_or_404(db, WorldPlace, place_id)
    if place.auto:
        # las derivadas de viajes se ocultan para que el sync no las reviva
        place.hidden = True
    else:
        db.delete(place)
    db.commit()
