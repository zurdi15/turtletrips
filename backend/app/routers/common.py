import enum
import unicodedata
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..db import Base
from ..models import Trip, User

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
    "ChecklistItem": "Tarea",
    "PackingTemplate": "Plantilla de maleta",
    "PackingTemplateItem": "Elemento de plantilla",
    "WorldPlace": "Lugar del mapa",
    "DayJournal": "Diario",
    "User": "Usuario",
    "Family": "Familia",
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


def ensure_trip_member(db: Session, user: User, trip_id: int) -> Trip:
    """404 si el viaje no existe; 403 si el viajero del usuario no participa.

    El admin pasa siempre (bypass total: es también la vía de rescate para
    viajes huérfanos sin ningún viajero con cuenta).
    """
    trip = get_or_404(db, Trip, trip_id)
    if user.is_admin:
        return trip
    if not any(t.id == user.traveler_id for t in trip.travelers):
        raise HTTPException(status_code=403, detail="No participas en este viaje")
    return trip


def get_trip_scoped(db: Session, user: User, model: type[T], obj_id: int) -> T:
    """get_or_404 + membresía del viaje del objeto (para mutaciones planas)."""
    obj = get_or_404(db, model, obj_id)
    ensure_trip_member(db, user, obj.trip_id)
    return obj


def delete_trip_scoped(db: Session, user: User, model: type[T], obj_id: int) -> None:
    db.delete(get_trip_scoped(db, user, model, obj_id))
    db.commit()


def require_family(user: User) -> int:
    """family_id del usuario; 403 accionable si su viajero no tiene familia."""
    family_id = user.traveler.family_id
    if family_id is None:
        raise HTTPException(
            status_code=403,
            detail="Tu viajero no pertenece a ninguna familia; pídesela al administrador",
        )
    return family_id


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
