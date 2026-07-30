import type { Booking, BookingSegment, ItineraryItem, Place } from '../api/types'
import { BOOKING_TYPE_KEYS, isTransport } from '../constants'
import { intlLocale } from '../i18n'
import { parseIsoDate } from '../composables/useMoney'
import { addDays, daysBetween, eachDayInclusive } from './dates'
import {
  JOURNEY_GAP_HOURS,
  SHORT_LAYOVER_MINUTES,
  gapMinutes,
  layoverAfter,
  segmentLabel,
} from './segments'
import { formatMinutes } from './transfers'

/** `t` de vue-i18n (o un stub en tests): clave + interpolación con nombre */
export type TranslateFn = (key: string, named?: Record<string, unknown>) => string

// ---------------------------------------------------------------------------
// Derivación pura de la agenda del itinerario: qué reservas aparecen en qué
// día y con qué etiquetas. Transportes el día de salida (y de llegada si es
// otro día), alojamiento del check-in a la noche previa al check-out (más el
// día del check-out), resto de reservas en su día.
// ---------------------------------------------------------------------------

/** Salida el día de inicio; si llega OTRO día (vuelo nocturno), también una
 *  entrada de "Llegada" en el día de destino. Con tramos, una entrada por
 *  tramo más la ESPERA de escala entre tramos del mismo trayecto. */
export interface TransportEntry {
  b: Booking
  kind: 'departure' | 'arrival' | 'layover'
  /** datetime que ancla la entrada en su día (y en el orden intra-día) */
  dt: string
  /** tramo del que sale la entrada; ausente en reservas sin tramos */
  seg?: BookingSegment
  /** índice del TRAYECTO (ida = 0, vuelta = 1…) dentro de la reserva: los
   *  chips de la agenda se pintan una vez por trayecto, no por tramo */
  journey?: number
  layoverPlace?: string | null
  layoverMinutes?: number | null
}

/** key estable de la fila: compartida por la agenda de la app y la pública */
export function transportKey(e: TransportEntry): string {
  const kind = e.kind === 'departure' ? 's' : e.kind === 'arrival' ? 'a' : 'w'
  return e.seg ? `t-${e.b.id}-${kind}${e.seg.position}` : `t-${e.b.id}-${kind}`
}

export function buildTransportsByDay(bookings: Booking[]): Map<string, TransportEntry[]> {
  const map = new Map<string, TransportEntry[]>()
  const add = (day: string, e: TransportEntry) => map.set(day, [...(map.get(day) ?? []), e])
  for (const b of bookings) {
    if (!isTransport(b.type)) continue
    const segs = (b.segments ?? []).filter((s) => s.departure_dt)
    if (segs.length) {
      let journey = 0
      segs.forEach((seg, i) => {
        // mismo criterio que groupJourneys: un hueco de ≥24 h con el tramo
        // anterior abre trayecto nuevo (la vuelta)
        if (i > 0) {
          const fromPrev = gapMinutes(segs[i - 1], seg)
          if (fromPrev != null && fromPrev >= JOURNEY_GAP_HOURS * 60) journey += 1
        }
        const dep = seg.departure_dt!
        add(dep.slice(0, 10), { b, seg, journey, kind: 'departure', dt: dep })
        if (seg.arrival_dt && seg.arrival_dt.slice(0, 10) > dep.slice(0, 10)) {
          add(seg.arrival_dt.slice(0, 10), {
            b,
            seg,
            journey,
            kind: 'arrival',
            dt: seg.arrival_dt,
          })
        }
        // la espera de escala vive en el día en que ATERRIZA el tramo previo
        const next = segs[i + 1]
        if (!next || !seg.arrival_dt) return
        const gap = gapMinutes(seg, next)
        if (gap == null || gap <= 0 || gap >= JOURNEY_GAP_HOURS * 60) return
        const { place, minutes } = layoverAfter(seg, next)
        add(seg.arrival_dt.slice(0, 10), {
          b,
          seg,
          journey,
          kind: 'layover',
          dt: seg.arrival_dt,
          layoverPlace: place,
          layoverMinutes: minutes,
        })
      })
    } else if (b.start_dt) {
      add(b.start_dt.slice(0, 10), { b, kind: 'departure', dt: b.start_dt })
      if (b.end_dt && b.end_dt.slice(0, 10) > b.start_dt.slice(0, 10)) {
        add(b.end_dt.slice(0, 10), { b, kind: 'arrival', dt: b.end_dt })
      }
    }
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.dt.localeCompare(b.dt))
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

function timeOfDt(dt: string | null | undefined): string | null {
  if (!dt) return null
  const t = dt.slice(11, 16)
  return t !== '00:00' ? t : null
}

function transportTime(e: TransportEntry): string {
  return timeOfDt(e.dt) ?? ''
}

function transportKind(e: TransportEntry, t: TranslateFn): string {
  if (e.kind === 'layover') return t('itinerary.agenda.layover')
  if (e.kind === 'arrival') return t('itinerary.agenda.arrival')
  return t(BOOKING_TYPE_KEYS[e.b.type])
}

export function transportLabel(e: TransportEntry): string {
  if (e.kind === 'layover') {
    const wait = e.layoverMinutes != null ? formatMinutes(e.layoverMinutes) : null
    if (e.layoverPlace && wait) return `${e.layoverPlace} · ${wait}`
    return e.layoverPlace ?? wait ?? e.b.title
  }
  if (e.seg) {
    const route = segmentLabel(e.seg) ?? e.b.title
    // el número de vuelo acompaña a la salida (en la llegada sería repetirlo);
    // en la vista pública no viaja y la etiqueta queda en la ruta sola
    if (e.kind === 'departure' && e.seg.flight_number) {
      return `${route} · ${e.seg.flight_number}`
    }
    return route
  }
  const b = e.b
  return b.origin || b.destination ? `${b.origin ?? '?'} → ${b.destination ?? '?'}` : b.title
}

function bookingTime(b: Booking): string {
  const t = b.start_dt ? b.start_dt.slice(11, 16) : ''
  return t && t !== '00:00' ? t : ''
}

/**
 * Vista estructurada de una fila de transporte para la agenda de la app:
 * tipo, horas de salida Y llegada, ruta y número de vuelo por separado, para
 * poder darles tipografía propia (la agenda pública sigue con
 * transportHead/transportLabel, más planos).
 */
export interface TransportRowView {
  /** "Vuelo", "Llegada", "Escala"… (columna izquierda) */
  kind: string
  dep: string | null
  arr: string | null
  /** noches que cruza la llegada respecto a la salida (0 = mismo día) */
  plusDays: number
  route: string
  flightNumber: string | null
  /** fila de espera de escala: se pinta en voz baja */
  layover: boolean
  /** escala de <1 h: conexión arriesgada, en ámbar */
  shortLayover: boolean
}

export function transportRowView(e: TransportEntry, t: TranslateFn): TransportRowView {
  if (e.kind === 'layover') {
    const wait = e.layoverMinutes != null ? formatMinutes(e.layoverMinutes) : null
    return {
      kind: t('itinerary.agenda.layover'),
      dep: null,
      arr: null,
      plusDays: 0,
      route: [e.layoverPlace, wait].filter(Boolean).join(' · ') || e.b.title,
      flightNumber: null,
      layover: true,
      shortLayover: e.layoverMinutes != null && e.layoverMinutes < SHORT_LAYOVER_MINUTES,
    }
  }
  const b = e.b
  const route = e.seg
    ? (segmentLabel(e.seg) ?? b.title)
    : b.origin || b.destination
      ? `${b.origin ?? '?'} → ${b.destination ?? '?'}`
      : b.title
  if (e.kind === 'arrival') {
    return {
      kind: t('itinerary.agenda.arrival'),
      dep: null,
      arr: timeOfDt(e.dt),
      plusDays: 0,
      route,
      flightNumber: null,
      layover: false,
      shortLayover: false,
    }
  }
  // salida: la llegada acompaña SIEMPRE que se conozca, aunque caiga otro día
  const arrDt = e.seg ? e.seg.arrival_dt : b.end_dt
  return {
    kind: t(BOOKING_TYPE_KEYS[b.type]),
    dep: timeOfDt(e.dt),
    arr: timeOfDt(arrDt),
    plusDays: arrDt ? Math.max(0, daysBetween(e.dt.slice(0, 10), arrDt.slice(0, 10))) : 0,
    route,
    flightNumber: e.seg ? e.seg.flight_number : b.flight_number,
    layover: false,
    shortLayover: false,
  }
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
