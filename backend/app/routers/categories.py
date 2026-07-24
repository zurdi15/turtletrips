from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Category, Expense, PackingItem, PackingTemplateItem
from ..schemas.packing import CategoryCreate, CategoryRead, CategoryUpdate
from .common import delete_by_id, get_or_404

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(kind: str | None = None, db: Session = Depends(get_db)):
    query = select(Category).order_by(Category.position, Category.id)
    if kind is not None:
        query = query.where(Category.kind == kind)
    return db.scalars(query).all()


@router.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    name = payload.name.strip()
    duplicate = db.scalar(
        select(Category).where(
            Category.kind == payload.kind, func.lower(Category.name) == name.lower()
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe esa categoría")
    max_pos = db.scalar(
        select(func.coalesce(func.max(Category.position), -1)).where(Category.kind == payload.kind)
    )
    category = Category(kind=payload.kind, name=name, color=payload.color, position=max_pos + 1)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    category = get_or_404(db, Category, category_id)
    data = payload.model_dump(exclude_unset=True)
    new_name = data.get("name")
    if new_name is not None:
        new_name = new_name.strip()
        duplicate = db.scalar(
            select(Category).where(
                Category.kind == category.kind,
                func.lower(Category.name) == new_name.lower(),
                Category.id != category_id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe esa categoría")
        # renombrar también en los datos existentes
        if category.kind == "expense":
            db.execute(
                update(Expense).where(Expense.category == category.name).values(category=new_name)
            )
        else:
            db.execute(
                update(PackingItem)
                .where(PackingItem.category == category.name)
                .values(category=new_name)
            )
            db.execute(
                update(PackingTemplateItem)
                .where(PackingTemplateItem.category == category.name)
                .values(category=new_name)
            )
        category.name = new_name
    if "color" in data:
        category.color = data["color"]
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Borra la categoría; los gastos/objetos existentes conservan el nombre."""
    delete_by_id(db, Category, category_id)
