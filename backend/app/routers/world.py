from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import User, WorldPlace
from ..schemas.worldmap import WorldPlaceCreate, WorldPlaceRead, WorldPlaceUpdate
from ..services.worldmap import ensure_country_entry, sync_world_places
from .common import get_or_404, require_family, save_new, save_updates

router = APIRouter(tags=["world"])


def _ensure_family_owned(user: User, place: WorldPlace) -> None:
    if place.family_id != user.traveler.family_id:
        raise HTTPException(status_code=403, detail="Ese lugar pertenece a otra familia")


@router.get("/world-places", response_model=list[WorldPlaceRead])
def list_world_places(user: CurrentUser, db: Session = Depends(get_db)):
    family_id = user.traveler.family_id
    if family_id is None:
        # sin familia no hay diario: mapa vacío en vez de error
        return []
    sync_world_places(db, family_id)
    return db.scalars(
        select(WorldPlace)
        .where(WorldPlace.family_id == family_id, WorldPlace.hidden == False)  # noqa: E712
        .order_by(WorldPlace.name)
    ).all()


@router.post("/world-places", response_model=WorldPlaceRead, status_code=201)
def create_world_place(
    payload: WorldPlaceCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    family_id = require_family(user)
    data = payload.model_dump()
    data["family_id"] = family_id
    if data.get("country_code"):
        data["country_code"] = data["country_code"].upper()
    # una ciudad/sitio nuevo arrastra su país al diario (save_new hace commit)
    if data.get("kind") != "country":
        ensure_country_entry(db, family_id, data.get("country_code"))
    return save_new(db, WorldPlace(), data)


@router.patch("/world-places/{place_id}", response_model=WorldPlaceRead)
def update_world_place(
    place_id: int, payload: WorldPlaceUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    place = get_or_404(db, WorldPlace, place_id)
    _ensure_family_owned(user, place)
    data = payload.model_dump(exclude_unset=True)
    if data.get("country_code"):
        data["country_code"] = data["country_code"].upper()
    if data.get("kind", place.kind) != "country":
        ensure_country_entry(db, place.family_id, data.get("country_code"))
    return save_updates(db, place, data)


@router.delete("/world-places/{place_id}", status_code=204)
def delete_world_place(place_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    place = get_or_404(db, WorldPlace, place_id)
    _ensure_family_owned(user, place)
    if place.auto:
        # las derivadas de viajes se ocultan para que el sync no las reviva
        place.hidden = True
    else:
        db.delete(place)
    db.commit()
