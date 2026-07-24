# 🐢 Turtle Trips · gestión de viajes self-hosted

Hermana de Traveler Turtles. El repo y la imagen se llaman `tt` — las siglas de ambas.

App self-hosted single-user para planificar viajes y controlar sus gastos. Sustituye el Excel de gastos y herramientas tipo Wanderlog:

- **Viajes** con países (multi, con bandera e imagen automática de Wikivoyage o foto propia), fechas, estado automático, presupuesto y viajeros globales reutilizables ("quién pagó", sin cuentas de usuario).
- **Sitios que ver** con categorías (ciudad, pueblo, monumento…), prioridad, geocoding (Nominatim/OpenStreetMap) y mapa Leaflet.
- **Itinerario** día a día con drag & drop, estancias de varios días y vista de calendario (FullCalendar).
- **Reservas** (hotel, vuelo, tren, actividad…) con códigos de confirmación, PDFs adjuntos y creación de gasto en un clic.
- **Gastos multi-moneda** con tipo de cambio del BCE (frankfurter) cacheado y editable, categorías configurables, resumen por categoría/día/pagador, gráficas e **import/export CSV** para migrar desde Excel.
- **Maleta** tipo checklist con categorías, enlaces de compra y **plantillas reutilizables** entre viajes.
- **Ajustes**: categorías de gastos y maleta personalizables, gestión de viajeros.

Stack: Vue 3 + PrimeVue (frontend), FastAPI + SQLite (backend), todo en **una única imagen Docker** (el backend sirve la SPA compilada). Sin autenticación: pensada para correr detrás de tu reverse proxy o VPN.

## Arranque rápido

```bash
docker compose up --build -d
# → http://localhost:8000
```

Los datos (SQLite + ficheros subidos) viven en el volumen `tt_data`, montado en `/data`.

## Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `TT_DATA_DIR` | `/data` | Directorio de datos (DB en `app.db`, ficheros en `uploads/`) |
| `TT_DEFAULT_CURRENCY` | `EUR` | Moneda base por defecto para viajes nuevos |
| `TT_NOMINATIM_URL` | `https://nominatim.openstreetmap.org` | Servidor de geocoding (puedes apuntar a uno propio) |
| `TT_RATES_URL` | `https://api.frankfurter.dev/v1` | API de tipos de cambio (self-hosteable) |

## Backup

Todo el estado está en `/data`: copia el volumen y listo.

```bash
docker run --rm -v tt_tt_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/tt-backup.tar.gz -C /data .
```

## Importar tus gastos desde Excel

1. Exporta tu hoja a CSV (separador `,` o `;`).
2. En el viaje → pestaña **Gastos** → **Importar CSV**.
3. Se reconocen cabeceras en español o inglés (`fecha/day`, `concepto/description`, `importe/amount`, `categoría`, `moneda`, `tasa`, `pagador`, `notas`), fechas `dd/mm/aaaa` e importes `1.234,56`.
4. Verás una previsualización con los errores fila a fila; no se importa nada hasta confirmar.

Si una fila usa una moneda distinta a la del viaje necesita columna `tasa` (tipo de cambio a moneda base); si falta, la fila se marca como error.

## Desarrollo

Requisitos: [uv](https://docs.astral.sh/uv/) (`sudo pacman -S uv` o `curl -LsSf https://astral.sh/uv/install.sh | sh`) y Node 22+.

```bash
./dev.sh          # backend :8000 + frontend :5173, ambos con hot reload
./dev.sh back     # solo backend (uvicorn --reload)
./dev.sh front    # solo frontend (Vite HMR)
```

La primera ejecución crea el venv e instala `node_modules` automáticamente. Abre
`http://localhost:5173` (Vite proxya `/api` al backend); los datos de dev van a `./data/`.

- API docs: `http://localhost:8000/api/docs`
- Tests backend: `cd backend && uv run pytest`
- Typecheck frontend: `cd frontend && npm run typecheck`
- Nueva migración tras cambiar modelos: `cd backend && uv run alembic revision --autogenerate -m "..."`

## Estructura

```
frontend/   Vue 3 + Vite + TS + PrimeVue + Pinia (SPA)
backend/    FastAPI + SQLAlchemy 2 + Alembic (API REST + sirve la SPA)
Dockerfile  multi-stage: build del front → runtime python
```
