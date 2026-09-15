from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import LinkGroup, TripLink
from ..services import files
from ..services.link_preview import fetch_preview_image
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


def _refresh_image(link: TripLink) -> None:
    """Descarga la miniatura OG del enlace (best-effort) y sustituye la anterior.
    Sin commit: lo hace quien llama."""
    fetched = fetch_preview_image(link.url)
    if link.image_path:
        files.delete_stored_file(link.trip_id, link.image_path)
        link.image_path = None
    if fetched is None:
        return
    content, suffix = fetched
    try:
        link.image_path = files.save_bytes(link.trip_id, content, suffix)
    except files.FileValidationError:
        link.image_path = None


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
    return save_new(db, group, {"name": payload.name.strip(), "icon": payload.icon})


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
    link = save_new(db, link, payload.model_dump())
    # la miniatura va DESPUÉS de guardar: un fetch lento o fallido no debe
    # impedir el alta del enlace
    _refresh_image(link)
    db.commit()
    db.refresh(link)
    return link


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
    url_changed = "url" in data and data["url"] != link.url
    link = save_updates(db, link, data)
    if url_changed:
        # otra URL = otra página: la miniatura anterior ya no vale
        _refresh_image(link)
        db.commit()
        db.refresh(link)
    return link


@router.post("/links/{link_id}/refresh-image", response_model=TripLinkRead)
def refresh_link_image(link_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    """Vuelve a intentar la miniatura (p. ej. la primera vez no había red)."""
    link = get_trip_scoped(db, user, TripLink, link_id)
    _refresh_image(link)
    db.commit()
    db.refresh(link)
    return link


@router.get("/links/{link_id}/image", include_in_schema=False)
def get_link_image(link_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    link = get_trip_scoped(db, user, TripLink, link_id)
    if not link.image_path:
        raise HTTPException(status_code=404, detail="Sin imagen")
    try:
        path = files.resolve_stored_file(link.trip_id, link.image_path)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Sin imagen") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sin imagen")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.delete("/links/{link_id}", status_code=204)
def delete_link(link_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    link = get_trip_scoped(db, user, TripLink, link_id)
    if link.image_path:
        files.delete_stored_file(link.trip_id, link.image_path)
    db.delete(link)
    db.commit()
