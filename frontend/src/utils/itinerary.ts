import type { Booking, ItineraryItem } from '../api/types'
import { BOOKING_TYPE_LABELS, isTransport } from '../constants'
import { parseIsoDate } from '../composables/useMoney'
import { addDays, daysBetween, eachDayInclusive } from './dates'

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

function lodgingKindLabel(b: Booking, day: string): string {
  const kind = lodgingKind(b, day)
  if (kind === 'checkin') return 'Check-in'
  if (kind === 'checkout') return 'Check-out'
  return 'noche'
}

function transportTime(e: TransportEntry): string {
  const t = transportDt(e).slice(11, 16)
  return t !== '00:00' ? t : ''
}

function transportKind(e: TransportEntry): string {
  return e.arrival ? 'Llegada' : BOOKING_TYPE_LABELS[e.b.type]
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

export function transportHead(e: TransportEntry): string {
  const t = transportTime(e)
  return t ? `${transportKind(e)}: ${t}` : transportKind(e)
}

export function lodgingHead(b: Booking, day: string): string {
  const kind = lodgingKindLabel(b, day)
  const t = lodgingTime(b, day)
  return t ? `${kind}: ${t}` : kind
}

export function bookingHead(b: Booking): string {
  const t = bookingTime(b)
  return t ? `${BOOKING_TYPE_LABELS[b.type]}: ${t}` : BOOKING_TYPE_LABELS[b.type]
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
): { title: string; sub: string } {
  const sub = parseIsoDate(iso).toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  if (tripStart) {
    const diff = daysBetween(tripStart, iso) + 1
    if (diff >= 1) return { title: `Día ${diff}`, sub }
  }
  return { title: sub, sub: '' }
}

export function fmtTime(t: string | null): string {
  return t ? t.slice(0, 5) : ''
}

export function fmtDayShort(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
}
