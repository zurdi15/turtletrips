from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Attachment, Booking, Trip
from ..schemas.attachment import AttachmentRead
from ..services import files
from .common import ensure_in_trip, get_or_404

router = APIRouter(tags=["attachments"])


@router.get("/trips/{trip_id}/attachments", response_model=list[AttachmentRead])
def list_attachments(
    trip_id: int, booking_id: int | None = None, db: Session = Depends(get_db)
):
    get_or_404(db, Trip, trip_id)
    query = select(Attachment).where(Attachment.trip_id == trip_id)
    if booking_id is not None:
        query = query.where(Attachment.booking_id == booking_id)
    return db.scalars(query.order_by(Attachment.id.desc())).all()


@router.post("/trips/{trip_id}/attachments", response_model=AttachmentRead, status_code=201)
async def upload_attachment(
    trip_id: int,
    file: UploadFile,
    booking_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    get_or_404(db, Trip, trip_id)
    ensure_in_trip(
        db, Booking, booking_id, trip_id, message="La reserva no pertenece a este viaje"
    )

    try:
        stored_name, size = await files.save_upload(trip_id, file)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    attachment = Attachment(
        trip_id=trip_id,
        booking_id=booking_id,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int, inline: bool = False, db: Session = Depends(get_db)
):
    attachment = get_or_404(db, Attachment, attachment_id)
    try:
        path = files.resolve_stored_file(attachment.trip_id, attachment.stored_name)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Fichero no encontrado") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichero no encontrado en disco")
    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.original_name,
        content_disposition_type="inline" if inline else "attachment",
    )


@router.delete("/attachments/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    attachment = get_or_404(db, Attachment, attachment_id)
    files.delete_stored_file(attachment.trip_id, attachment.stored_name)
    db.delete(attachment)
    db.commit()
