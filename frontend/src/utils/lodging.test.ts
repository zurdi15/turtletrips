import { describe, expect, it } from 'vitest'
import type { Booking } from '../api/types'
import {
  bookingNights,
  coveredNights,
  hasLodgingBookings,
  lodgingCoverage,
  transitNights,
  tripNights,
} from './lodging'

let nextId = 1
function hotel(start: string | null, end: string | null = null): Booking {
  return booking({ type: 'hotel', start_dt: start, end_dt: end })
}

function booking(partial: Partial<Booking>): Booking {
  return {
    id: nextId++,
    trip_id: 1,
    type: 'hotel',
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

describe('tripNights', () => {
  it('cuenta una noche menos que días', () => {
    expect(tripNights({ start_date: '2026-04-10', end_date: '2026-04-13' })).toEqual([
      '2026-04-10',
      '2026-04-11',
      '2026-04-12',
    ])
  })

  it('ida y vuelta el mismo día no tiene noches', () => {
    expect(tripNights({ start_date: '2026-04-10', end_date: '2026-04-10' })).toEqual([])
  })

  it('sin fechas no hay noches', () => {
    expect(tripNights({ start_date: null, end_date: '2026-04-13' })).toEqual([])
    expect(tripNights({ start_date: '2026-04-10', end_date: null })).toEqual([])
  })
})

describe('bookingNights', () => {
  it('cubre del check-in a la víspera del check-out', () => {
    expect(bookingNights(hotel('2026-04-10T15:00', '2026-04-13T11:00'))).toEqual([
      '2026-04-10',
      '2026-04-11',
      '2026-04-12',
    ])
  })

  it('sin check-out asume una noche', () => {
    expect(bookingNights(hotel('2026-04-10T15:00'))).toEqual(['2026-04-10'])
  })

  it('check-out el mismo día o antes: una noche, no un rango vacío', () => {
    expect(bookingNights(hotel('2026-04-10T15:00', '2026-04-10T20:00'))).toEqual(['2026-04-10'])
    expect(bookingNights(hotel('2026-04-10T15:00', '2026-04-09T11:00'))).toEqual(['2026-04-10'])
  })

  it('ignora lo que no es alojamiento y lo que no tiene fecha', () => {
    expect(bookingNights(booking({ type: 'flight', start_dt: '2026-04-10T08:00' }))).toEqual([])
    expect(bookingNights(hotel(null))).toEqual([])
  })
})

describe('coveredNights', () => {
  it('indexa por noche y acumula las reservas que la cubren', () => {
    const a = hotel('2026-04-10T15:00', '2026-04-12T11:00')
    const b = hotel('2026-04-11T15:00', '2026-04-13T11:00')
    const index = coveredNights([a, b])
    expect([...index.keys()].sort()).toEqual(['2026-04-10', '2026-04-11', '2026-04-12'])
    expect(index.get('2026-04-11')).toEqual([a, b])
    expect(index.get('2026-04-12')).toEqual([b])
  })
})

describe('lodgingCoverage', () => {
  const trip = { start_date: '2026-04-10', end_date: '2026-04-16' } // 6 noches

  it('viaje entero cubierto: sin huecos', () => {
    const c = lodgingCoverage(trip, [hotel('2026-04-10T15:00', '2026-04-16T11:00')])
    expect(c).toMatchObject({ totalNights: 6, covered: 6, gaps: [], overlapNights: [] })
    expect(c.gapNights.size).toBe(0)
  })

  it('agrupa las noches descubiertas en tramos consecutivos', () => {
    const c = lodgingCoverage(trip, [
      hotel('2026-04-10T15:00', '2026-04-12T11:00'), // noches 10 y 11
      hotel('2026-04-14T15:00', '2026-04-15T11:00'), // noche 14
    ])
    expect(c.covered).toBe(3)
    expect(c.gaps).toEqual([
      { from: '2026-04-12', to: '2026-04-13', nights: 2 },
      { from: '2026-04-15', to: '2026-04-15', nights: 1 },
    ])
    expect([...c.gapNights].sort()).toEqual(['2026-04-12', '2026-04-13', '2026-04-15'])
  })

  it('el día del check-out no es una noche: no tapa el hueco siguiente', () => {
    const c = lodgingCoverage({ start_date: '2026-04-10', end_date: '2026-04-12' }, [
      hotel('2026-04-10T15:00', '2026-04-11T11:00'),
    ])
    expect(c.gaps).toEqual([{ from: '2026-04-11', to: '2026-04-11', nights: 1 }])
  })

  it('la última noche del viaje es la víspera de la vuelta', () => {
    const c = lodgingCoverage(trip, [hotel('2026-04-10T15:00', '2026-04-15T11:00')])
    expect(c.gaps).toEqual([{ from: '2026-04-15', to: '2026-04-15', nights: 1 }])
  })

  it('detecta noches con dos reservas encima', () => {
    const c = lodgingCoverage(trip, [
      hotel('2026-04-10T15:00', '2026-04-16T11:00'),
      hotel('2026-04-12T15:00', '2026-04-14T11:00'),
    ])
    expect(c.overlapNights).toEqual(['2026-04-12', '2026-04-13'])
  })

  it('las reservas fuera del viaje no cuentan como cobertura', () => {
    const c = lodgingCoverage(trip, [hotel('2026-04-01T15:00', '2026-04-05T11:00')])
    expect(c.covered).toBe(0)
    expect(c.gaps).toEqual([{ from: '2026-04-10', to: '2026-04-15', nights: 6 }])
  })

  it('viaje sin fechas: nada que avisar', () => {
    const c = lodgingCoverage({ start_date: null, end_date: null }, [hotel('2026-04-10T15:00')])
    expect(c).toMatchObject({ totalNights: 0, covered: 0, gaps: [] })
  })
})

describe('transitNights', () => {
  const seg = (position: number, departure_dt: string | null, arrival_dt: string | null) => ({
    id: position,
    position,
    origin: null,
    destination: null,
    departure_dt,
    arrival_dt,
    flight_number: null,
  })

  it('un vuelo nocturno cubre la noche de salida', () => {
    const flight = booking({
      type: 'flight',
      segments: [seg(0, '2026-04-10T22:00:00', '2026-04-11T06:30:00')],
    })
    expect([...transitNights([flight])]).toEqual(['2026-04-10'])
  })

  it('con escala, la noche entre tramos del mismo trayecto también va a bordo', () => {
    const flight = booking({
      type: 'flight',
      segments: [
        seg(0, '2026-04-10T15:00:00', '2026-04-10T23:00:00'),
        seg(1, '2026-04-11T06:00:00', '2026-04-11T12:00:00'),
      ],
    })
    expect([...transitNights([flight])]).toEqual(['2026-04-10'])
  })

  it('la vuelta (hueco ≥ 24 h) es otro trayecto: no tapa las noches de en medio', () => {
    const flight = booking({
      type: 'flight',
      segments: [
        seg(0, '2026-04-10T22:00:00', '2026-04-11T06:00:00'),
        seg(1, '2026-04-15T23:00:00', '2026-04-16T07:00:00'),
      ],
    })
    expect([...transitNights([flight])].sort()).toEqual(['2026-04-10', '2026-04-15'])
  })

  it('reserva plana sin tramos: salida y llegada de la reserva', () => {
    const train = booking({ type: 'train', start_dt: '2026-04-10T21:00:00', end_dt: '2026-04-11T08:00:00' })
    expect([...transitNights([train])]).toEqual(['2026-04-10'])
  })

  it('llegar el mismo día no es una noche a bordo; los hoteles no cuentan', () => {
    const flight = booking({
      type: 'flight',
      segments: [seg(0, '2026-04-10T08:00:00', '2026-04-10T12:00:00')],
    })
    expect(transitNights([flight, hotel('2026-04-10T15:00', '2026-04-12T11:00')]).size).toBe(0)
  })
})

describe('lodgingCoverage con noches a bordo', () => {
  const trip = { start_date: '2026-04-10', end_date: '2026-04-16' } // 6 noches
  const outbound = booking({
    type: 'flight',
    segments: [
      {
        id: 1,
        position: 0,
        origin: 'MAD',
        destination: 'NRT',
        departure_dt: '2026-04-10T22:00:00',
        arrival_dt: '2026-04-11T17:00:00',
        flight_number: null,
      },
    ],
  })

  it('la noche del vuelo de ida no es un hueco ni una cama', () => {
    const c = lodgingCoverage(trip, [outbound, hotel('2026-04-11T15:00', '2026-04-16T11:00')])
    expect(c).toMatchObject({ totalNights: 6, covered: 5, transit: 1, gaps: [] })
    expect(c.gapNights.size).toBe(0)
  })

  it('una noche a bordo corta el tramo de huecos como lo haría un hotel', () => {
    const c = lodgingCoverage(trip, [outbound, hotel('2026-04-13T15:00', '2026-04-16T11:00')])
    expect(c.transit).toBe(1)
    expect(c.gaps).toEqual([{ from: '2026-04-11', to: '2026-04-12', nights: 2 }])
  })

  it('un hotel esa misma noche sigue contando como cama', () => {
    const c = lodgingCoverage(trip, [outbound, hotel('2026-04-10T15:00', '2026-04-16T11:00')])
    expect(c).toMatchObject({ covered: 6, transit: 0 })
  })
})

describe('hasLodgingBookings', () => {
  it('solo cuenta alojamientos con fecha', () => {
    expect(hasLodgingBookings([])).toBe(false)
    expect(hasLodgingBookings([booking({ type: 'flight', start_dt: '2026-04-10T08:00' })])).toBe(
      false,
    )
    expect(hasLodgingBookings([hotel(null)])).toBe(false)
    expect(hasLodgingBookings([hotel('2026-04-10T15:00')])).toBe(true)
  })
})
