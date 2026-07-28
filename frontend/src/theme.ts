import colors from 'tailwindcss/colors'
import type { BookingType, PlaceCategory, WorldPlaceKind } from './api/types'

// ---------------------------------------------------------------------------
// Colores de DATOS renderizados desde JS (canvas de Chart.js, divIcons de
// Leaflet, eventos de FullCalendar, paletas guardadas en DB): invariantes al
// tema, por eso son constantes TS y no CSS vars. La fuente primitiva es la
// paleta de Tailwind — la misma que usan los tokens CSS, cero drift.
// ---------------------------------------------------------------------------

/** color de viajero/categoría sin definir */
export const FALLBACK_COLOR = colors.slate[400]

export const WHITE = colors.white

export const PLACE_CATEGORY_COLORS: Record<PlaceCategory, string> = {
  city: colors.teal[700],
  town: colors.lime[500],
  sight: colors.rose[600],
  food: colors.amber[500],
  museum: colors.violet[500],
  nature: colors.green[600],
  viewpoint: colors.sky[500],
  shopping: colors.pink[500],
  lodging: colors.violet[600],
  other: colors.slate[500],
}

/** paleta para categorías y viajeros (elección en settings / alta rápida) */
export const CATEGORY_PALETTE = [
  colors.amber[500],
  colors.sky[500],
  colors.violet[500],
  colors.green[600],
  colors.rose[600],
  colors.pink[500],
  colors.orange[500],
  colors.indigo[500],
  colors.teal[700],
  colors.lime[500],
  colors.slate[500],
  colors.slate[400],
]

export const MEMBER_COLORS = [
  colors.sky[500],
  colors.amber[500],
  colors.green[600],
  colors.rose[600],
  colors.violet[500],
  colors.pink[500],
  colors.slate[500],
]

/** marcadores del mapa mundial por tipo de lugar */
export const KIND_COLORS: Record<WorldPlaceKind, string> = {
  country: colors.amber[500],
  region: colors.emerald[600],
  city: colors.sky[500],
  place: colors.rose[600],
}

/**
 * Relleno de países y regiones del mapa mundial. Los polígonos los pinta
 * Leaflet desde JS, así que el color vive aquí y no en los tokens CSS; el par
 * claro/oscuro se elige con `isDark` (los basemaps de CARTO son muy distintos).
 */
export const WORLD_CHOROPLETH = {
  fill: colors.emerald[500],
  fillDark: colors.emerald[400],
  stroke: colors.emerald[700],
  strokeDark: colors.emerald[300],
  /** países sin visitar: solo un borde tenue, sin relleno */
  idleStroke: colors.slate[400],
  idleStrokeDark: colors.slate[500],
  /** división interna sin marcar: un punto más oscura que la de países, o se
   *  pierde sobre el beige de la cartografía */
  regionStroke: colors.slate[500],
  regionStrokeDark: colors.slate[400],
  /** territorios sin código ISO (Kosovo, Somalilandia) o fuera de la app */
  noData: colors.slate[300],
  noDataDark: colors.slate[600],
}

/** marcadores de reservas (mapa del viaje y eventos del calendario) */
export const BOOKING_MARKER_COLORS: Partial<Record<BookingType, string>> & {
  transport: string
  fallback: string
} = {
  hotel: colors.violet[600],
  activity: colors.sky[500],
  car_rental: colors.slate[500],
  transport: colors.sky[600],
  fallback: colors.slate[500],
}

/** eventos all-day de items multi-día en el calendario */
export const ALLDAY_EVENT_COLOR = colors.teal[700]

/** línea de ruta del itinerario en el mapa del viaje */
export const ROUTE_COLOR = colors.emerald[500]

/** países estrenados en las estadísticas anuales (vs. repetidos = FALLBACK_COLOR) */
export const STATS_NEW_COLOR = colors.emerald[500]

/** serie temporal de la vista de gráficos de gastos */
export const CHART_LINE_COLOR = colors.sky[500]
