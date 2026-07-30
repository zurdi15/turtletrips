"""Familias: lectura para cualquier usuario, mutaciones solo admin.

El GET es legible por todos (el front muestra nombres de familia en viajeros);
por eso este router va en el bloque autenticado normal y las mutaciones llevan
el candado de admin por endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import AdminUser, CurrentUser
from ..db import get_db
from ..models import BagEditRevoke, Family, Traveler, Trip
from ..schemas.admin import FamilyCreate, FamilyReorder, FamilyUpdate
from ..schemas.auth import FamilyRead
from ..schemas.packing import BagPermissionsRead, BagPermissionUpdate
from ..services.categories import ensure_default_categories
from .common import get_or_404

router = APIRouter(tags=["families"])


def _find_by_name(db: Session, name: str) -> Family | None:
    return db.scalar(
        select(Family).where(func.lower(Family.name) == name.strip().lower())
    )


@router.get("/families", response_model=list[FamilyRead])
def list_families(db: Session = Depends(get_db)):
    return db.scalars(select(Family).order_by(Family.position, Family.id)).all()


@router.post("/families", response_model=FamilyRead, status_code=201)
def create_family(payload: FamilyCreate, _admin: AdminUser, db: Session = Depends(get_db)):
    if _find_by_name(db, payload.name):
        raise HTTPException(status_code=409, detail="Ya existe una familia con ese nombre")
    max_pos = db.scalar(select(func.coalesce(func.max(Family.position), -1)))
    family = Family(name=payload.name.strip(), position=max_pos + 1)
    db.add(family)
    db.commit()
    db.refresh(family)
    ensure_default_categories(db, family.id)
    return family


@router.post("/families/reorder", status_code=204)
def reorder_families(payload: FamilyReorder, _admin: AdminUser, db: Session = Depends(get_db)):
    """Fija el orden manual: la posición es el índice en la lista recibida."""
    families = {f.id: f for f in db.scalars(select(Family))}
    for position, family_id in enumerate(payload.ids):
        family = families.get(family_id)
        if family is not None:
            family.position = position
    db.commit()


@router.patch("/families/{family_id}", response_model=FamilyRead)
def rename_family(
    family_id: int, payload: FamilyUpdate, _admin: AdminUser, db: Session = Depends(get_db)
):
    family = get_or_404(db, Family, family_id)
    duplicate = _find_by_name(db, payload.name)
    if duplicate and duplicate.id != family_id:
        raise HTTPException(status_code=409, detail="Ya existe una familia con ese nombre")
    family.name = payload.name.strip()
    db.commit()
    db.refresh(family)
    return family


@router.delete("/families/{family_id}", status_code=204)
def delete_family(family_id: int, _admin: AdminUser, db: Session = Depends(get_db)):
    """Solo se puede borrar vacía; su config (categorías/plantillas/mapa) cae en cascada."""
    family = get_or_404(db, Family, family_id)
    has_travelers = db.scalar(
        select(Traveler.id).where(Traveler.family_id == family_id).limit(1)
    )
    if has_travelers is not None:
        raise HTTPException(status_code=409, detail="La familia tiene viajeros asignados")
    has_trips = db.scalar(select(Trip.id).where(Trip.family_id == family_id).limit(1))
    if has_trips is not None:
        raise HTTPException(status_code=409, detail="La familia tiene viajes asociados")
    db.delete(family)
    db.commit()


# --- permisos de maletas (página Familia) ---
# Por defecto toda tu familia gestiona tus maletas; aquí cada usuario revoca
# (o devuelve) ese permiso miembro a miembro. Solo el dueño toca sus filas.


@router.get("/family/bag-permissions", response_model=BagPermissionsRead)
def my_bag_permissions(user: CurrentUser, db: Session = Depends(get_db)):
    revoked = db.scalars(
        select(BagEditRevoke.editor_traveler_id).where(
            BagEditRevoke.owner_traveler_id == user.traveler_id
        )
    ).all()
    restricted_by = db.scalars(
        select(BagEditRevoke.owner_traveler_id).where(
            BagEditRevoke.editor_traveler_id == user.traveler_id
        )
    ).all()
    return BagPermissionsRead(revoked=list(revoked), restricted_by=list(restricted_by))


@router.put("/family/bag-permissions/{traveler_id}", status_code=204)
def set_bag_permission(
    traveler_id: int,
    payload: BagPermissionUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if traveler_id == user.traveler_id:
        raise HTTPException(status_code=400, detail="Tus maletas ya son tuyas")
    target = get_or_404(db, Traveler, traveler_id)
    family_id = user.traveler.family_id
    if family_id is None or target.family_id != family_id:
        raise HTTPException(
            status_code=400,
            detail="Solo puedes gestionar permisos de miembros de tu familia",
        )
    revoke = db.scalar(
        select(BagEditRevoke).where(
            BagEditRevoke.owner_traveler_id == user.traveler_id,
            BagEditRevoke.editor_traveler_id == traveler_id,
        )
    )
    if payload.allowed and revoke is not None:
        db.delete(revoke)
    elif not payload.allowed and revoke is None:
        db.add(
            BagEditRevoke(
                owner_traveler_id=user.traveler_id, editor_traveler_id=traveler_id
            )
        )
    db.commit()
