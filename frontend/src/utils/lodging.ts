// Cobertura de alojamiento NOCHE A NOCHE: qué noches del viaje tienen cama y
// cuáles no. Una noche se nombra por el día en que te acuestas, así que una
// reserva cubre [check-in .. check-out − 1] y un viaje tiene una noche menos
// que días.
//
// ⚠️ No sirve `buildLodgingByDay` de itinerary.ts: aquella incluye a propósito
// el día del check-out porque la agenda quiere enseñar la salida.
import type { Booking } from '../api/types'
import { addDays, eachDayInclusive } from './dates'

/** Tramo consecutivo de noches sin alojamiento */
export interface LodgingGap {
  /** primera noche descubierta (ISO) */
  from: string
  /** última noche descubierta (ISO); igual a `from` si es una sola */
  to: string
  nights: number
}

export interface LodgingCoverage {
  totalNights: number
  covered: number
  gaps: LodgingGap[]
  /** noches sin alojamiento sueltas, para marcar el día en la agenda */
  gapNights: Set<string>
  /** noches con más de una reserva (doble reserva o solape al cambiar de hotel) */
  overlapNights: string[]
}

/** Noches del viaje: del día de entrada a la víspera del de salida. */
export function tripNights(trip: {
  start_date: string | null
  end_date: string | null
}): string[] {
  if (!trip.start_date || !trip.end_date) return []
  // ida y vuelta el mismo día: no se duerme fuera (eachDayInclusive da [])
  return eachDayInclusive(trip.start_date, addDays(trip.end_date, -1))
}

/** Noches que cubre una reserva de alojamiento; [] si no es alojamiento. */
export function bookingNights(b: Booking): string[] {
  if (b.type !== 'hotel' || !b.start_dt) return []
  const checkin = b.start_dt.slice(0, 10)
  const checkout = b.end_dt ? b.end_dt.slice(0, 10) : null
  // sin check-out (o mal metido) se asume una noche
  if (!checkout || checkout <= checkin) return [checkin]
  return eachDayInclusive(checkin, addDays(checkout, -1))
}

/**
 * Índice noche → reservas que la cubren. Es la pieza reutilizable: de aquí
 * salen los huecos y los solapes, y más adelante el reparto de noches por país.
 */
export function coveredNights(bookings: Booking[]): Map<string, Booking[]> {
  const map = new Map<string, Booking[]>()
  for (const b of bookings) {
    for (const night of bookingNights(b)) {
      map.set(night, [...(map.get(night) ?? []), b])
    }
  }
  return map
}

/** ¿Se lleva el alojamiento en la app? Sin ninguna reserva no hay nada que avisar. */
export function hasLodgingBookings(bookings: Booking[]): boolean {
  return bookings.some((b) => b.type === 'hotel' && b.start_dt)
}

/** Huecos de alojamiento del viaje, agrupados en tramos consecutivos. */
export function lodgingCoverage(
  trip: { start_date: string | null; end_date: string | null },
  bookings: Booking[],
): LodgingCoverage {
  const nights = tripNights(trip)
  const index = coveredNights(bookings)
  const gaps: LodgingGap[] = []
  const gapNights = new Set<string>()
  const overlapNights: string[] = []
  let covered = 0
  // las noches vienen consecutivas, así que basta con cortar el tramo en cuanto
  // aparece una noche cubierta
  let run: LodgingGap | null = null

  for (const night of nights) {
    const booked = index.get(night)?.length ?? 0
    if (booked > 1) overlapNights.push(night)
    if (booked) {
      covered += 1
      run = null
      continue
    }
    gapNights.add(night)
    if (run) {
      run.to = night
      run.nights += 1
    } else {
      run = { from: night, to: night, nights: 1 }
      gaps.push(run)
    }
  }

  return { totalNights: nights.length, covered, gaps, gapNights, overlapNights }
}
