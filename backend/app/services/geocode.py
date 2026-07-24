import asyncio
import time

import httpx

from ..config import get_settings
from ..schemas.misc import GeocodeResult

_USER_AGENT = "tt-travel-app/0.1 (self-hosted; https://github.com/zurdi)"
_MIN_INTERVAL = 1.1  # política de uso de Nominatim: máx 1 req/s
_CACHE_MAX = 200

_lock = asyncio.Lock()
_last_request = 0.0
_cache: dict[str, list[GeocodeResult]] = {}


class GeocodeError(Exception):
    pass


async def search(query: str, limit: int = 8) -> list[GeocodeResult]:
    key = query.strip().lower()
    if key in _cache:
        return _cache[key]

    settings = get_settings()
    global _last_request
    async with _lock:
        wait = _MIN_INTERVAL - (time.monotonic() - _last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.nominatim_url}/search",
                    # accept-language=es: nombres en español (si no, Nominatim
                    # devuelve el idioma local: 臺北 en vez de Taipéi)
                    params={
                        "q": query,
                        "format": "jsonv2",
                        "limit": limit,
                        "accept-language": "es",
                    },
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            raise GeocodeError(f"Error consultando Nominatim: {exc}") from exc
        finally:
            _last_request = time.monotonic()

    results = [
        GeocodeResult(
            display_name=item["display_name"],
            lat=float(item["lat"]),
            lon=float(item["lon"]),
        )
        for item in data
    ]
    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[key] = results
    return results
