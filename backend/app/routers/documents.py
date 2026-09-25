"""Documentos personales de la familia (DNI, pasaporte, carnet de conducir…).

No cuelgan de ningún viaje: se guardan por FAMILIA y los ve y gestiona toda
la familia, que es lo que hace falta para reservar (el pasaporte del crío lo
necesita quien compre los vuelos). No hay bypass de admin: el administrador de
la instancia no tiene por qué ver los papeles de otras familias.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Document, Traveler, User
from ..schemas.document import DocumentRead, DocumentUpdate
from ..services import files
from .common import clean_file_name, get_or_404, require_family

router = APIRouter(tags=["documents"])


def _ensure_family_traveler(db: Session, family_id: int, traveler_id: int) -> Traveler:
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler.family_id != family_id:
        raise HTTPException(status_code=403, detail="Ese viajero no es de tu familia")
    return traveler


def _owned(db: Session, user: User, document_id: int) -> Document:
    document = get_or_404(db, Document, document_id)
    if document.family_id != require_family(user):
        raise HTTPException(status_code=403, detail="Ese documento es de otra familia")
    return document


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(user: CurrentUser, db: Session = Depends(get_db)):
    family_id = require_family(user)
    return db.scalars(
        select(Document)
        .where(Document.family_id == family_id)
        .order_by(Document.traveler_id, Document.id.desc())
    ).all()


@router.post("/documents", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile,
    user: CurrentUser,
    traveler_id: int = Form(),
    db: Session = Depends(get_db),
):
    family_id = require_family(user)
    _ensure_family_traveler(db, family_id, traveler_id)
    try:
        stored_name, size = await files.save_document(family_id, file)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    document = Document(
        family_id=family_id,
        traveler_id=traveler_id,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.patch("/documents/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: int, payload: DocumentUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    document = _owned(db, user, document_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("original_name") is not None:
        document.original_name = clean_file_name(data["original_name"], document.original_name)
    if data.get("traveler_id") is not None:
        _ensure_family_traveler(db, document.family_id, data["traveler_id"])
        document.traveler_id = data["traveler_id"]
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents/{document_id}/download", include_in_schema=False)
def download_document(
    document_id: int, user: CurrentUser, inline: bool = False, db: Session = Depends(get_db)
):
    document = _owned(db, user, document_id)
    try:
        path = files.resolve_document(document.family_id, document.stored_name)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Fichero no encontrado") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichero no encontrado en disco")
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.original_name,
        content_disposition_type="inline" if inline else "attachment",
    )


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    document = _owned(db, user, document_id)
    files.delete_document(document.family_id, document.stored_name)
    db.delete(document)
    db.commit()
