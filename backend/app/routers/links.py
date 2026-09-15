from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import LinkGroup, TripLink
from ..schemas.links import (
    LinkGroupCreate,
    LinkGroupRead,
    LinkGroupReorder,
    LinkGroupUpdate,
    TripLinkCreate,
    TripLinkRead,
    TripLinkReorder,
    TripLinkUpdate,
)
from .common import (
    delete_trip_scoped,
    ensure_trip_member,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["links"])


def _ensure_group_in_trip(db: Session, trip_id: int, group_id: int | None) -> None:
    """Un enlace solo puede colgar de un bloque de SU viaje (400 si no)."""
    if group_id is None:
        return
    group = db.get(LinkGroup, group_id)
    if group is None or group.trip_id != trip_id:
        raise HTTPException(status_code=400, detail="El bloque no pertenece a este viaje")


def _next_position(db: Session, model, trip_id: int, **filters) -> int:
    """Siguiente posición libre (al final) dentro del viaje/bloque."""
    stmt = select(model.position).where(model.trip_id == trip_id)
    for key, value in filters.items():
        stmt = stmt.where(getattr(model, key) == value)
    positions = db.scalars(stmt).all()
    return (max(positions) + 1) if positions else 0


# ---- bloques ----


@router.get("/trips/{trip_id}/link-groups", response_model=list[LinkGroupRead])
def list_link_groups(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    return db.scalars(
        select(LinkGroup)
        .where(LinkGroup.trip_id == trip_id)
        .order_by(LinkGroup.position, LinkGroup.id)
    ).all()


@router.post("/trips/{trip_id}/link-groups", response_model=LinkGroupRead, status_code=201)
def create_link_group(
    trip_id: int, payload: LinkGroupCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    group = LinkGroup(trip_id=trip_id, position=_next_position(db, LinkGroup, trip_id))
    return save_new(db, group, {"name": payload.name.strip()})


@router.post("/trips/{trip_id}/link-groups/reorder", status_code=204)
def reorder_link_groups(
    trip_id: int, payload: LinkGroupReorder, user: CurrentUser, db: Session = Depends(get_db)
):
    """Fija el orden manual de los bloques: la posición es el índice recibido."""
    ensure_trip_member(db, user, trip_id)
    groups = {
        g.id: g for g in db.scalars(select(LinkGroup).where(LinkGroup.trip_id == trip_id))
    }
    for position, group_id in enumerate(payload.ids):
        group = groups.get(group_id)
        if group is not None:
            group.position = position
    db.commit()


@router.patch("/link-groups/{group_id}", response_model=LinkGroupRead)
def update_link_group(
    group_id: int, payload: LinkGroupUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    group = get_trip_scoped(db, user, LinkGroup, group_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        data["name"] = data["name"].strip()
    return save_updates(db, group, data)


@router.delete("/link-groups/{group_id}", status_code=204)
def delete_link_group(group_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    """Borra el bloque; sus enlaces sobreviven sin bloque (FK SET NULL)."""
    delete_trip_scoped(db, user, LinkGroup, group_id)


# ---- enlaces ----


@router.get("/trips/{trip_id}/links", response_model=list[TripLinkRead])
def list_links(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    return db.scalars(
        select(TripLink)
        .where(TripLink.trip_id == trip_id)
        .order_by(TripLink.position, TripLink.id)
    ).all()


@router.post("/trips/{trip_id}/links", response_model=TripLinkRead, status_code=201)
def create_link(
    trip_id: int, payload: TripLinkCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    _ensure_group_in_trip(db, trip_id, payload.group_id)
    link = TripLink(
        trip_id=trip_id,
        position=_next_position(db, TripLink, trip_id, group_id=payload.group_id),
    )
    return save_new(db, link, payload.model_dump())


@router.post("/trips/{trip_id}/links/reorder", response_model=list[TripLinkRead])
def reorder_links(
    trip_id: int, payload: TripLinkReorder, user: CurrentUser, db: Session = Depends(get_db)
):
    """Aplica la disposición completa (bloque + posición) tras un drag & drop
    y devuelve la lista resultante para que el front la sustituya de golpe."""
    ensure_trip_member(db, user, trip_id)
    links = {
        link.id: link
        for link in db.scalars(select(TripLink).where(TripLink.trip_id == trip_id))
    }
    for bucket in payload.buckets:
        _ensure_group_in_trip(db, trip_id, bucket.group_id)
        for position, link_id in enumerate(bucket.ids):
            link = links.get(link_id)
            if link is not None:
                link.group_id = bucket.group_id
                link.position = position
    db.commit()
    return list_links(trip_id, user, db)


@router.patch("/links/{link_id}", response_model=TripLinkRead)
def update_link(
    link_id: int, payload: TripLinkUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    link = get_trip_scoped(db, user, TripLink, link_id)
    data = payload.model_dump(exclude_unset=True)
    if "group_id" in data and data["group_id"] != link.group_id:
        _ensure_group_in_trip(db, link.trip_id, data["group_id"])
        # al cambiar de bloque el enlace se va al final del nuevo
        data["position"] = _next_position(
            db, TripLink, link.trip_id, group_id=data["group_id"]
        )
    return save_updates(db, link, data)


@router.delete("/links/{link_id}", status_code=204)
def delete_link(link_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    delete_trip_scoped(db, user, TripLink, link_id)
