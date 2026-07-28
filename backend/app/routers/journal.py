from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import DayJournal, User
from ..schemas.journal import DayJournalRead, DayJournalUpdate
from ..services import files
from .common import ensure_trip_member

router = APIRouter(tags=["journal"])


def _get_or_create(db: Session, user: User, trip_id: int, day: date) -> DayJournal:
    """Fila de diario de (trip_id, day), creándola si no existe."""
    ensure_trip_member(db, user, trip_id)
    entry = db.scalar(
        select(DayJournal).where(
            DayJournal.trip_id == trip_id, DayJournal.day == day
        )
    )
    if entry is None:
        entry = DayJournal(trip_id=trip_id, day=day)
        db.add(entry)
    return entry


@router.get("/trips/{trip_id}/journal", response_model=list[DayJournalRead])
def list_journal(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    return db.scalars(
        select(DayJournal)
        .where(DayJournal.trip_id == trip_id)
        .order_by(DayJournal.day)
    ).all()


@router.put("/trips/{trip_id}/journal/{day}", response_model=DayJournalRead)
def upsert_journal(
    trip_id: int,
    day: date,
    payload: DayJournalUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    entry = _get_or_create(db, user, trip_id, day)
    entry.text = payload.text
    # el encuadre solo se toca si viene: guardar el texto no debe recentrar la foto
    if payload.photo_focus_x is not None:
        entry.photo_focus_x = payload.photo_focus_x
    if payload.photo_focus_y is not None:
        entry.photo_focus_y = payload.photo_focus_y
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/trips/{trip_id}/journal/{day}/photo", response_model=DayJournalRead)
async def upload_photo(
    trip_id: int, day: date, file: UploadFile, user: CurrentUser, db: Session = Depends(get_db)
):
    entry = _get_or_create(db, user, trip_id, day)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="La postal debe ser una imagen")
    try:
        stored_name, _size = await files.save_upload(trip_id, file)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    if entry.photo_image:
        files.delete_stored_file(trip_id, entry.photo_image)
    entry.photo_image = stored_name
    # el encuadre anterior no vale para otra foto: vuelve al centro
    entry.photo_focus_x = 0.5
    entry.photo_focus_y = 0.5
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/trips/{trip_id}/journal/{day}/photo", include_in_schema=False)
def get_photo(trip_id: int, day: date, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    entry = db.scalar(
        select(DayJournal).where(
            DayJournal.trip_id == trip_id, DayJournal.day == day
        )
    )
    if entry is None or not entry.photo_image:
        raise HTTPException(status_code=404, detail="Sin postal")
    try:
        path = files.resolve_stored_file(trip_id, entry.photo_image)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Sin postal") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sin postal")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.delete("/trips/{trip_id}/journal/{day}/photo", response_model=DayJournalRead)
def delete_photo(trip_id: int, day: date, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    entry = db.scalar(
        select(DayJournal).where(
            DayJournal.trip_id == trip_id, DayJournal.day == day
        )
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Sin postal")
    if entry.photo_image:
        files.delete_stored_file(trip_id, entry.photo_image)
        entry.photo_image = None
        db.commit()
        db.refresh(entry)
    return entry
