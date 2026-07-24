from urllib.parse import quote

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["countries"])

# Wikivoyage tiene banners panorámicos perfectos como hero; Wikipedia como fallback
_SOURCES = [
    "https://en.wikivoyage.org/api/rest_v1/page/summary/",
    "https://es.wikipedia.org/api/rest_v1/page/summary/",
]

_cache: dict[str, str | None] = {}


class CountryImage(BaseModel):
    image_url: str | None


@router.get("/country-image", response_model=CountryImage)
async def country_image(q: str = Query(min_length=2, max_length=100)):
    key = q.strip().lower()
    if key in _cache:
        return CountryImage(image_url=_cache[key])

    image: str | None = None
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        for base in _SOURCES:
            try:
                resp = await client.get(
                    base + quote(q.strip().replace(" ", "_")),
                    headers={"User-Agent": "tt-travel-app/0.1 (self-hosted)"},
                )
                if resp.status_code != 200:
                    continue
                data = resp.json()
                image = (data.get("originalimage") or {}).get("source") or (
                    data.get("thumbnail") or {}
                ).get("source")
                if image:
                    break
            except httpx.HTTPError:
                continue

    if len(_cache) > 300:
        _cache.pop(next(iter(_cache)))
    _cache[key] = image
    return CountryImage(image_url=image)
