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
_search_cache: dict[str, list["ImageResult"]] = {}


class CountryImage(BaseModel):
    image_url: str | None


class ImageResult(BaseModel):
    title: str
    thumb_url: str
    image_url: str


@router.get("/image-search", response_model=list[ImageResult])
async def image_search(q: str = Query(min_length=2, max_length=100)):
    """Busca fotos en Wikimedia Commons (sin API key) para la portada."""
    key = q.strip().lower()
    if key in _search_cache:
        return _search_cache[key]

    results: list[ImageResult] = []
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": q.strip(),
                    "gsrnamespace": 6,
                    "gsrlimit": 12,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "iiurlwidth": 480,
                },
                headers={"User-Agent": "tt-travel-app/0.1 (self-hosted)"},
            )
            resp.raise_for_status()
            pages = (resp.json().get("query") or {}).get("pages") or {}
            for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
                info = (page.get("imageinfo") or [{}])[0]
                if not info.get("url") or info.get("mime") not in (
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                ):
                    continue
                results.append(
                    ImageResult(
                        title=page.get("title", "").removeprefix("File:"),
                        thumb_url=info.get("thumburl") or info["url"],
                        image_url=info["url"],
                    )
                )
        except httpx.HTTPError:
            pass

    if len(_search_cache) > 100:
        _search_cache.pop(next(iter(_search_cache)))
    _search_cache[key] = results
    return results


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
