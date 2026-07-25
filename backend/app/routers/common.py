import enum
import unicodedata
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..db import Base

T = TypeVar("T", bound=Base)

NOT_FOUND_LABELS = {
    "Trip": "Viaje",
    "Traveler": "Viajero",
    "Place": "Sitio",
    "ItineraryItem": "Elemento de itinerario",
    "Booking": "Reserva",
    "Expense": "Gasto",
    "Settlement": "Liquidación",
    "Attachment": "Adjunto",
    "Category": "Categoría",
    "PackingItem": "Elemento de maleta",
    "PackingTemplate": "Plantilla de maleta",
    "PackingTemplateItem": "Elemento de plantilla",
    "WorldPlace": "Lugar del mapa",
    "DayJournal": "Diario",
}


def get_or_404(db: Session, model: type[T], obj_id: int) -> T:
    obj = db.get(model, obj_id)
    if obj is None:
        label = NOT_FOUND_LABELS.get(model.__name__, model.__name__)
        raise HTTPException(status_code=404, detail=f"{label} no encontrado")
    return obj


def apply_updates(obj: Base, data: dict) -> None:
    for key, value in data.items():
        if isinstance(value, enum.Enum):
            value = value.value
        setattr(obj, key, value)


def ensure_in_trip(
    db: Session, model: type[T], obj_id: int | None, trip_id: int, *, message: str
) -> None:
    """400 con `message` si el objeto no existe o no pertenece al viaje.

    obj_id=None es no-op (enlaces opcionales).
    """
    if obj_id is None:
        return
    obj = db.get(model, obj_id)
    if obj is None or obj.trip_id != trip_id:
        raise HTTPException(status_code=400, detail=message)


def save_new(db: Session, obj: T, data: dict) -> T:
    apply_updates(obj, data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def save_updates(db: Session, obj: T, data: dict) -> T:
    apply_updates(obj, data)
    db.commit()
    db.refresh(obj)
    return obj


def delete_by_id(db: Session, model: type[T], obj_id: int) -> None:
    db.delete(get_or_404(db, model, obj_id))
    db.commit()


def ascii_filename(name: str, fallback: str) -> str:
    """Nombre apto para Content-Disposition (los headers HTTP solo admiten ASCII)."""
    return (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode()
        .replace(" ", "_")[:50]
        or fallback
    )
