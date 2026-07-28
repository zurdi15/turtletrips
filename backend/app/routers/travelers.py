from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Family, Traveler, User
from ..schemas.trip import TravelerCreate, TravelerRead, TravelerUpdate
from ..services import files
from .common import get_or_404, save_updates

router = APIRouter(tags=["travelers"])


def _find_by_name(db: Session, name: str) -> Traveler | None:
    return db.scalar(
        select(Traveler).where(func.lower(Traveler.name) == name.strip().lower())
    )


def _ensure_can_edit(user: User, traveler: Traveler) -> None:
    """Editable: el viajero propio o cualquier virtual; los de otros users, solo admin."""
    if user.is_admin or traveler.id == user.traveler_id or traveler.user is None:
        return
    raise HTTPException(
        status_code=403, detail="Ese viajero pertenece a otra cuenta de usuario"
    )


@router.get("/travelers", response_model=list[TravelerRead])
def list_travelers(db: Session = Depends(get_db)):
    return db.scalars(select(Traveler).order_by(Traveler.name)).all()


@router.post("/travelers", response_model=TravelerRead, status_code=201)
def create_traveler(payload: TravelerCreate, user: CurrentUser, db: Session = Depends(get_db)):
    existing = _find_by_name(db, payload.name)
    if existing:
        return existing
    data = payload.model_dump(exclude_unset=True)
    if "family_id" in data:
        # familia explícita del formulario: un no-admin solo la suya o ninguna
        family_id = data["family_id"]
        if family_id is not None:
            get_or_404(db, Family, family_id)
            if not user.is_admin and family_id != user.traveler.family_id:
                raise HTTPException(
                    status_code=403,
                    detail="Solo el administrador puede asignar otras familias",
                )
    else:
        # sin campo, entra en la familia del creador (alta rápida del TripForm)
        family_id = user.traveler.family_id
    traveler = Traveler(
        name=payload.name.strip(), color=payload.color, family_id=family_id
    )
    db.add(traveler)
    db.commit()
    db.refresh(traveler)
    return traveler


@router.patch("/travelers/{traveler_id}", response_model=TravelerRead)
def update_traveler(
    traveler_id: int, payload: TravelerUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    traveler = get_or_404(db, Traveler, traveler_id)
    _ensure_can_edit(user, traveler)
    data = payload.model_dump(exclude_unset=True)
    if "family_id" in data:
        if not user.is_admin:
            raise HTTPException(
                status_code=403, detail="Solo el administrador puede cambiar la familia"
            )
        if data["family_id"] is not None:
            get_or_404(db, Family, data["family_id"])
    if "name" in data:
        duplicate = _find_by_name(db, data["name"])
        if duplicate and duplicate.id != traveler_id:
            raise HTTPException(status_code=409, detail="Ya existe un viajero con ese nombre")
        data["name"] = data["name"].strip()
    return save_updates(db, traveler, data)


@router.delete("/travelers/{traveler_id}", status_code=204)
def delete_traveler(traveler_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler.user is not None:
        raise HTTPException(
            status_code=409,
            detail="Este viajero tiene una cuenta de usuario; borra antes la cuenta",
        )
    if traveler.avatar_image:
        files.delete_avatar(traveler.avatar_image)
    db.delete(traveler)
    db.commit()


# --- avatar (foto de perfil del viajero, con o sin cuenta) ---


@router.post("/travelers/{traveler_id}/avatar", response_model=TravelerRead)
async def upload_avatar(
    traveler_id: int, file: UploadFile, user: CurrentUser, db: Session = Depends(get_db)
):
    traveler = get_or_404(db, Traveler, traveler_id)
    _ensure_can_edit(user, traveler)
    try:
        stored_name = await files.save_avatar(file)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    if traveler.avatar_image:
        files.delete_avatar(traveler.avatar_image)
    traveler.avatar_image = stored_name
    # el encuadre anterior no vale para otra foto: vuelve al centro
    traveler.avatar_focus_x = 0.5
    traveler.avatar_focus_y = 0.5
    db.commit()
    db.refresh(traveler)
    return traveler


@router.get("/travelers/{traveler_id}/avatar", include_in_schema=False)
def get_avatar(traveler_id: int, db: Session = Depends(get_db)):
    traveler = get_or_404(db, Traveler, traveler_id)
    if not traveler.avatar_image:
        raise HTTPException(status_code=404, detail="Sin avatar")
    try:
        path = files.resolve_avatar(traveler.avatar_image)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Sin avatar") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sin avatar")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.delete("/travelers/{traveler_id}/avatar", response_model=TravelerRead)
def delete_avatar(traveler_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    traveler = get_or_404(db, Traveler, traveler_id)
    _ensure_can_edit(user, traveler)
    if traveler.avatar_image:
        files.delete_avatar(traveler.avatar_image)
        traveler.avatar_image = None
        db.commit()
        db.refresh(traveler)
    return traveler
