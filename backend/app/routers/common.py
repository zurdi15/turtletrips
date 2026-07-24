import enum
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
    "Attachment": "Adjunto",
    "Category": "Categoría",
    "PackingItem": "Elemento de maleta",
    "PackingTemplate": "Plantilla de maleta",
    "PackingTemplateItem": "Elemento de plantilla",
    "WorldPlace": "Lugar del mapa",
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
