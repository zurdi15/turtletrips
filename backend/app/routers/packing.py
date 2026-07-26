from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..auth import CurrentUser
from ..db import get_db
from ..models import (
    PackingItem,
    PackingSelection,
    PackingTemplate,
    PackingTemplateItem,
    Traveler,
    Trip,
    User,
)
from ..schemas.packing import (
    PackingItemCreate,
    PackingItemRead,
    PackingItemUpdate,
    PackingSelectionRead,
    PackingTemplateCreate,
    PackingTemplateDetail,
    PackingTemplateItemCreate,
    PackingTemplateItemRead,
    PackingTemplateItemUpdate,
    PackingTemplateRead,
    PackingTemplateUpdate,
)
from .common import (
    ensure_trip_member,
    get_or_404,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["packing"])


# --- matriz de permisos (por FAMILIA) ---
# Maletas de viaje: ver = poder editar. La común es de todos; las de tu familia
# (con o sin cuenta) las editáis todos; las de otras familias NI SE VEN (la
# lista de items y selecciones se filtra en el servidor). Plantillas: las de
# toda tu familia se VEN; se EDITAN solo las tuyas y las de virtuales de tu
# familia. El admin conserva el bypass total en ambas.


def _bag_visible(user: User, traveler: Traveler | None, traveler_id: int | None) -> bool:
    if user.is_admin or traveler_id is None or traveler_id == user.traveler_id:
        return True
    family_id = user.traveler.family_id
    return traveler is not None and family_id is not None and traveler.family_id == family_id


def _ensure_bag_editable(db: Session, user: User, traveler_id: int | None) -> None:
    traveler = db.get(Traveler, traveler_id) if traveler_id is not None else None
    if not _bag_visible(user, traveler, traveler_id):
        raise HTTPException(status_code=403, detail="Esa maleta es de otra familia")


def _visible_items(user: User, trip: Trip, items: list[PackingItem]) -> list[PackingItem]:
    by_id = {t.id: t for t in trip.travelers}
    return [
        item
        for item in items
        if _bag_visible(user, by_id.get(item.traveler_id), item.traveler_id)
    ]


def _can_read_template(user: User, owner: Traveler) -> bool:
    if user.is_admin or owner.id == user.traveler_id:
        return True
    return owner.family_id is not None and owner.family_id == user.traveler.family_id


def _can_edit_template(user: User, owner: Traveler) -> bool:
    if user.is_admin or owner.id == user.traveler_id:
        return True
    return not owner.has_user and _can_read_template(user, owner)


def _ensure_template_readable(user: User, template: PackingTemplate) -> None:
    if not _can_read_template(user, template.traveler):
        raise HTTPException(status_code=403, detail="Esa plantilla es de otra familia")


def _ensure_template_editable(user: User, template: PackingTemplate) -> None:
    _ensure_template_readable(user, template)
    if not _can_edit_template(user, template.traveler):
        raise HTTPException(
            status_code=403, detail="Las plantillas de otro viajero son solo de consulta"
        )


def _resolve_template_owner(db: Session, user: User, traveler_id: int | None) -> int:
    """Dueño de una plantilla nueva: tú (None) o un viajero que puedas gestionar."""
    if traveler_id is None or traveler_id == user.traveler_id:
        return user.traveler_id
    traveler = get_or_404(db, Traveler, traveler_id)
    if not _can_edit_template(user, traveler):
        raise HTTPException(
            status_code=403,
            detail="Solo puedes crear plantillas tuyas o de viajeros sin cuenta de tu familia",
        )
    return traveler.id


def _validate_traveler(db: Session, trip: Trip, traveler_id: int | None) -> None:
    if traveler_id is None:
        return
    if not any(t.id == traveler_id for t in trip.travelers):
        raise HTTPException(status_code=400, detail="El viajero no pertenece a este viaje")


def _trip_items(db: Session, trip_id: int, traveler_id: int | None = ...) -> list[PackingItem]:
    query = select(PackingItem).where(PackingItem.trip_id == trip_id)
    if traveler_id is not ...:
        query = query.where(PackingItem.traveler_id == traveler_id)
    return list(db.scalars(query.order_by(PackingItem.id)))


def _upsert_selection(
    db: Session, trip_id: int, traveler_id: int | None, template_id: int
) -> None:
    selection = db.scalar(
        select(PackingSelection).where(
            PackingSelection.trip_id == trip_id,
            PackingSelection.traveler_id == traveler_id,
        )
    )
    if selection is None:
        db.add(PackingSelection(trip_id=trip_id, traveler_id=traveler_id, template_id=template_id))
    else:
        selection.template_id = template_id


@router.get("/trips/{trip_id}/packing", response_model=list[PackingItemRead])
def list_packing(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    return _visible_items(user, trip, _trip_items(db, trip_id))


@router.get("/trips/{trip_id}/packing/selections", response_model=list[PackingSelectionRead])
def list_selections(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    by_id = {t.id: t for t in trip.travelers}
    selections = db.scalars(
        select(PackingSelection).where(PackingSelection.trip_id == trip_id)
    ).all()
    return [
        s for s in selections
        if _bag_visible(user, by_id.get(s.traveler_id), s.traveler_id)
    ]


@router.delete("/trips/{trip_id}/packing/selection", status_code=204)
def clear_selection(
    trip_id: int,
    user: CurrentUser,
    traveler_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Desvincula la plantilla asociada a la maleta; los elementos no se tocan."""
    ensure_trip_member(db, user, trip_id)
    _ensure_bag_editable(db, user, traveler_id)
    selection = db.scalar(
        select(PackingSelection).where(
            PackingSelection.trip_id == trip_id,
            PackingSelection.traveler_id == traveler_id,
        )
    )
    if selection is not None:
        db.delete(selection)
        db.commit()


@router.post("/trips/{trip_id}/packing", response_model=PackingItemRead, status_code=201)
def create_packing_item(
    trip_id: int, payload: PackingItemCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    _validate_traveler(db, trip, payload.traveler_id)
    _ensure_bag_editable(db, user, payload.traveler_id)
    return save_new(db, PackingItem(trip_id=trip_id), payload.model_dump())


@router.patch("/packing/{item_id}", response_model=PackingItemRead)
def update_packing_item(
    item_id: int, payload: PackingItemUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    item = get_trip_scoped(db, user, PackingItem, item_id)
    _ensure_bag_editable(db, user, item.traveler_id)
    data = payload.model_dump(exclude_unset=True)
    if "traveler_id" in data:
        trip = db.get(Trip, item.trip_id)
        _validate_traveler(db, trip, data["traveler_id"])
        # mover un elemento exige poder editar también la maleta destino
        _ensure_bag_editable(db, user, data["traveler_id"])
    return save_updates(db, item, data)


@router.delete("/packing/{item_id}", status_code=204)
def delete_packing_item(item_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    item = get_trip_scoped(db, user, PackingItem, item_id)
    _ensure_bag_editable(db, user, item.traveler_id)
    db.delete(item)
    db.commit()


# --- plantillas de maleta ---


def _template_read(template: PackingTemplate) -> PackingTemplateRead:
    return PackingTemplateRead(
        id=template.id,
        traveler_id=template.traveler_id,
        name=template.name,
        item_count=len(template.items),
    )


@router.get("/packing-templates", response_model=list[PackingTemplateRead])
def list_templates(user: CurrentUser, db: Session = Depends(get_db)):
    # las tuyas + las de TODA tu familia (las ajenas en solo-consulta);
    # el admin las ve TODAS (gestiona plantillas de cualquier viajero)
    query = select(PackingTemplate)
    if not user.is_admin:
        conditions = [PackingTemplate.traveler_id == user.traveler_id]
        family_id = user.traveler.family_id
        if family_id is not None:
            conditions.append(
                PackingTemplate.traveler_id.in_(
                    select(Traveler.id).where(Traveler.family_id == family_id)
                )
            )
        query = query.where(or_(*conditions))
    templates = db.scalars(
        query.options(selectinload(PackingTemplate.items)).order_by(PackingTemplate.name)
    ).all()
    return [_template_read(t) for t in templates]


@router.post("/packing-templates", response_model=PackingTemplateRead, status_code=201)
def create_template(
    payload: PackingTemplateCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    # el dueño es el viajero de la maleta origen (o el indicado); la común, tuya
    owner_id = _resolve_template_owner(db, user, payload.traveler_id)
    name = payload.name.strip()
    duplicate = db.scalar(
        select(PackingTemplate).where(
            PackingTemplate.traveler_id == owner_id,
            func.lower(PackingTemplate.name) == name.lower(),
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con ese nombre")
    template = PackingTemplate(name=name, traveler_id=owner_id)
    if payload.from_trip_id is not None:
        trip = ensure_trip_member(db, user, payload.from_trip_id)
        _validate_traveler(db, trip, payload.traveler_id)
        for item in _trip_items(db, trip.id, payload.traveler_id):
            template.items.append(
                PackingTemplateItem(name=item.name, category=item.category, url=item.url)
            )
    db.add(template)
    db.flush()
    if payload.from_trip_id is not None:
        # la maleta pasa a estar asociada a la plantilla recién creada
        _upsert_selection(db, payload.from_trip_id, payload.traveler_id, template.id)
    db.commit()
    db.refresh(template)
    return _template_read(template)


@router.get("/packing-templates/{template_id}", response_model=PackingTemplateDetail)
def get_template(template_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_readable(user, template)
    return PackingTemplateDetail(
        id=template.id,
        traveler_id=template.traveler_id,
        name=template.name,
        items=template.items,
    )


@router.patch("/packing-templates/{template_id}", response_model=PackingTemplateRead)
def update_template(
    template_id: int, payload: PackingTemplateUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_editable(user, template)
    data = payload.model_dump(exclude_unset=True)
    owner_id = template.traveler_id
    new_owner = data.get("traveler_id")
    if new_owner is not None and new_owner != template.traveler_id:
        # reasignar dueño (mover la maleta a otro viajero/familia): solo admin
        if not user.is_admin:
            raise HTTPException(
                status_code=403, detail="Solo el administrador puede reasignar plantillas"
            )
        owner_id = get_or_404(db, Traveler, new_owner).id
    name = data["name"].strip() if data.get("name") else template.name
    duplicate = db.scalar(
        select(PackingTemplate).where(
            PackingTemplate.traveler_id == owner_id,
            func.lower(PackingTemplate.name) == name.lower(),
            PackingTemplate.id != template_id,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con ese nombre")
    template.name = name
    template.traveler_id = owner_id
    db.commit()
    db.refresh(template)
    return _template_read(template)


@router.delete("/packing-templates/{template_id}", status_code=204)
def delete_template(template_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_editable(user, template)
    db.delete(template)
    db.commit()


@router.post("/packing-templates/{template_id}/items", response_model=PackingTemplateItemRead, status_code=201)
def create_template_item(
    template_id: int, payload: PackingTemplateItemCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_editable(user, template)
    return save_new(db, PackingTemplateItem(template_id=template_id), payload.model_dump())


@router.patch("/packing-template-items/{item_id}", response_model=PackingTemplateItemRead)
def update_template_item(
    item_id: int, payload: PackingTemplateItemUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    item = get_or_404(db, PackingTemplateItem, item_id)
    _ensure_template_editable(user, item.template)
    return save_updates(db, item, payload.model_dump(exclude_unset=True))


@router.delete("/packing-template-items/{item_id}", status_code=204)
def delete_template_item(item_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    item = get_or_404(db, PackingTemplateItem, item_id)
    _ensure_template_editable(user, item.template)
    db.delete(item)
    db.commit()


@router.post(
    "/trips/{trip_id}/packing/apply/{template_id}", response_model=list[PackingItemRead]
)
def apply_template(
    trip_id: int,
    template_id: int,
    user: CurrentUser,
    traveler_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Copia la plantilla a la maleta del viajero (o común) y la deja seleccionada.

    Los elementos copiados son independientes: se pueden modificar sin tocar la plantilla.
    No duplica elementos ya presentes en esa maleta.
    """
    trip = ensure_trip_member(db, user, trip_id)
    _validate_traveler(db, trip, traveler_id)
    _ensure_bag_editable(db, user, traveler_id)
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_readable(user, template)
    existing = {
        (item.name.strip().lower(), item.category)
        for item in _trip_items(db, trip_id, traveler_id)
    }
    for entry in template.items:
        if (entry.name.strip().lower(), entry.category) in existing:
            continue
        db.add(
            PackingItem(
                trip_id=trip_id,
                traveler_id=traveler_id,
                name=entry.name,
                category=entry.category,
                url=entry.url,
            )
        )
    _upsert_selection(db, trip_id, traveler_id, template_id)
    db.commit()
    return _visible_items(user, trip, _trip_items(db, trip_id))


@router.post(
    "/packing-templates/{template_id}/sync-from-trip/{trip_id}",
    response_model=PackingTemplateDetail,
)
def sync_template_from_trip(
    template_id: int,
    trip_id: int,
    user: CurrentUser,
    traveler_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Sobrescribe los elementos de la plantilla con la maleta del viajero (o común)."""
    template = get_or_404(db, PackingTemplate, template_id)
    _ensure_template_editable(user, template)
    trip = ensure_trip_member(db, user, trip_id)
    _validate_traveler(db, trip, traveler_id)
    _ensure_bag_editable(db, user, traveler_id)
    template.items.clear()
    for item in _trip_items(db, trip_id, traveler_id):
        template.items.append(
            PackingTemplateItem(name=item.name, category=item.category, url=item.url)
        )
    _upsert_selection(db, trip_id, traveler_id, template_id)
    db.commit()
    db.refresh(template)
    return PackingTemplateDetail(
        id=template.id,
        traveler_id=template.traveler_id,
        name=template.name,
        items=template.items,
    )
