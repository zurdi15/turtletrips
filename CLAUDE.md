# Turtle Trips (tt) — app self-hosted de gestión de viajes

Single-user, sin auth (se delega en reverse proxy). Vue 3 + FastAPI + SQLite, una sola imagen Docker donde FastAPI sirve la SPA compilada desde `backend/static/`. UI en español.

## Comandos

```bash
./dev.sh             # dev con hot reload: backend :8000 + frontend :5173 (o `back`/`front`)

# Backend (desde backend/, dependencias gestionadas con uv + uv.lock)
uv run pytest                                      # tests
TT_DATA_DIR=../data uv run uvicorn app.asgi:app --reload
TT_DATA_DIR=../data uv run alembic upgrade head
uv run alembic revision --autogenerate -m "…"      # tras cambiar models.py

# Frontend (desde frontend/)
npm run dev          # dev server :5173 con proxy /api → :8000
npm run build        # → dist/
npm run typecheck    # vue-tsc

# Todo junto
docker compose up --build
```

## Arquitectura

- `backend/app/models.py` — todas las entidades SQLAlchemy. Trip → places/itinerary/bookings/expenses/attachments/packing_items con cascade delete. `Trip.status` es una property derivada de fechas salvo `status_override`. `Trip.countries` es JSON con códigos ISO alpha-2; `cover_image` es la portada subida (endpoints `/trips/{id}/cover`).
- **Viajeros** (`Traveler`) son globales y se asocian a viajes vía tabla `trip_travelers` (M2M). `Expense.paid_by_id` apunta a travelers.
- **Categorías** de gastos y maleta viven en la tabla `categories` (kind expense|packing), configurables desde /settings. Los defaults se siembran en el arranque (`services/categories.ensure_default_categories`, idempotente). `Expense.category` es un string (no FK): renombrar una categoría propaga el cambio; borrarla deja el nombre huérfano.
- **Maleta**: una por viajero y viaje (`PackingItem.traveler_id`; NULL = maleta común) + `PackingTemplate`/`PackingTemplateItem` como plantillas reutilizables. Aplicar una plantilla COPIA los elementos a la maleta de ese viajero (overrides libres sin tocar la plantilla) y persiste la selección en `packing_selections` (trip, traveler → template); sync-from-trip acepta `?traveler_id=` para guardar los overrides de vuelta. Las plantillas se editan también directamente en /maletas (CRUD de items).
- Navegación principal: Viajes (/), Maletas (/maletas), Viajeros (/viajeros), Ajustes (/settings, solo categorías).
- `ItineraryItem.end_day` permite estancias de varios días (agenda muestra filas "sigue"; el calendario un evento all-day multi-día).
- `/country-image?q=` proxya el banner de Wikivoyage (fallback Wikipedia) para heros/cards; el front cachea por código de país (`useCountryImage`).
- `backend/app/routers/` — REST bajo `/api/v1`. Recursos anidados para listar/crear (`/trips/{id}/expenses`), rutas planas para mutar (`/expenses/{id}`).
- Gastos multi-moneda: `exchange_rate` se snapshotea en cada gasto; `amount_base = amount * rate` se guarda calculado. Tasas: cache en DB (`exchange_rate_cache`) → frankfurter.app. La resolución está en `services/rates.py` + `resolve_rate` en `routers/expenses.py`.
- CSV import/export en `services/csv_io.py`: cabeceras ES/EN, importes `1.234,56`, fechas `dd/mm/yyyy`, dry-run con preview. El pagador se crea como TripMember si no existe.
- Ficheros en `{TT_DATA_DIR}/uploads/{trip_id}/{uuid}` (`services/files.py`); la DB guarda solo metadatos. Borrar viaje borra su carpeta.
- Geocoding: proxy a Nominatim con throttle 1 req/s (`services/geocode.py`).
- `app/main.py` `create_app()` acepta un engine para tests; `app/asgi.py` es el entrypoint de uvicorn. El catch-all no-`/api` sirve `static/index.html` (SPA history mode).
- Frontend: stores Pinia por dominio (cada uno con `load(tripId)`); tipos de la API a mano en `src/api/types.ts` (mantener en sync con los schemas Pydantic); labels/colores en español en `src/constants.ts`.

## Convenciones

- Tests backend: TestClient + SQLite en memoria (`tests/conftest.py`); `TT_DATA_DIR` se fija a un tmp ANTES de importar la app (get_settings usa lru_cache).
- Fechas naive (sin timezone) en toda la app: `toIsoDate()` en el front evita sorpresas de zona horaria con `DatePicker`.
- Dinero: `Decimal` en backend, importes serializados como float en las respuestas.
