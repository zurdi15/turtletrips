import threading
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine

from .auth import get_current_user, require_admin
from .config import get_settings
from .db import make_engine, make_sessionmaker
from .routers import (
    admin,
    attachments,
    auth,
    backup,
    bookings,
    categories,
    checklist,
    countries,
    expenses,
    families,
    geocode,
    itinerary,
    journal,
    packing,
    places,
    rates,
    stats,
    travelers,
    trips,
    weather,
    world,
)
from .services.categories import ensure_default_categories_all

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
    # serializa export/restore de backups (una restauración a medias es fatal)
    app.state.backup_lock = threading.Lock()

    # protegidos: cualquier usuario con sesión
    for router in (
        trips.router,
        travelers.router,
        places.router,
        itinerary.router,
        bookings.router,
        expenses.router,
        attachments.router,
        journal.router,
        packing.router,
        checklist.router,
        categories.router,
        countries.router,
        geocode.router,
        rates.router,
        stats.router,
        weather.router,
        world.router,
        families.router,  # GET para todos; mutaciones con candado admin por endpoint
    ):
        app.include_router(
            router, prefix=API_PREFIX, dependencies=[Depends(get_current_user)]
        )

    # solo admin: gestión de usuarios y backup de la instancia entera
    for router in (admin.router, backup.router):
        app.include_router(
            router, prefix=API_PREFIX, dependencies=[Depends(require_admin)]
        )

    # públicos: auth (login/bootstrap/status) y el feed .ics de suscripción
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(itinerary.public_router, prefix=API_PREFIX)

    # sembrar categorías por defecto de cada familia (idempotente)
    with app.state.sessionmaker() as session:
        ensure_default_categories_all(session)

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health():
        return {"status": "ok"}

    if settings.serve_static and STATIC_DIR.is_dir():
        assets_dir = STATIC_DIR / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        @app.head("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            if full_path.startswith("api/"):
                return FileResponse(STATIC_DIR / "index.html", status_code=404)
            candidate = (STATIC_DIR / full_path).resolve()
            if (
                full_path
                and candidate.is_relative_to(STATIC_DIR)
                and candidate.is_file()
            ):
                # el service worker y el manifest nunca deben cachearse por HTTP:
                # un sw.js viejo retrasaría los deploys de la PWA
                if full_path == "sw.js":
                    return FileResponse(candidate, headers={"Cache-Control": "no-cache"})
                if full_path == "manifest.webmanifest":
                    return FileResponse(
                        candidate,
                        media_type="application/manifest+json",
                        headers={"Cache-Control": "no-cache"},
                    )
                return FileResponse(candidate)
            if full_path == "favicon.ico":
                # el favicon va inline en el HTML; sin fichero real, 404 limpio
                raise HTTPException(status_code=404)
            # el index nunca debe cachearse: referencia assets con hash que
            # cambian en cada build (index viejo = assets rotos tras desplegar)
            return FileResponse(
                STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"}
            )

    else:

        @app.get("/", include_in_schema=False)
        def dev_root():
            return HTMLResponse(
                "<h1>Turtle Trips · backend</h1>"
                "<p>Modo dev: la app se sirve en "
                "<a href='http://localhost:5173'>http://localhost:5173</a> "
                "(Vite con hot reload). Docs de la API: "
                "<a href='/api/docs'>/api/docs</a>.</p>"
            )

    return app
