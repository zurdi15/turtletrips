from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import (
    PackingItem,
    PackingSelection,
    PackingTemplate,
    PackingTemplateItem,
    Trip,
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
from .common import delete_by_id, get_or_404, save_new, save_updates

router = APIRouter(tags=["packing"])


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
def list_packing(trip_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    return _trip_items(db, trip_id)


@router.get("/trips/{trip_id}/packing/selections", response_model=list[PackingSelectionRead])
def list_selections(trip_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    return db.scalars(
        select(PackingSelection).where(PackingSelection.trip_id == trip_id)
    ).all()


@router.post("/trips/{trip_id}/packing", response_model=PackingItemRead, status_code=201)
def create_packing_item(trip_id: int, payload: PackingItemCreate, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    _validate_traveler(db, trip, payload.traveler_id)
    return save_new(db, PackingItem(trip_id=trip_id), payload.model_dump())


@router.patch("/packing/{item_id}", response_model=PackingItemRead)
def update_packing_item(item_id: int, payload: PackingItemUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, PackingItem, item_id)
    data = payload.model_dump(exclude_unset=True)
    if "traveler_id" in data:
        trip = db.get(Trip, item.trip_id)
        _validate_traveler(db, trip, data["traveler_id"])
    return save_updates(db, item, data)


@router.delete("/packing/{item_id}", status_code=204)
def delete_packing_item(item_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, PackingItem, item_id)


# --- plantillas de maleta ---


def _template_read(template: PackingTemplate) -> PackingTemplateRead:
    return PackingTemplateRead(
        id=template.id, name=template.name, item_count=len(template.items)
    )


@router.get("/packing-templates", response_model=list[PackingTemplateRead])
def list_templates(db: Session = Depends(get_db)):
    templates = db.scalars(
        select(PackingTemplate)
        .options(selectinload(PackingTemplate.items))
        .order_by(PackingTemplate.name)
    ).all()
    return [_template_read(t) for t in templates]


@router.post("/packing-templates", response_model=PackingTemplateRead, status_code=201)
def create_template(payload: PackingTemplateCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    duplicate = db.scalar(
        select(PackingTemplate).where(func.lower(PackingTemplate.name) == name.lower())
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con ese nombre")
    template = PackingTemplate(name=name)
    if payload.from_trip_id is not None:
        trip = get_or_404(db, Trip, payload.from_trip_id)
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
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = get_or_404(db, PackingTemplate, template_id)
    return PackingTemplateDetail(id=template.id, name=template.name, items=template.items)


@router.patch("/packing-templates/{template_id}", response_model=PackingTemplateRead)
def rename_template(
    template_id: int, payload: PackingTemplateUpdate, db: Session = Depends(get_db)
):
    template = get_or_404(db, PackingTemplate, template_id)
    name = payload.name.strip()
    duplicate = db.scalar(
        select(PackingTemplate).where(
            func.lower(PackingTemplate.name) == name.lower(),
            PackingTemplate.id != template_id,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe una plantilla con ese nombre")
    template.name = name
    db.commit()
    db.refresh(template)
    return _template_read(template)


@router.delete("/packing-templates/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, PackingTemplate, template_id)


@router.post("/packing-templates/{template_id}/items", response_model=PackingTemplateItemRead, status_code=201)
def create_template_item(
    template_id: int, payload: PackingTemplateItemCreate, db: Session = Depends(get_db)
):
    get_or_404(db, PackingTemplate, template_id)
    return save_new(db, PackingTemplateItem(template_id=template_id), payload.model_dump())


@router.patch("/packing-template-items/{item_id}", response_model=PackingTemplateItemRead)
def update_template_item(
    item_id: int, payload: PackingTemplateItemUpdate, db: Session = Depends(get_db)
):
    item = get_or_404(db, PackingTemplateItem, item_id)
    return save_updates(db, item, payload.model_dump(exclude_unset=True))


@router.delete("/packing-template-items/{item_id}", status_code=204)
def delete_template_item(item_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, PackingTemplateItem, item_id)


@router.post(
    "/trips/{trip_id}/packing/apply/{template_id}", response_model=list[PackingItemRead]
)
def apply_template(
    trip_id: int,
    template_id: int,
    traveler_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Copia la plantilla a la maleta del viajero (o común) y la deja seleccionada.

    Los elementos copiados son independientes: se pueden modificar sin tocar la plantilla.
    No duplica elementos ya presentes en esa maleta.
    """
    trip = get_or_404(db, Trip, trip_id)
    _validate_traveler(db, trip, traveler_id)
    template = get_or_404(db, PackingTemplate, template_id)
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
    return _trip_items(db, trip_id)


@router.post(
    "/packing-templates/{template_id}/sync-from-trip/{trip_id}",
    response_model=PackingTemplateDetail,
)
def sync_template_from_trip(
    template_id: int,
    trip_id: int,
    traveler_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Sobrescribe los elementos de la plantilla con la maleta del viajero (o común)."""
    template = get_or_404(db, PackingTemplate, template_id)
    trip = get_or_404(db, Trip, trip_id)
    _validate_traveler(db, trip, traveler_id)
    template.items.clear()
    for item in _trip_items(db, trip_id, traveler_id):
        template.items.append(
            PackingTemplateItem(name=item.name, category=item.category, url=item.url)
        )
    _upsert_selection(db, trip_id, traveler_id, template_id)
    db.commit()
    db.refresh(template)
    return PackingTemplateDetail(id=template.id, name=template.name, items=template.items)
