from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import ExchangeRateCache


class RateUnavailableError(Exception):
    pass


def _cached_rate(db: Session, base: str, quote: str, day: date) -> Decimal | None:
    row = db.scalar(
        select(ExchangeRateCache).where(
            ExchangeRateCache.base == base,
            ExchangeRateCache.quote == quote,
            ExchangeRateCache.day == day,
        )
    )
    return Decimal(str(row.rate)) if row else None


async def get_rate(db: Session, base: str, quote: str, day: date) -> tuple[Decimal, str]:
    """Tipo de cambio base->quote para un día. Devuelve (rate, source).

    Orden: identidad, cache en DB, API de frankfurter (y se cachea).
    Lanza RateUnavailableError si no hay red y no está cacheado.
    """
    base, quote = base.upper(), quote.upper()
    if base == quote:
        return Decimal(1), "identity"

    cached = _cached_rate(db, base, quote, day)
    if cached is not None:
        return cached, "cache"

    settings = get_settings()
    # frankfurter no tiene datos de fines de semana: /{date} devuelve el día hábil anterior
    url = f"{settings.rates_url}/{day.isoformat()}"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, params={"base": base, "symbols": quote})
            resp.raise_for_status()
            data = resp.json()
        rate = Decimal(str(data["rates"][quote]))
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise RateUnavailableError(
            f"No se pudo obtener el tipo de cambio {base}->{quote} para {day}"
        ) from exc

    db.add(ExchangeRateCache(base=base, quote=quote, day=day, rate=rate))
    db.commit()
    return rate, "api"
