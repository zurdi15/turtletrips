from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas.misc import RateRead
from ..services.rates import RateUnavailableError, get_rate

router = APIRouter(tags=["rates"])


@router.get("/rates", response_model=RateRead)
async def read_rate(
    base: str = Query(alias="from", min_length=3, max_length=3),
    quote: str = Query(alias="to", min_length=3, max_length=3),
    day: date_type | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
):
    day = day or date_type.today()
    try:
        rate, source = await get_rate(db, base, quote, day)
    except RateUnavailableError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RateRead(base=base.upper(), quote=quote.upper(), day=day, rate=float(rate), source=source)
