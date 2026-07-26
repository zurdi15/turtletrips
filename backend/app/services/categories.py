from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_PACKING_CATEGORIES,
    Category,
    CategoryKind,
    Family,
)


def ensure_default_categories(db: Session, family_id: int) -> None:
    """Siembra las categorías por defecto de una familia si no tiene de ese tipo."""
    defaults = {
        CategoryKind.expense.value: DEFAULT_EXPENSE_CATEGORIES,
        CategoryKind.packing.value: DEFAULT_PACKING_CATEGORIES,
    }
    changed = False
    for kind, entries in defaults.items():
        exists = db.scalar(
            select(Category.id)
            .where(Category.kind == kind, Category.family_id == family_id)
            .limit(1)
        )
        if exists is None:
            for position, (name, color) in enumerate(entries):
                db.add(
                    Category(
                        family_id=family_id,
                        kind=kind,
                        name=name,
                        color=color,
                        position=position,
                    )
                )
            changed = True
    if changed:
        db.commit()


def ensure_default_categories_all(db: Session) -> None:
    """Siembra defaults en todas las familias (arranque y restore, idempotente)."""
    for family_id in db.scalars(select(Family.id)):
        ensure_default_categories(db, family_id)
