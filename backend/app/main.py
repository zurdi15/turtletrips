from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine

from .config import get_settings
from .db import make_engine, make_sessionmaker
from .routers import (
    attachments,
    bookings,
    categories,
    countries,
    expenses,
    geocode,
    itinerary,
    packing,
    places,
    rates,
    travelers,
    trips,
)
from .services.categories import ensure_default_categories

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
API_PREFIX = "/api/v1"


def create_app(engine: Engine | None = None) -> FastAPI:
    settings = get_settings()
    if engine is None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        engine = make_engine(settings.db_url)

    app = FastAPI(
        title="Turtle Trips",
        description="App self-hosted de gestión de viajes",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    for router in (
        trips.router,
        travelers.router,
        places.router,
        itinerary.router,
        bookings.router,
        expenses.router,
        attachments.router,
        packing.router,
        categories.router,
        countries.router,
        geocode.router,
        rates.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    # sembrar categorías por defecto (idempotente; la tabla ya existe tras alembic/create_all)
    with app.state.sessionmaker() as session:
        ensure_default_categories(session)

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health():
        return {"status": "ok"}

    if STATIC_DIR.is_dir():
        assets_dir = STATIC_DIR / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            if full_path.startswith("api/"):
                return FileResponse(STATIC_DIR / "index.html", status_code=404)
            candidate = (STATIC_DIR / full_path).resolve()
            if (
                full_path
                and candidate.is_relative_to(STATIC_DIR)
                and candidate.is_file()
            ):
                return FileResponse(candidate)
            return FileResponse(STATIC_DIR / "index.html")

    return app
