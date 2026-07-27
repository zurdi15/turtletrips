from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import ChecklistItem
from ..schemas.checklist import (
    ChecklistItemCreate,
    ChecklistItemRead,
    ChecklistItemUpdate,
)
from .common import (
    delete_trip_scoped,
    ensure_trip_member,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["checklist"])


@router.get("/trips/{trip_id}/checklist", response_model=list[ChecklistItemRead])
def list_checklist(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    return db.scalars(
        select(ChecklistItem)
        .where(ChecklistItem.trip_id == trip_id)
        .order_by(ChecklistItem.id)
    ).all()


@router.post("/trips/{trip_id}/checklist", response_model=ChecklistItemRead, status_code=201)
def create_checklist_item(
    trip_id: int, payload: ChecklistItemCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    return save_new(db, ChecklistItem(trip_id=trip_id), payload.model_dump())


@router.patch("/checklist-items/{item_id}", response_model=ChecklistItemRead)
def update_checklist_item(
    item_id: int, payload: ChecklistItemUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    item = get_trip_scoped(db, user, ChecklistItem, item_id)
    return save_updates(db, item, payload.model_dump(exclude_unset=True))


@router.delete("/checklist-items/{item_id}", status_code=204)
def delete_checklist_item(item_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    delete_trip_scoped(db, user, ChecklistItem, item_id)
