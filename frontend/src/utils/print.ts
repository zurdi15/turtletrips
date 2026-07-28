// Qué lleva la versión imprimible y en qué orden. Todo pura decisión: el
// documento se limita a pintar lo que decide esto.
//
// La firma ya contempla el álbum de fotos (fase 7): `layout` y la lista de
// secciones viajan desde el principio para no rehacer el documento entero
// cuando llegue.

export type PrintLayout = 'report' | 'album'
export type PrintSection = 'cover' | 'itinerary' | 'map' | 'places' | 'bookings' | 'expenses'

export interface PrintOptions {
  layout: PrintLayout
  map: boolean
  notes: boolean
  expenses: boolean
}

/** Lo que hay realmente en el viaje: una sección vacía no se imprime */
export interface PrintContent {
  days: number
  places: number
  locatedPlaces: number
  bookings: number
  hasExpenses: boolean
}

const ORDER: PrintSection[] = ['cover', 'itinerary', 'map', 'places', 'bookings', 'expenses']

function truthy(value: unknown, fallback: boolean): boolean {
  if (value === undefined || value === null || value === '') return fallback
  return value === '1' || value === 'true' || value === true
}

/**
 * Opciones desde la query (`?map=0&expenses=1`). `allowExpenses` es un CANDADO,
 * no un valor por defecto: en el enlace público no hay dinero que enseñar por
 * mucho que alguien escriba `?expenses=1` en la barra del navegador.
 */
export function resolvePrintOptions(
  query: Record<string, unknown>,
  { allowExpenses }: { allowExpenses: boolean },
): PrintOptions {
  return {
    layout: query.layout === 'album' ? 'album' : 'report',
    map: truthy(query.map, true),
    notes: truthy(query.notes, true),
    expenses: allowExpenses && truthy(query.expenses, true),
  }
}

/** Secciones a pintar, en orden y sin las que no tienen contenido */
export function printSections(options: PrintOptions, content: PrintContent): PrintSection[] {
  const wanted = new Set<PrintSection>(['cover'])
  if (content.days) wanted.add('itinerary')
  // el mapa necesita al menos un sitio LOCALIZADO; el listado, cualquiera
  if (options.map && content.locatedPlaces) wanted.add('map')
  if (content.places) wanted.add('places')
  if (content.bookings) wanted.add('bookings')
  if (options.expenses && content.hasExpenses) wanted.add('expenses')
  return ORDER.filter((section) => wanted.has(section))
}

/**
 * Título del documento: el navegador lo usa como nombre del PDF al "Guardar
 * como PDF", así que sale "Japón 2026 — 2026-02-07.pdf" y no "localhost".
 */
export function printDocumentTitle(name: string, startDate: string | null): string {
  return startDate ? `${name} — ${startDate}` : name
}
