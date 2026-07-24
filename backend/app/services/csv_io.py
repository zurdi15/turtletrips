import csv
import io
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Category, CategoryKind, Expense, Place, Traveler, Trip
from ..schemas.expense import ImportPreviewRow, ImportResult, ImportRowError

EXPORT_COLUMNS = [
    "day", "category", "description", "amount", "currency",
    "exchange_rate", "amount_base", "paid_by", "place", "notes",
]

_HEADER_ALIASES = {
    "day": {"day", "fecha", "date", "dia"},
    "category": {"category", "categoria", "tipo"},
    "description": {"description", "descripcion", "concepto", "detalle"},
    "amount": {"amount", "importe", "cantidad", "monto"},
    "currency": {"currency", "moneda", "divisa"},
    "exchange_rate": {"exchange_rate", "tasa", "cambio", "tipo_cambio", "tipo_de_cambio"},
    "paid_by": {"paid_by", "pagado_por", "pagador", "quien_pago"},
    "place": {"place", "lugar", "sitio", "ubicacion"},  # se fusiona con las notas
    "notes": {"notes", "notas", "comentarios"},
}

_MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
}

# alias habituales (incluye los nombres del enum antiguo) -> categoría actual
_CATEGORY_ALIASES = {
    "comida": "Comida", "food": "Comida", "restaurante": "Comida",
    "transporte": "Transporte", "transport": "Transporte",
    "alojamiento": "Alojamiento", "lodging": "Alojamiento", "hotel": "Alojamiento",
    "tours": "Tours", "activities": "Tours", "actividades": "Tours", "actividad": "Tours",
    "entradas": "Entradas", "tickets": "Entradas", "entrada": "Entradas",
    "souvenirs": "Souvenirs", "shopping": "Souvenirs", "compras": "Souvenirs",
    "gasolina": "Gasolina", "fuel": "Gasolina", "combustible": "Gasolina",
    "vuelos": "Vuelos", "flights": "Vuelos", "vuelo": "Vuelos",
    "otros": "Otros", "other": "Otros", "otro": "Otros", "fees": "Otros", "tasas": "Otros",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace(" ", "_")


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    # formato largo español: "10 febrero 2026", "10 de febrero de 2026", "10-feb-2026"
    parts = [
        p for p in re.split(r"[ _\-/]+", _normalize(raw)) if p and p not in ("de", "del")
    ]
    if len(parts) == 3 and parts[0].isdigit() and parts[2].isdigit():
        month = _MONTHS_ES.get(parts[1])
        if month:
            return date(int(parts[2]), month, int(parts[0]))
    raise ValueError(f"Fecha no reconocida: {raw!r}")


def _parse_amount(raw: str) -> Decimal:
    # quita símbolos de moneda y cualquier espacio (incluidos los nbsp que mete Excel)
    cleaned = re.sub(r"[\s\u00a0\u202f]", "", raw).replace("€", "").replace("$", "")
    if "," in cleaned and "." in cleaned:
        # "1.234,56" (formato español) vs "1,234.56"
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Importe no reconocido: {raw!r}") from exc


def _resolve_category(db: Session, raw: str) -> str:
    """Alias conocidos, categoría existente (sin distinguir mayúsculas/acentos) o el texto tal cual."""
    normalized = _normalize(raw)
    if normalized in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[normalized]
    for cat in db.scalars(select(Category).where(Category.kind == CategoryKind.expense.value)):
        if _normalize(cat.name) == normalized:
            return cat.name
    return raw.strip()[:50]


def export_csv(db: Session, trip: Trip) -> str:
    travelers = {t.id: t.name for t in db.scalars(select(Traveler))}
    places = {p.id: p.name for p in trip.places}
    expenses = db.scalars(
        select(Expense).where(Expense.trip_id == trip.id).order_by(Expense.day, Expense.id)
    ).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for e in expenses:
        writer.writerow([
            e.day.isoformat(), e.category, e.description, str(e.amount), e.currency,
            str(e.exchange_rate), str(e.amount_base),
            travelers.get(e.paid_by_id, "") if e.paid_by_id else "",
            places.get(e.place_id, "") if e.place_id else "", e.notes or "",
        ])
    return buffer.getvalue()


def _map_headers(fieldnames: list[str]) -> dict[str, str]:
    """Mapea nombre de columna del CSV -> campo canónico."""
    mapping: dict[str, str] = {}
    for raw in fieldnames:
        normalized = _normalize(raw)
        for field, aliases in _HEADER_ALIASES.items():
            if normalized in aliases and field not in mapping.values():
                mapping[raw] = field
                break
    return mapping


def import_csv(db: Session, trip: Trip, content: bytes, dry_run: bool) -> ImportResult:
    text = content.decode("utf-8-sig", errors="replace")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return ImportResult(dry_run=dry_run, valid_rows=[], errors=[
            ImportRowError(row=0, error="CSV vacío o sin cabecera")
        ], imported=0)

    header_map = _map_headers(list(reader.fieldnames))
    required = {"day", "description", "amount"}
    missing = required - set(header_map.values())
    if missing:
        return ImportResult(dry_run=dry_run, valid_rows=[], errors=[
            ImportRowError(row=0, error=f"Faltan columnas requeridas: {', '.join(sorted(missing))}")
        ], imported=0)

    valid: list[tuple[ImportPreviewRow, str | None]] = []
    errors: list[ImportRowError] = []
    last_day: date | None = None  # las filas sin fecha heredan la de la fila anterior

    for idx, raw_row in enumerate(reader, start=2):  # fila 1 = cabecera
        row = {header_map[k]: (v or "").strip() for k, v in raw_row.items() if k in header_map}
        if not any(row.values()):
            continue
        try:
            if row.get("day"):
                day = _parse_date(row["day"])
                last_day = day
            elif last_day is not None:
                day = last_day
            elif trip.start_date is not None:
                day = trip.start_date
                last_day = day
            else:
                raise ValueError(
                    "Fila sin fecha, sin fila anterior de la que heredarla y el viaje no tiene fecha de inicio"
                )
            amount = _parse_amount(row["amount"])
            if amount <= 0:
                raise ValueError("El importe debe ser positivo")
            currency = (row.get("currency") or trip.base_currency).upper()
            if len(currency) != 3:
                raise ValueError(f"Moneda no reconocida: {currency!r}")

            category = _resolve_category(db, row["category"]) if row.get("category") else "Otros"

            if row.get("exchange_rate"):
                rate = _parse_amount(row["exchange_rate"])
            elif currency == trip.base_currency.upper():
                rate = Decimal(1)
            else:
                raise ValueError(
                    f"Falta exchange_rate para moneda {currency} (distinta de {trip.base_currency})"
                )

            paid_by = row.get("paid_by") or None
            preview = ImportPreviewRow(
                row=idx, day=day, category=category, description=row["description"],
                amount=float(amount), currency=currency, exchange_rate=float(rate),
                amount_base=float((amount * rate).quantize(Decimal("0.01"))),
                paid_by=paid_by, place=row.get("place") or None,
                notes=row.get("notes") or None,
            )
            valid.append((preview, paid_by))
        except (ValueError, KeyError) as exc:
            errors.append(ImportRowError(row=idx, error=str(exc)))

    imported = 0
    if not dry_run:
        travelers_by_name = {
            t.name.strip().lower(): t for t in db.scalars(select(Traveler))
        }
        places_by_name = {p.name.strip().lower(): p for p in trip.places}
        known_categories = {
            _normalize(c.name)
            for c in db.scalars(select(Category).where(Category.kind == CategoryKind.expense.value))
        }
        max_pos = db.scalar(
            select(func.coalesce(func.max(Category.position), -1)).where(
                Category.kind == CategoryKind.expense.value
            )
        )
        for preview, paid_by_name in valid:
            # el pagador se crea como viajero global y se asocia al viaje
            paid_by_id = None
            if paid_by_name:
                key = paid_by_name.strip().lower()
                traveler = travelers_by_name.get(key)
                if traveler is None:
                    traveler = Traveler(name=paid_by_name.strip())
                    db.add(traveler)
                    db.flush()
                    travelers_by_name[key] = traveler
                if traveler not in trip.travelers:
                    trip.travelers.append(traveler)
                paid_by_id = traveler.id
            # las categorías desconocidas se crean automáticamente
            if _normalize(preview.category) not in known_categories:
                max_pos += 1
                db.add(
                    Category(
                        kind=CategoryKind.expense.value,
                        name=preview.category,
                        color="#94a3b8",
                        position=max_pos,
                    )
                )
                known_categories.add(_normalize(preview.category))
            # la columna "lugar" se convierte en un sitio real del viaje (o reutiliza uno)
            place_id = None
            if preview.place:
                key = preview.place.strip().lower()
                place = places_by_name.get(key)
                if place is None:
                    place = Place(trip_id=trip.id, name=preview.place.strip(), category="other")
                    db.add(place)
                    db.flush()
                    places_by_name[key] = place
                place_id = place.id
            db.add(Expense(
                trip_id=trip.id,
                day=preview.day,
                category=preview.category,
                description=preview.description,
                amount=Decimal(str(preview.amount)),
                currency=preview.currency,
                exchange_rate=Decimal(str(preview.exchange_rate)),
                amount_base=Decimal(str(preview.amount_base)),
                paid_by_id=paid_by_id,
                place_id=place_id,
                notes=preview.notes,
            ))
            imported += 1
        db.commit()

    return ImportResult(
        dry_run=dry_run,
        valid_rows=[p for p, _ in valid],
        errors=errors,
        imported=imported,
    )
