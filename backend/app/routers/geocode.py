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
