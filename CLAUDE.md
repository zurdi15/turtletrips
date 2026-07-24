# Turtle Trips (tt) — app self-hosted de gestión de viajes

Single-user, sin auth (se delega en reverse proxy). Vue 3 + FastAPI + SQLite, una sola imagen Docker donde FastAPI sirve la SPA compilada desde `backend/static/`. UI en español.

## Comandos

```bash
./dev.sh             # dev con hot reload — trabaja SIEMPRE en http://localhost:5173
                     # (`back`/`front` para solo uno; `--open` abre el navegador)
                     # en dev :8000 solo sirve la API (TT_SERVE_STATIC=0): nada de builds

# Backend (desde backend/, dependencias gestionadas con uv + uv.lock)
uv run pytest                                      # tests
TT_DATA_DIR=../data uv run uvicorn app.asgi:app --reload
TT_DATA_DIR=../data uv run alembic upgrade head
uv run alembic revision --autogenerate -m "…"      # tras cambiar models.py

# Frontend (desde frontend/)
npm run dev          # dev server :5173 con proxy /api → :8000
npm run build        # → dist/ (incluye sw.js + manifest de la PWA)
npm run typecheck    # vue-tsc
npm test             # vitest (lógica pura: utils/ y composables/)

# Todo junto
docker compose up --build
```

## Arquitectura

- `backend/app/models.py` — todas las entidades SQLAlchemy. Trip → places/itinerary/bookings/expenses/attachments/packing_items con cascade delete. `Trip.status` es una property derivada de fechas salvo `status_override`. `Trip.countries` es JSON con códigos ISO alpha-2; `cover_image` es la portada subida (endpoints `/trips/{id}/cover`).
- **Viajeros** (`Traveler`) son globales y se asocian a viajes vía tabla `trip_travelers` (M2M). `Expense.paid_by_id` apunta a travelers.
- **Reparto de gastos** (Splitwise-like): `Expense.split_mode` (equal|amount|percent) + tabla `expense_shares` (`value` NULL en equal). Sin filas = reparto implícito a partes iguales entre los viajeros ACTUALES del viaje (sin backfill). Cálculo en `services/balances.py` (mayor resto a céntimos sobre `amount_base`, liquidación greedy) expuesto en `GET /trips/{id}/balances`; UI en la vista "Saldos" de la pestaña Gastos (`BalancesPanel.vue` + `ExpenseSplitEditor.vue` en el form; lógica espejo en `composables/useSplit.ts`). El CSV no importa/exporta repartos (quedan "entre todos").
- **Fondo común**: `Expense.paid_by_common` marca gastos pagados del monedero común (pagador virtual, NO un Traveler). Excluyente con `paid_by_id` (el router lo garantiza: marcar uno desmarca el otro). Cuentan en totales/summary pero NO en balances (contadores `common_*` en TripBalances). En la UI es la opción "Fondo común" (cartera ámbar) del selector de pagador (form, filtros y edición en bloque).
- **Liquidaciones**: tabla `settlements` (trip, from→to, amount_base) registra pagos entre viajeros ("Liquidar" en la vista Saldos; se pueden deshacer). Los saldos las descuentan de los netos y las sugerencias se recalculan. `Trip.debts_settled` (property, expuesta en TripRead → pill "Saldado" en tarjetas y cabecera) = hay liquidaciones y los netos quedan a cero; corta en `settlements` vacío para no cargar gastos en el listado. Al añadir ciudad/sitio al mapa mundial, `ensure_country_entry` arrastra su país (respetando hidden).
- **Categorías** de gastos y maleta viven en la tabla `categories` (kind expense|packing), configurables desde /settings. Los defaults se siembran en el arranque (`services/categories.ensure_default_categories`, idempotente). `Expense.category` es un string (no FK): renombrar una categoría propaga el cambio; borrarla deja el nombre huérfano.
- **Maleta**: una por viajero y viaje (`PackingItem.traveler_id`; NULL = maleta común) + `PackingTemplate`/`PackingTemplateItem` como plantillas reutilizables. Aplicar una plantilla COPIA los elementos a la maleta de ese viajero (overrides libres sin tocar la plantilla) y persiste la selección en `packing_selections` (trip, traveler → template); sync-from-trip acepta `?traveler_id=` para guardar los overrides de vuelta. Las plantillas se editan también directamente en /packing (CRUD de items).
- Navegación principal: Viajes (/), Mapa (/map), Maletas (/packing), Viajeros (/travelers), Ajustes (/settings: categorías y copia de seguridad). Rutas SIEMPRE en inglés aunque la UI sea en español.
- **Mapa mundial** (`WorldPlace`, /world-places): diario global — países (marcador de bandera emoji), ciudades y sitios con nota libre. Se auto-rellena en cada GET (`services/worldmap.sync_world_places`, idempotente): países de viajes TERMINADOS, sitios visitados y sitios enlazados a gastos (auto=True, origin=nombre del viaje; borrar una entrada auto la marca hidden para que no reviva). El nombre de países auto es el código ISO; el front lo traduce.
- Geocoding con `accept-language=es,en` (español donde hay traducción, inglés romanizado como fallback: "Taipéi", no 臺北; "Hanamichi-dori", no 花道通り). Tiles de CARTO sin API key (voyager en claro, dark_all en oscuro) vía `useMapTiles`; el backend pina Python 3.12 con `.python-version` (uv) para sobrevivir a los upgrades de Python del sistema.
- `ItineraryItem.end_day` permite estancias de varios días (agenda muestra filas "sigue"; el calendario un evento all-day multi-día).
- **Reserva ↔ sitio ↔ gasto**: al crear/editar una reserva con coordenadas, `services/booking_place.ensure_booking_place` la enlaza (`Booking.place_id`) al sitio más cercano — POI ≤300 m, town ≤5 km, city ≤15 km (gana el de menor distancia/radio) — o crea uno nuevo (categoría `lodging` para hoteles); cambiar las coords re-enlaza. Una reserva con coste crea su gasto AUTOMÁTICAMENTE al crearla o al estrenar coste (`_auto_create_expense`, best-effort: sin tasa disponible se salta y queda el endpoint manual `create-expense`, que sigue siendo la vía de regeneración tras borrar el gasto y rechaza duplicados con 400). La reserva lleva pagador propio (`Booking.paid_by_id`/`paid_by_common`, excluyentes como en Expense, selector reutilizable `PayerSelect.vue`) que el gasto generado hereda. Reserva y gasto generado quedan sincronizados en ambos sentidos: editar la reserva espeja título/fecha/sitio/importe/moneda/pagador en el gasto (`_sync_linked_expense`, rescala repartos por importes), y editar el gasto devuelve importe/moneda/pagador a la reserva; mover el día del gasto desplaza entrada Y salida de la reserva conservando duración y horas (el título manda SIEMPRE desde la reserva; el gasto muestra el día de entrada/salida inicial). En la agenda del itinerario TODAS las reservas con fecha salen automáticamente como secciones con cabecera: transportes (azul, `mdi-plane-train`, día de salida), resto de reservas (ámbar, actividades/coche/otros) y alojamiento (violeta, `mdi-bed`, check-in → noche antes del check-out, al pie del día); todas enlazan a la pestaña Reservas (`?booking=id` la resalta). En el calendario los hoteles son bandas all-day violetas.
- `/country-image?q=` proxya el banner de Wikivoyage (fallback Wikipedia) para heros/cards; el front cachea por código de país (`useCountryImage`).
- `backend/app/routers/` — REST bajo `/api/v1`. Recursos anidados para listar/crear (`/trips/{id}/expenses`), rutas planas para mutar (`/expenses/{id}`).
- Gastos multi-moneda: `exchange_rate` se snapshotea en cada gasto; `amount_base = amount * rate` se guarda calculado. Tasas: cache en DB (`exchange_rate_cache`) → frankfurter.app. Todo en `services/rates.py` (`get_rate`, `resolve_rate`, `to_base`).
- **Backup/restore** (`services/backup.py`, `/api/v1/backup/export|restore`, UI en Ajustes): ZIP con snapshot de la DB (API backup de sqlite3, seguro con WAL — NUNCA copiar el fichero a pelo) + manifest + uploads. Restore valida (traversal, zip-bomb, `quick_check`, revisión alembic conocida), aparta lo anterior en `data_dir/pre-restore/`, corre `alembic upgrade head` y recrea `app.state.engine` en caliente; `app.state.backup_lock` serializa.
- **Export .ics** (`services/ics.py`, `GET /trips/{id}/calendar.ics?bookings=`): VEVENTs generados a mano (escape+folding 75 octetos+CRLF, UIDs estables, DTEND exclusivo en all-day, horas flotantes sin TZID). Reservas transporte → "Vuelo: MAD → Tokio"; las enlazadas a items no se duplican.
- **PWA** (`vite-plugin-pwa` en vite.config.ts): autoUpdate, precache del shell, NetworkFirst para GETs de la API (excluye backup/descargas/ics/csv/covers), CacheFirst para tiles, SWR para imágenes. El catch-all sirve `sw.js` y `manifest.webmanifest` con `Cache-Control: no-cache` (crítico para deploys). Iconos en `frontend/public/` generados desde `favicon.svg` (el maskable es la variante full-bleed).
- CSV import/export en `services/csv_io.py`: cabeceras ES/EN, importes `1.234,56`, fechas `dd/mm/yyyy`, dry-run con preview. El pagador se crea como TripMember si no existe.
- Ficheros en `{TT_DATA_DIR}/uploads/{trip_id}/{uuid}` (`services/files.py`); la DB guarda solo metadatos. Borrar viaje borra su carpeta.
- Geocoding: proxy a Nominatim con throttle 1 req/s (`services/geocode.py`).
- `app/main.py` `create_app()` acepta un engine para tests; `app/asgi.py` es el entrypoint de uvicorn. El catch-all no-`/api` sirve `static/index.html` (SPA history mode) salvo con `TT_SERVE_STATIC=0` (dev), que muestra una página informativa apuntando a :5173.
- Routers: helpers compartidos en `routers/common.py` (`get_or_404`, `apply_updates`, `ensure_in_trip`, `save_new`/`save_updates`/`delete_by_id`, `ascii_filename`) — el CRUD clónico va SIEMPRE con estos helpers; los `list_*` y casos especiales (world delete auto/hidden, expenses moneda) se quedan explícitos.
- Frontend: stores Pinia por dominio compuestos sobre `stores/tripResource.ts` (`useTripResource`: items/tripId/loading + load/create/update/remove); tipos de la API en `src/api/types.ts` (mantener en sync con los schemas Pydantic), incluidos los `*Input` derivados de las entidades; labels/colores en español en `src/constants.ts`. Lógica pura testeable en `src/utils/` (expenses, worldGrouping) y composables (`useExpenseFilters`, `useExpenseCharts`, `useSplit`); las vistas grandes son orquestadores de componentes (`components/expenses/`, `components/world/`).
- **Iconos**: sin emojis en la UI (única excepción: banderas de país). PrimeIcons para lo genérico y `@mdi/font` (`mdi mdi-*`) donde PrimeIcons no llega — viajes: cama, avión, tren, ferry… (`BOOKING_TYPE_ICONS`, categoría `lodging`). En el calendario los iconos entran vía `eventContent` (extendedProps.icon).
- **Animaciones** (sistema `tt-*` en `style.css`): solo se anima la ENTRADA (la salida es instantánea) y solo con transform/opacity (corren en el compositor, no se congelan con el hilo principal ocupado — por eso las tabs activas NO llevan transición de color). Clases: `tt-anim-rise` (montaje de vistas/tabs, cae por fallthrough en `<router-view class=…>`), `tt-stagger` (cascada de hijas en listas), `tt-lift` (hover de tarjetas clicables, incluye colores), `tt-pop-in` (pills/banners), `tt-bar` (barras de progreso), transiciones Vue nombradas `tt-fade`/`tt-rise`/`tt-list` (TransitionGroup: el contenedor necesita `relative`). Todo respeta `prefers-reduced-motion`. Números que cuentan: `useAnimatedNumber` (composable con test).

## Convenciones

- Tests backend: TestClient + SQLite en memoria (`tests/conftest.py`); `TT_DATA_DIR` se fija a un tmp ANTES de importar la app (get_settings usa lru_cache). Tests frontend: Vitest sin DOM (`*.test.ts` junto al código, solo lógica pura).
- Fechas naive (sin timezone) en toda la app: `toIsoDate()` en el front evita sorpresas de zona horaria con `DatePicker`.
- Dinero: `Decimal` en backend, importes serializados como float en las respuestas.
