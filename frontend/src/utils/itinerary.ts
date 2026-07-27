import type { Booking, ItineraryItem, Place } from '../api/types'
import { BOOKING_TYPE_KEYS, isTransport } from '../constants'
import { intlLocale } from '../i18n'
import { parseIsoDate } from '../composables/useMoney'
import { addDays, daysBetween, eachDayInclusive } from './dates'

/** `t` de vue-i18n (o un stub en tests): clave + interpolación con nombre */
export type TranslateFn = (key: string, named?: Record<string, unknown>) => string

// ---------------------------------------------------------------------------
// Derivación pura de la agenda del itinerario: qué reservas aparecen en qué
// día y con qué etiquetas. Transportes el día de salida (y de llegada si es
// otro día), alojamiento del check-in a la noche previa al check-out (más el
// día del check-out), resto de reservas en su día.
// ---------------------------------------------------------------------------

/** Salida el día de inicio; si llega OTRO día (vuelo nocturno), también una
 *  entrada de "Llegada" en el día de destino. */
export interface TransportEntry {
  b: Booking
  arrival: boolean
}

function transportDt(e: TransportEntry): string {
  return e.arrival ? e.b.end_dt! : e.b.start_dt!
}

export function buildTransportsByDay(bookings: Booking[]): Map<string, TransportEntry[]> {
  const map = new Map<string, TransportEntry[]>()
  const add = (day: string, e: TransportEntry) => map.set(day, [...(map.get(day) ?? []), e])
  for (const b of bookings) {
    if (!isTransport(b.type) || !b.start_dt) continue
    add(b.start_dt.slice(0, 10), { b, arrival: false })
    if (b.end_dt && b.end_dt.slice(0, 10) > b.start_dt.slice(0, 10)) {
      add(b.end_dt.slice(0, 10), { b, arrival: true })
    }
  }
  for (const list of map.values()) {
    list.sort((a, b) => transportDt(a).localeCompare(transportDt(b)))
  }
  return map
}

/** Resto de reservas con fecha (actividades, coche, otros): en su día. */
export function buildOtherBookingsByDay(bookings: Booking[]): Map<string, Booking[]> {
  const map = new Map<string, Booking[]>()
  for (const b of bookings) {
    if (b.type === 'hotel' || isTransport(b.type) || !b.start_dt) continue
    const day = b.start_dt.slice(0, 10)
    map.set(day, [...(map.get(day) ?? []), b])
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.start_dt!.localeCompare(b.start_dt!))
  }
  return map
}

/** Noches del check-in a la víspera del check-out, más el día del check-out. */
export function buildLodgingByDay(bookings: Booking[]): Map<string, Booking[]> {
  const map = new Map<string, Booking[]>()
  const add = (day: string, b: Booking) => map.set(day, [...(map.get(day) ?? []), b])
  for (const b of bookings) {
    if (b.type !== 'hotel' || !b.start_dt) continue
    const checkin = b.start_dt.slice(0, 10)
    const checkout = b.end_dt ? b.end_dt.slice(0, 10) : null
    if (!checkout || checkout <= checkin) {
      add(checkin, b)
      continue
    }
    for (const day of eachDayInclusive(checkin, checkout)) add(day, b)
  }
  return map
}

export type LodgingKind = 'checkin' | 'noche' | 'checkout'

export function lodgingKind(b: Booking, day: string): LodgingKind {
  if (b.start_dt && b.start_dt.slice(0, 10) === day) return 'checkin'
  if (b.end_dt && b.end_dt.slice(0, 10) === day) return 'checkout'
  return 'noche'
}

// filas en tres columnas: hora | tipo (Vuelo/Llegada/Check-in…) | ruta o nombre

function lodgingTime(b: Booking, day: string): string {
  const kind = lodgingKind(b, day)
  if (kind === 'noche') return ''
  const dt = kind === 'checkout' ? b.end_dt! : b.start_dt!
  const t = dt.slice(11, 16)
  return t !== '00:00' ? t : ''
}

function lodgingKindLabel(b: Booking, day: string, t: TranslateFn): string {
  const kind = lodgingKind(b, day)
  if (kind === 'checkin') return t('itinerary.agenda.checkin')
  if (kind === 'checkout') return t('itinerary.agenda.checkout')
  return t('itinerary.agenda.night')
}

function transportTime(e: TransportEntry): string {
  const t = transportDt(e).slice(11, 16)
  return t !== '00:00' ? t : ''
}

function transportKind(e: TransportEntry, t: TranslateFn): string {
  return e.arrival ? t('itinerary.agenda.arrival') : t(BOOKING_TYPE_KEYS[e.b.type])
}

export function transportLabel(e: TransportEntry): string {
  const b = e.b
  return b.origin || b.destination ? `${b.origin ?? '?'} → ${b.destination ?? '?'}` : b.title
}

function bookingTime(b: Booking): string {
  const t = b.start_dt ? b.start_dt.slice(11, 16) : ''
  return t && t !== '00:00' ? t : ''
}

// cabecera de columna izquierda: "Check-in: 15:00", "Vuelo: 07:30", "noche"…

export function transportHead(e: TransportEntry, t: TranslateFn): string {
  const time = transportTime(e)
  return time ? `${transportKind(e, t)}: ${time}` : transportKind(e, t)
}

export function lodgingHead(b: Booking, day: string, t: TranslateFn): string {
  const kind = lodgingKindLabel(b, day, t)
  const time = lodgingTime(b, day)
  return time ? `${kind}: ${time}` : kind
}

export function bookingHead(b: Booking, t: TranslateFn): string {
  const time = bookingTime(b)
  return time ? `${t(BOOKING_TYPE_KEYS[b.type])}: ${time}` : t(BOOKING_TYPE_KEYS[b.type])
}

/** Días que muestra la agenda: rango del viaje + items (con sus rangos) +
 *  cualquier día con transporte/alojamiento/reserva. Orden ascendente. */
export function agendaDays(
  trip: { start_date: string | null; end_date: string | null },
  items: ItineraryItem[],
  transportsByDay: Map<string, TransportEntry[]>,
  otherBookingsByDay: Map<string, Booking[]>,
  lodgingByDay: Map<string, Booking[]>,
): string[] {
  const set = new Set<string>()
  if (trip.start_date && trip.end_date) {
    for (const day of eachDayInclusive(trip.start_date, trip.end_date)) set.add(day)
  }
  for (const item of items) {
    if (item.end_day && item.end_day > item.day) {
      for (const day of eachDayInclusive(item.day, item.end_day)) set.add(day)
    } else {
      set.add(item.day)
    }
  }
  for (const day of transportsByDay.keys()) set.add(day)
  for (const day of lodgingByDay.keys()) set.add(day)
  for (const day of otherBookingsByDay.keys()) set.add(day)
  return [...set].sort()
}

/** Items de varios días que "continúan" en un día dado (no arrastrables). */
export function buildContinuations(items: ItineraryItem[]): Map<string, ItineraryItem[]> {
  const map = new Map<string, ItineraryItem[]>()
  for (const item of items) {
    if (!item.end_day || item.end_day <= item.day) continue
    for (const day of eachDayInclusive(addDays(item.day, 1), item.end_day)) {
      map.set(day, [...(map.get(day) ?? []), item])
    }
  }
  return map
}

export function rangeNights(item: ItineraryItem): number {
  if (!item.end_day) return 0
  return daysBetween(item.day, item.end_day)
}

/** Cabecera de día: "Día N" si cae dentro del viaje, si no la fecha larga. */
export function agendaDayLabel(
  iso: string,
  tripStart: string | null,
  t: TranslateFn,
): { title: string; sub: string } {
  // la fecha manda (título); el ordinal "Día N" acompaña en pequeño
  const dateLabel = parseIsoDate(iso).toLocaleDateString(intlLocale(), {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  if (tripStart) {
    const diff = daysBetween(tripStart, iso) + 1
    if (diff >= 1) return { title: dateLabel, sub: t('itinerary.agenda.dayN', { n: diff }) }
  }
  return { title: dateLabel, sub: '' }
}

export function fmtTime(t: string | null): string {
  return t ? t.slice(0, 5) : ''
}

export function fmtDayShort(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString(intlLocale(), { day: 'numeric', month: 'short' })
}

export interface RouteStop {
  placeId: number
  name: string
  lat: number
  lon: number
  /** días ISO en los que el itinerario pasa por la parada (ordenados) */
  days: string[]
}

/**
 * Ruta del viaje: sitios de la agenda en orden (día, posición). Las visitas
 * consecutivas al mismo sitio se funden en UNA parada acumulando sus días
 * (las estancias multi-día aportan el rango completo) — así cada parada sabe
 * cuándo se fue y cuánto se estuvo.
 */
export function buildRoute(items: ItineraryItem[], placeById: Map<number, Place>): RouteStop[] {
  const ordered = [...items].sort(
    (a, b) => a.day.localeCompare(b.day) || a.order_index - b.order_index || a.id - b.id,
  )
  const route: RouteStop[] = []
  for (const item of ordered) {
    const place = item.place_id != null ? placeById.get(item.place_id) : undefined
    if (place?.lat == null || place.lon == null) continue
    const days =
      item.end_day && item.end_day > item.day
        ? eachDayInclusive(item.day, item.end_day)
        : [item.day]
    const prev = route[route.length - 1]
    if (prev && prev.placeId === place.id) {
      prev.days = [...new Set([...prev.days, ...days])].sort()
      continue
    }
    route.push({ placeId: place.id, name: place.name, lat: place.lat, lon: place.lon, days })
  }
  return route
}
