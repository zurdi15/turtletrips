import asyncio
import time
from typing import Any

import httpx

from ..config import get_settings
from ..schemas.misc import GeocodeResult

_USER_AGENT = "tt-travel-app/0.1 (self-hosted; https://github.com/zurdi)"
_MIN_INTERVAL = 1.1  # política de uso de Nominatim: máx 1 req/s
_CACHE_MAX = 200

_lock = asyncio.Lock()
_last_request = 0.0
# búsquedas y reversos comparten caché: las claves no colisionan ("q:" / "r:")
_cache: dict[str, Any] = {}


class GeocodeError(Exception):
    pass


async def _nominatim(path: str, params: dict[str, Any]) -> Any:
    """GET a Nominatim respetando el ritmo de 1 req/s (serializado por el lock)."""
    settings = get_settings()
    global _last_request
    async with _lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.nominatim_url}/{path}",
                    # es,en: español donde exista traducción y, si no, inglés
                    # (romanizado) — sin el fallback, lo no traducido sale en
                    # el alfabeto local (ホテルグレイスリー新宿, 花道通り…)
                    params={**params, "format": "jsonv2", "accept-language": "es,en"},
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as exc:
            raise GeocodeError(f"Error consultando Nominatim: {exc}") from exc
        finally:
            _last_request = time.monotonic()


def _remember(key: str, value: Any) -> Any:
    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[key] = value
    return value


def _to_result(item: dict[str, Any]) -> GeocodeResult:
    return GeocodeResult(
        display_name=item["display_name"],
        lat=float(item["lat"]),
        lon=float(item["lon"]),
    )


async def search(query: str, limit: int = 8) -> list[GeocodeResult]:
    key = "q:" + query.strip().lower()
    if key in _cache:
        return _cache[key]
    data = await _nominatim("search", {"q": query, "limit": limit})
    return _remember(key, [_to_result(item) for item in data])


async def reverse(lat: float, lon: float) -> GeocodeResult | None:
    """Lugar más cercano a unas coordenadas (el pin del mapa); None si no hay
    nada por ahí (alta mar). Se redondea a ~10 m para que dos toques casi en
    el mismo sitio compartan caché."""
    key = f"r:{lat:.4f},{lon:.4f}"
    if key in _cache:
        return _cache[key]
    data = await _nominatim("reverse", {"lat": lat, "lon": lon})
    # Nominatim responde 200 con {"error": "Unable to geocode"} si no hay nada
    result = _to_result(data) if isinstance(data, dict) and "display_name" in data else None
    return _remember(key, result)
