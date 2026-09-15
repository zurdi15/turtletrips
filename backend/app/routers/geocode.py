from fastapi import APIRouter, HTTPException, Query

from ..schemas.misc import GeocodeResult
from ..services import geocode as geocode_service

router = APIRouter(tags=["geocode"])


@router.get("/geocode", response_model=list[GeocodeResult])
async def geocode(q: str = Query(min_length=2, max_length=200)):
    try:
        return await geocode_service.search(q)
    except geocode_service.GeocodeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/geocode/reverse", response_model=GeocodeResult)
async def reverse_geocode(lat: float = Query(ge=-90, le=90), lon: float = Query(ge=-180, le=180)):
    """El lugar más cercano a un punto fijado a mano en el mapa."""
    try:
        result = await geocode_service.reverse(lat, lon)
    except geocode_service.GeocodeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Sin resultados para ese punto")
    return result
