from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_PACKING_CATEGORIES,
    Category,
    CategoryKind,
)


def ensure_default_categories(db: Session) -> None:
    """Siembra las categorías por defecto si no hay ninguna de ese tipo."""
    defaults = {
        CategoryKind.expense.value: DEFAULT_EXPENSE_CATEGORIES,
        CategoryKind.packing.value: DEFAULT_PACKING_CATEGORIES,
    }
    changed = False
    for kind, entries in defaults.items():
        exists = db.scalar(select(Category.id).where(Category.kind == kind).limit(1))
        if exists is None:
            for position, (name, color) in enumerate(entries):
                db.add(Category(kind=kind, name=name, color=color, position=position))
            changed = True
    if changed:
        db.commit()
