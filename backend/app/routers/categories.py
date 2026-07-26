from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import (
    Category,
    Expense,
    PackingItem,
    PackingTemplate,
    PackingTemplateItem,
    Trip,
    User,
)
from ..schemas.packing import CategoryCreate, CategoryRead, CategoryUpdate
from .common import ensure_trip_member, get_or_404, require_family

router = APIRouter(tags=["categories"])


def _ensure_family_owned(user: User, category: Category) -> None:
    if user.is_admin or category.family_id == user.traveler.family_id:
        return
    raise HTTPException(status_code=403, detail="Esa categoría pertenece a otra familia")


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(
    user: CurrentUser,
    kind: str | None = None,
    trip_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Categorías de tu familia; con ?trip_id= las de la familia del viaje
    (para invitados de otra familia en viajes conjuntos)."""
    if trip_id is not None:
        family_id = ensure_trip_member(db, user, trip_id).family_id
    else:
        family_id = user.traveler.family_id
    if family_id is None:
        return []
    query = (
        select(Category)
        .where(Category.family_id == family_id)
        .order_by(Category.position, Category.id)
    )
    if kind is not None:
        query = query.where(Category.kind == kind)
    return db.scalars(query).all()


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryCreate, user: CurrentUser, db: Session = Depends(get_db)):
    family_id = require_family(user)
    name = payload.name.strip()
    duplicate = db.scalar(
        select(Category).where(
            Category.family_id == family_id,
            Category.kind == payload.kind,
            func.lower(Category.name) == name.lower(),
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe esa categoría")
    max_pos = db.scalar(
        select(func.coalesce(func.max(Category.position), -1)).where(
            Category.family_id == family_id, Category.kind == payload.kind
        )
    )
    category = Category(
        family_id=family_id,
        kind=payload.kind,
        name=name,
        color=payload.color,
        position=max_pos + 1,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, payload: CategoryUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    category = get_or_404(db, Category, category_id)
    _ensure_family_owned(user, category)
    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name is not None:
        new_name = new_name.strip()
        duplicate = db.scalar(
            select(Category).where(
                Category.family_id == category.family_id,
                Category.kind == category.kind,
                func.lower(Category.name) == new_name.lower(),
                Category.id != category_id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe esa categoría")
        # renombrar propaga a los datos existentes, SOLO dentro de la familia
        family_trip_ids = select(Trip.id).where(Trip.family_id == category.family_id)
        if category.kind == "expense":
            db.execute(
                update(Expense)
                .where(
                    Expense.category == category.name,
                    Expense.trip_id.in_(family_trip_ids),
                )
                .values(category=new_name)
            )
        else:
            db.execute(
                update(PackingItem)
                .where(
                    PackingItem.category == category.name,
                    PackingItem.trip_id.in_(family_trip_ids),
                )
                .values(category=new_name)
            )
            family_template_ids = select(PackingTemplate.id).where(
                PackingTemplate.family_id == category.family_id
            )
            db.execute(
                update(PackingTemplateItem)
                .where(
                    PackingTemplateItem.category == category.name,
                    PackingTemplateItem.template_id.in_(family_template_ids),
                )
                .values(category=new_name)
            )
        category.name = new_name
    if "color" in data:
        category.color = data["color"]
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    """Borra la categoría; los gastos/objetos existentes conservan el nombre."""
    category = get_or_404(db, Category, category_id)
    _ensure_family_owned(user, category)
    db.delete(category)
    db.commit()
