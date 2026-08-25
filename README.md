<p align="center">
  <img src="docs/assets/logo.svg" width="96" alt="Turtle Trips logo" />
</p>

<h1 align="center">Turtle Trips</h1>

<p align="center">
  Plan your trips, split the expenses and take the journal with you.
</p>

<p align="center">
  <a href="https://github.com/zurdi15/turtletrips/releases"><img src="https://img.shields.io/github/v/release/zurdi15/turtletrips?sort=semver" alt="Release" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zurdi15/turtletrips" alt="License" /></a>
</p>

Turtle Trips is a **self-hosted, multi-user** app to plan your trips: manage your itinerary, bookings, expenses and the luggage with your data on your own server. Every user is a traveler (travelers without an account — kids, guests — also exist), users group into **families** with their own world map and categories, and a trip is shared by everyone traveling on it. It ships as a single Docker image (FastAPI + SQLite + a Vue PWA).

## Features

- **Trips** — countries (multiple, with flag and automatic cover from Wikivoyage or your own photo), dates, automatic status and budget.
- **Places to see** — categories (city, sight, nature…), priority, geocoding and a map.
- **Day-by-day itinerary** — drag & drop, multi-day stays and a calendar view; dated bookings (flights, hotels, activities) show up in the agenda on their own.
- **Bookings** — hotel, flight, train, activity… with confirmation code, flight number and attachments. A booking with a cost **creates its expense automatically** and both stay in sync in either direction; it also links itself to the nearest place on the map.
- **.ics calendar** — export the itinerary or **subscribe by URL** from Google Calendar to keep it always up to date.
- **Multi-currency expenses** — cached, editable ECB exchange rates (frankfurter), configurable categories, groupings, charts and bulk editing.
- **Splitwise-style splitting** — equal parts, amounts or percentages per expense, plus a **common fund** as a virtual payer for shared money.
- **Balances and settlements** — per-traveler balances, settlement suggestions and recorded payments until the trip shows "Settled".
- **CSV import/export** — migrate from Excel, with Spanish/English headers and a dry-run preview.
- **Packing lists** — one per traveler (plus a shared one) with progress and categories. Families pack together: everyone from your family on the trip can edit each other's bags, while other families' bags stay private.
- **Packing templates** — reusable, per traveler: visible to your whole family and appliable to any bag you can edit; each template is edited only by its owner (kids' templates are managed by the whole family).
- **Multi-user with login** — session cookies with no secrets to configure, per-user theme and language stored in the database, and a profile page (name, color, photo, password). The admin-only Travelers page is the single hub for people: travelers grouped by family with everything inline — manage families, move travelers and handle accounts (a new account can claim an existing virtual traveler).
- **World map** — a per-family journal of visited countries, cities and places that **fills itself in** from finished trips where the family took part, and lets you add everything from before the app by hand.
- **ES/EN** — full Spanish and English UI, switchable from Settings.
- **PWA** — installable, with app-shell precaching and basic offline support.
- **Backups** — a ZIP (database + files) from the app itself, with validated hot restore.

## Screenshots

| Desktop | Mobile |
| :---: | :---: |
| <img src="docs/screenshots/home.png" alt="trip list" width="720"> | <img src="docs/screenshots/mobile-home.png" alt="mobile view" width="240"> |

| Trip overview | Multi-currency expenses |
| :---: | :---: |
| <img src="docs/screenshots/trip-overview-light.png" alt="trip overview"> | <img src="docs/screenshots/expenses-light.png" alt="expenses"> |

| Itinerary | World map |
| :---: | :---: |
| <img src="docs/screenshots/itinerary.png" alt="itinerary"> | <img src="docs/screenshots/world-map.png" alt="world map"> |

<details>
  <summary>More screenshots</summary>

| Places to see | Packing list |
| :---: | :---: |
| <img src="docs/screenshots/places-light.png" alt="places"> | <img src="docs/screenshots/packing-light.png" alt="packing"> |

</details>

## Quick start

```yaml
services:
  turtletrips:
    image: ghcr.io/zurdi15/turtletrips:latest
    ports: ["8000:8000"]
    volumes: ["./data:/data"]
    restart: unless-stopped
```

```
docker compose up -d
```

Open `http://localhost:8000`. On first run the login screen offers to create the **admin account**; the admin then creates the rest of the accounts and manages families right from the Travelers page (each account is linked to a traveler, new or an existing virtual one). The commented compose file is [examples/docker-compose.yml](examples/docker-compose.yml).

## Configuration

All settings are environment variables with the `TT_` prefix.

| Variable | Default | Description |
|---|---|---|
| `TT_DATA_DIR` | `/data` | Data directory (DB at `app.db`, files under `uploads/`) |
| `TT_DEFAULT_CURRENCY` | `EUR` | Default base currency for new trips |
| `TT_NOMINATIM_URL` | `https://nominatim.openstreetmap.org` | Geocoding server (you can point it to your own) |
| `TT_RATES_URL` | `https://api.frankfurter.dev/v1` | Exchange-rate API (self-hostable) |
| `TT_COOKIE_SECURE` | `false` | Mark the session cookie as `Secure` (enable behind HTTPS) |
| `TT_SESSION_TTL_DAYS` | `30` | Session lifetime; it renews itself while the app is in use |
| `TT_PASSWORD_RESET_TTL_MINUTES` | `60` | Validity of a password-reset link |
| `TT_SERVE_STATIC` | `true` | Serve the SPA (disable only in dev) |

### Data

All data (the SQLite database at `app.db` and the uploaded files under `uploads/`) lives in `/data`: a single directory to back up. From the app, **Settings → Backup** downloads a consistent ZIP with the database and files, restorable from the same screen. By hand, copying the directory works too, but stop the container first — the database runs in WAL mode and a raw copy of a live file can be torn:

```bash
docker compose stop && tar czf tt-backup.tar.gz -C /path/to/your/data . && docker compose start
```

### Reverse proxy & authentication

The app ships with its own login (session cookie, `HttpOnly` + `SameSite=Lax`), so a reverse proxy with auth is not required. If you keep one, leave `/api/v1/calendar/*` and `/api/v1/public/*` exempt: the calendar subscription and the read-only share links are public feeds with their own tokens. Set `TT_COOKIE_SECURE=true` when serving over HTTPS. There is no outgoing mail: password-reset links are printed in the server logs (`docker logs`) for the admin to hand out.

> [!NOTE]
> Locked out of the only admin account? Reset it by hand against the volume: `sqlite3 /data/app.db "DELETE FROM users; DELETE FROM sessions;"` — the next visit shows the admin bootstrap screen again (travelers, trips and data are untouched).

## Import your expenses from Excel

1. Export your sheet to CSV (`,` or `;` separator).
2. In the trip → **Expenses** tab → **Import CSV**.
3. Headers are recognized in Spanish or English (`fecha/day`, `concepto/description`, `importe/amount`, `categoría/category`, `moneda/currency`, `tasa/rate`, `pagador/payer`, `notas/notes`), along with `dd/mm/yyyy` dates and `1.234,56` amounts.
4. You get a row-by-row preview with any errors; nothing is imported until you confirm.

If a row uses a currency other than the trip's, it needs a `rate` column (exchange rate to the base currency); if missing, the row is flagged as an error.

## Development

Requirements: [uv](https://docs.astral.sh/uv/) and Node 22+.

```bash
./dev.sh   # backend :8000 + frontend :5173, both with hot reload
```

```
backend/    FastAPI · SQLAlchemy 2 · Alembic · SQLite (REST API + serves the SPA)
frontend/   Vue 3 · Vite · TypeScript · PrimeVue · Pinia (SPA)
Dockerfile  multi-stage: frontend build → python runtime
```

Use the app at `http://localhost:5173`; the API and its docs live at `http://localhost:8000/api/docs`. Tests: `cd backend && uv run pytest` · `cd frontend && npm test`.

## License

MIT — see [LICENSE](LICENSE).
