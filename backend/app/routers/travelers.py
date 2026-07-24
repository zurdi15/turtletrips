from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Traveler
from ..schemas.trip import TravelerCreate, TravelerRead, TravelerUpdate
from .common import apply_updates, get_or_404

router = APIRouter(tags=["travelers"])


def _find_by_name(db: Session, name: str) -> Traveler | None:
    return db.scalar(
        select(Traveler).where(func.lower(Traveler.name) == name.strip().lower())
    )


@router.get("/travelers", response_model=list[TravelerRead])
def list_travelers(db: Session = Depends(get_db)):
    return db.scalars(select(Traveler).order_by(Traveler.name)).all()


@router.post("/travelers", response_model=TravelerRead, status_code=201)
def create_traveler(payload: TravelerCreate, db: Session = Depends(get_db)):
    existing = _find_by_name(db, payload.name)
    if existing:
        return existing
    traveler = Traveler(name=payload.name.strip(), color=payload.color)
    db.add(traveler)
    db.commit()
    db.refresh(traveler)
    return traveler


@router.patch("/travelers/{traveler_id}", response_model=TravelerRead)
def update_traveler(traveler_id: int, payload: TravelerUpdate, db: Session = Depends(get_db)):
    traveler = get_or_404(db, Traveler, traveler_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        duplicate = _find_by_name(db, data["name"])
        if duplicate and duplicate.id != traveler_id:
            raise HTTPException(status_code=409, detail="Ya existe un viajero con ese nombre")
        data["name"] = data["name"].strip()
    apply_updates(traveler, data)
    db.commit()
    db.refresh(traveler)
    return traveler


@router.delete("/travelers/{traveler_id}", status_code=204)
def delete_traveler(traveler_id: int, db: Session = Depends(get_db)):
    traveler = get_or_404(db, Traveler, traveler_id)
    db.delete(traveler)
    db.commit()
