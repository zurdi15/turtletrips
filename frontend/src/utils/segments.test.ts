import { describe, expect, it } from 'vitest'
import type { Booking, BookingSegment } from '../api/types'
import {
  gapMinutes,
  groupJourneys,
  journeyRoute,
  layoverAfter,
  segmentLabel,
  upcomingBookings,
} from './segments'

let nextId = 1
function seg(partial: Partial<BookingSegment>): BookingSegment {
  return {
    id: nextId++,
    position: 0,
    origin: null,
    destination: null,
    departure_dt: null,
    arrival_dt: null,
    flight_number: null,
    ...partial,
  }
}

// ida con escala y vuelta con escala (los 4 vuelos de una reserva)
const MAD_DOH = seg({
  origin: 'MAD',
  destination: 'DOH',
  departure_dt: '2026-04-01T10:00:00',
  arrival_dt: '2026-04-01T18:30:00',
})
const DOH_NRT = seg({
  origin: 'DOH',
  destination: 'NRT',
  departure_dt: '2026-04-01T21:55:00',
  arrival_dt: '2026-04-02T13:20:00',
})
const NRT_DOH = seg({
  origin: 'NRT',
  destination: 'DOH',
  departure_dt: '2026-04-14T22:00:00',
  arrival_dt: '2026-04-15T04:30:00',
})
const DOH_MAD = seg({
  origin: 'DOH',
  destination: 'MAD',
  departure_dt: '2026-04-15T07:45:00',
  arrival_dt: '2026-04-15T13:45:00',
})

describe('gapMinutes', () => {
  it('mide la espera llegada→salida, también cruzando la medianoche', () => {
    expect(gapMinutes(MAD_DOH, DOH_NRT)).toBe(205) // 18:30 → 21:55
    expect(gapMinutes(NRT_DOH, DOH_MAD)).toBe(195) // 04:30 → 07:45 (día siguiente ya)
    const lateArrival = seg({ arrival_dt: '2026-04-01T23:30:00' })
    const earlyNext = seg({ departure_dt: '2026-04-02T01:15:00' })
    expect(gapMinutes(lateArrival, earlyNext)).toBe(105)
  })

  it('null si falta alguna de las dos horas', () => {
    expect(gapMinutes(seg({}), DOH_NRT)).toBeNull()
    expect(gapMinutes(MAD_DOH, seg({}))).toBeNull()
  })
})

describe('groupJourneys', () => {
  it('escala corta une, hueco de días separa (ida y vuelta)', () => {
    const journeys = groupJourneys([MAD_DOH, DOH_NRT, NRT_DOH, DOH_MAD])
    expect(journeys).toHaveLength(2)
    expect(journeys[0].map((s) => s.origin)).toEqual(['MAD', 'DOH'])
    expect(journeys[1].map((s) => s.origin)).toEqual(['NRT', 'DOH'])
  })

  it('un hueco incomputable (faltan fechas) une sin escala', () => {
    const sinFechas = seg({ origin: 'DOH', destination: 'NRT' })
    expect(groupJourneys([MAD_DOH, sinFechas])).toHaveLength(1)
  })

  it('exactamente 24 h ya es trayecto nuevo', () => {
    const next = seg({ origin: 'DOH', departure_dt: '2026-04-02T18:30:00' })
    expect(groupJourneys([MAD_DOH, next])).toHaveLength(2)
  })

  it('sin tramos, sin trayectos', () => {
    expect(groupJourneys([])).toEqual([])
  })
})

describe('layoverAfter', () => {
  it('la espera vive donde aterrizas', () => {
    expect(layoverAfter(MAD_DOH, DOH_NRT)).toEqual({ place: 'DOH', minutes: 205 })
  })

  it('sin horas: el sitio sí, la duración no', () => {
    const prev = seg({ destination: 'DOH' })
    expect(layoverAfter(prev, DOH_NRT)).toEqual({ place: 'DOH', minutes: null })
  })

  it('sin destino previo cae al origen del siguiente; huecos negativos no puntúan', () => {
    expect(layoverAfter(seg({}), DOH_NRT).place).toBe('DOH')
    const overlapping = seg({ arrival_dt: '2026-04-01T23:00:00' })
    const before = seg({ origin: 'DOH', departure_dt: '2026-04-01T22:00:00' })
    expect(layoverAfter(overlapping, before).minutes).toBeNull()
  })
})

describe('upcomingBookings', () => {
  function bookingWith(partial: Partial<Booking>): Booking {
    return {
      id: nextId++,
      trip_id: 1,
      type: 'flight',
      title: 'Reserva',
      provider: null,
      confirmation_code: null,
      flight_number: null,
      start_dt: null,
      end_dt: null,
      origin: null,
      destination: null,
      address: null,
      lat: null,
      lon: null,
      cost_amount: null,
      cost_currency: null,
      notes: null,
      place_id: null,
      paid_by_id: null,
      paid_by_common: false,
      segments: [],
      ...partial,
    }
  }
  const roundTrip = bookingWith({ segments: [MAD_DOH, DOH_NRT, NRT_DOH, DOH_MAD] })

  it('la vuelta sigue siendo próxima aunque la ida ya haya volado', () => {
    const midTrip = new Date('2026-04-05T12:00:00').getTime()
    const entries = upcomingBookings([roundTrip], midTrip)
    expect(entries).toHaveLength(1)
    expect(entries[0]).toMatchObject({ dt: '2026-04-14T22:00:00', route: 'NRT → MAD' })
    // el trayecto viaja entero: el resumen pinta con él los tramos y escalas
    expect(entries[0].journey.map((s) => s.origin)).toEqual(['NRT', 'DOH'])
  })

  it('antes del viaje aparecen los dos trayectos, ordenados', () => {
    const before = new Date('2026-03-01T00:00:00').getTime()
    const entries = upcomingBookings([roundTrip], before)
    expect(entries.map((e) => e.route)).toEqual(['MAD → NRT', 'NRT → MAD'])
  })

  it('el horizonte corta lo lejano: a 7 días vista la vuelta aún no asoma', () => {
    const dayMs = 24 * 60 * 60 * 1000
    const beforeTrip = new Date('2026-03-30T12:00:00').getTime()
    // la ida (1 abr) cae dentro de la semana; la vuelta (14 abr) no
    const entries = upcomingBookings([roundTrip], beforeTrip, 0, 7 * dayMs)
    expect(entries.map((e) => e.route)).toEqual(['MAD → NRT'])
  })

  it('reserva sin tramos usa start_dt (route null) y el margen de gracia', () => {
    const legacy = bookingWith({ segments: [], start_dt: '2026-04-05T09:00:00' })
    const later = new Date('2026-04-05T23:00:00').getTime()
    expect(upcomingBookings([legacy], later)).toHaveLength(0)
    const dayMs = 24 * 60 * 60 * 1000
    const withGrace = upcomingBookings([legacy], later, dayMs)
    expect(withGrace).toHaveLength(1)
    expect(withGrace[0].route).toBeNull()
  })
})

describe('segmentLabel y journeyRoute', () => {
  it('ruta con interrogantes solo si falta un extremo', () => {
    expect(segmentLabel(MAD_DOH)).toBe('MAD → DOH')
    expect(segmentLabel(seg({ origin: 'MAD' }))).toBe('MAD → ?')
    expect(segmentLabel(seg({}))).toBeNull()
  })

  it('journeyRoute: extremos del trayecto y escalas contadas', () => {
    expect(journeyRoute([MAD_DOH, DOH_NRT])).toEqual({
      origin: 'MAD',
      destination: 'NRT',
      stops: 1,
    })
    expect(journeyRoute([])).toEqual({ origin: null, destination: null, stops: 0 })
  })
})
