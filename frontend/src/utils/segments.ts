// Derivación pura de los tramos de una reserva de transporte: agrupar en
// TRAYECTOS (ida vs vuelta) y calcular las esperas de escala entre tramos.
import type { Booking, BookingSegment } from '../api/types'
import { formatMinutes } from './transfers'

/** hueco llegada→salida a partir del cual ya no es una escala sino otro
 *  trayecto (la vuelta, una stopover de días) */
export const JOURNEY_GAP_HOURS = 24

/** ms de un datetime naive "YYYY-MM-DDTHH:MM:SS" sin pasar por la zona horaria
 *  del navegador (dos naive comparados en UTC dan la diferencia real) */
function naiveMs(iso: string): number {
  const [d, t] = iso.split('T')
  const [y, m, day] = d.split('-').map(Number)
  const [hh = 0, mm = 0] = (t ?? '').split(':').map(Number)
  return Date.UTC(y, m - 1, day, hh, mm)
}

/** Minutos de espera entre dos tramos consecutivos; null si falta alguna hora */
export function gapMinutes(prev: BookingSegment, next: BookingSegment): number | null {
  if (!prev.arrival_dt || !next.departure_dt) return null
  return Math.round((naiveMs(next.departure_dt) - naiveMs(prev.arrival_dt)) / 60_000)
}

/**
 * Agrupa los tramos (ya ordenados por position, como los sirve la API) en
 * trayectos: hueco < 24 h = escala del mismo trayecto; mayor = trayecto nuevo
 * (la vuelta). Un hueco incomputable (faltan horas) une, no separa.
 */
export function groupJourneys(segments: BookingSegment[]): BookingSegment[][] {
  const journeys: BookingSegment[][] = []
  let current: BookingSegment[] = []
  for (const seg of segments) {
    const prev = current[current.length - 1]
    if (prev) {
      const gap = gapMinutes(prev, seg)
      if (gap != null && gap >= JOURNEY_GAP_HOURS * 60) {
        journeys.push(current)
        current = []
      }
    }
    current.push(seg)
  }
  if (current.length) journeys.push(current)
  return journeys
}

/** La espera de escala tras un tramo: dónde (el sitio donde aterrizas) y
 *  cuánto; minutes null si no se puede calcular (y no se pinta duración) */
export function layoverAfter(
  prev: BookingSegment,
  next: BookingSegment,
): { place: string | null; minutes: number | null } {
  const minutes = gapMinutes(prev, next)
  return {
    place: prev.destination ?? next.origin,
    minutes: minutes != null && minutes > 0 ? minutes : null,
  }
}

/** "MAD → DOH" (o lo que haya de la ruta) */
export function segmentLabel(seg: BookingSegment): string | null {
  if (!seg.origin && !seg.destination) return null
  return `${seg.origin ?? '?'} → ${seg.destination ?? '?'}`
}

/** Extremos de un trayecto: "MAD → NRT" con sus escalas contadas */
export function journeyRoute(
  journey: BookingSegment[],
): { origin: string | null; destination: string | null; stops: number } {
  return {
    origin: journey[0]?.origin ?? null,
    destination: journey[journey.length - 1]?.destination ?? null,
    stops: Math.max(0, journey.length - 1),
  }
}

/** escala más corta que esto = conexión arriesgada, se pinta en ámbar */
export const SHORT_LAYOVER_MINUTES = 60

/** La espera tras el tramo `index` de un trayecto, lista para pintar
 *  ("DOH · 1 h 25 min" + si es una conexión justa); null en el último tramo
 *  o sin nada que decir. La comparten la tarjeta de reserva y el resumen. */
export function layoverInfo(
  journey: BookingSegment[],
  index: number,
): { text: string; short: boolean } | null {
  const next = journey[index + 1]
  if (!next) return null
  const { place, minutes } = layoverAfter(journey[index], next)
  if (!place && minutes == null) return null
  const wait = minutes != null ? formatMinutes(minutes) : null
  return {
    text: [place, wait].filter(Boolean).join(' · '),
    short: minutes != null && minutes < SHORT_LAYOVER_MINUTES,
  }
}

export interface UpcomingBookingEntry {
  b: Booking
  /** datetime que ordena y fecha la entrada (salida del trayecto pendiente) */
  dt: string
  /** ruta del trayecto cuando la reserva tiene tramos ("NRT → MAD") */
  route: string | null
  /** tramos del trayecto (vacío en reservas sin tramos): el resumen pinta
   *  con ellos los vuelos y sus escalas, no solo el trayecto completo */
  journey: BookingSegment[]
}

/**
 * Reservas pendientes para el "próximamente" del resumen: una reserva con
 * tramos aporta UNA entrada por trayecto — así la vuelta sigue apareciendo
 * aunque la ida ya haya volado, en vez de esfumarse con la reserva entera.
 * `grace` deja asomar lo recién pasado (p. ej. el último día) y `horizon`
 * corta lo lejano (a 7 días vista, lo del mes que viene no es "próximo").
 * Orden por fecha.
 */
export function upcomingBookings(
  bookings: Booking[],
  now: number,
  grace = 0,
  horizon = Infinity,
): UpcomingBookingEntry[] {
  const inWindow = (dt: string) => {
    const ms = new Date(dt).getTime()
    return ms >= now - grace && ms <= now + horizon
  }
  const entries: UpcomingBookingEntry[] = []
  for (const b of bookings) {
    const segs = (b.segments ?? []).filter((s) => s.departure_dt)
    if (segs.length) {
      for (const journey of groupJourneys(segs)) {
        const dep = journey[0].departure_dt!
        if (!inWindow(dep)) continue
        const { origin, destination } = journeyRoute(journey)
        entries.push({
          b,
          dt: dep,
          route: origin || destination ? `${origin ?? '?'} → ${destination ?? '?'}` : null,
          journey,
        })
      }
    } else if (b.start_dt && inWindow(b.start_dt)) {
      entries.push({ b, dt: b.start_dt, route: null, journey: [] })
    }
  }
  return entries.sort((a, other) => a.dt.localeCompare(other.dt))
}
