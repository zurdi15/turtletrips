import type { Trip, TripStatus } from '../api/types'
import { TRIP_STATUS_LABELS } from '../constants'
import { formatDate } from '../composables/useMoney'

/** Orden por fecha de mayor a menor (los próximos antes que los terminados). */
export function byDateDesc(trips: Trip[]): Trip[] {
  return [...trips].sort((a, b) => {
    if (!a.start_date && !b.start_date) return b.id - a.id
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return b.start_date.localeCompare(a.start_date)
  })
}

const STATUS_ORDER: TripStatus[] = ['ongoing', 'upcoming', 'planning', 'done']

export interface TripGroup {
  key: string
  title: string
  trips: Trip[]
}

export function groupTrips(trips: Trip[], mode: 'year' | 'status'): TripGroup[] {
  if (mode === 'status') {
    return STATUS_ORDER.filter((s) => trips.some((t) => t.status === s)).map((status) => ({
      key: status,
      title: TRIP_STATUS_LABELS[status],
      trips: byDateDesc(trips.filter((t) => t.status === status)),
    }))
  }
  const byYear = new Map<string, Trip[]>()
  for (const trip of trips) {
    const year = trip.start_date ? trip.start_date.slice(0, 4) : 'Sin fecha'
    byYear.set(year, [...(byYear.get(year) ?? []), trip])
  }
  return [...byYear.entries()]
    .sort((a, b) => {
      if (a[0] === 'Sin fecha') return 1
      if (b[0] === 'Sin fecha') return -1
      return b[0].localeCompare(a[0]) // años recientes primero
    })
    .map(([year, trips]) => ({ key: year, title: year, trips: byDateDesc(trips) }))
}

/** Hero del listado: viaje en curso, o el próximo MÁS CERCANO en fecha. */
export function pickHeroTrip(trips: Trip[]): Trip | null {
  const ongoing = trips.filter((t) => t.status === 'ongoing')
  if (ongoing.length) return ongoing[0]
  const upcoming = trips
    .filter((t) => t.status === 'upcoming' && t.start_date)
    .sort((a, b) => a.start_date!.localeCompare(b.start_date!))
  return upcoming[0] ?? null
}

export function tripDateRange(trip: Pick<Trip, 'start_date' | 'end_date'>): string {
  if (!trip.start_date) return 'Sin fechas'
  let s = formatDate(trip.start_date)
  if (trip.end_date) s += ` → ${formatDate(trip.end_date)}`
  return s
}
