import { describe, expect, it } from 'vitest'
import type { Booking, ItineraryItem, Place } from '../api/types'
import { coordKey, itemCoord, pickDayCoords, weatherIcon } from './weather'

function makePlace(id: number, lat: number | null, lon: number | null): Place {
  return {
    id, trip_id: 1, name: `P${id}`, category: 'other' as Place['category'],
    notes: null, url: null, address: null, lat, lon, visited: false, priority: 0,
  }
}

function makeBooking(overrides: Partial<Booking>): Booking {
  return {
    id: 1, trip_id: 1, type: 'hotel' as Booking['type'], title: 'Hotel', provider: null,
    confirmation_code: null, flight_number: null, start_dt: null, end_dt: null,
    origin: null, destination: null, address: null, lat: null, lon: null,
    cost_amount: null, cost_currency: null, notes: null, place_id: null,
    paid_by_id: null, paid_by_common: false,
    ...overrides,
  }
}

function makeItem(id: number, placeId: number | null): ItineraryItem {
  return {
    id, trip_id: 1, day: '2026-08-01', end_day: null, start_time: null, end_time: null,
    order_index: 0, title: 'x', notes: null, place_id: placeId, booking_id: null,
  } as ItineraryItem
}

describe('pickDayCoords', () => {
  const placeById = new Map([
    [1, makePlace(1, 40.4, -3.7)],
    [2, makePlace(2, null, null)],
    [3, makePlace(3, 41.4, 2.2)],
  ])

  it('usa SOLO el alojamiento y cubre todas sus noches (días "sigue")', () => {
    const hotel = makeBooking({ lat: 48.8, lon: 2.3 })
    // buildLodgingByDay reparte la estancia por noches: aquí se simula ya repartida
    const lodging = new Map([
      ['2026-08-01', [hotel]],
      ['2026-08-02', [hotel]],
    ])
    const coords = pickDayCoords(['2026-08-01', '2026-08-02', '2026-08-03'], lodging, placeById)
    expect(coords.get('2026-08-01')).toEqual({ lat: 48.8, lon: 2.3 })
    expect(coords.get('2026-08-02')).toEqual({ lat: 48.8, lon: 2.3 })
    // día sin alojamiento: la cabecera no lleva previsión
    expect(coords.has('2026-08-03')).toBe(false)
  })

  it('el alojamiento sin coords propias usa las de su sitio enlazado', () => {
    const lodging = new Map([['2026-08-01', [makeBooking({ place_id: 3 })]]])
    const coords = pickDayCoords(['2026-08-01'], lodging, placeById)
    expect(coords.get('2026-08-01')).toEqual({ lat: 41.4, lon: 2.2 })
  })

  it('itemCoord da la coordenada del sitio de la actividad', () => {
    expect(itemCoord(makeItem(1, 1), placeById)).toEqual({ lat: 40.4, lon: -3.7 })
    expect(itemCoord(makeItem(2, 2), placeById)).toBeNull()
    expect(itemCoord(makeItem(3, null), placeById)).toBeNull()
  })
})

describe('weatherIcon / coordKey', () => {
  it('mapea familias de códigos WMO', () => {
    expect(weatherIcon(0)).toContain('sunny')
    expect(weatherIcon(3)).toContain('cloudy')
    expect(weatherIcon(63)).toContain('rainy')
    expect(weatherIcon(75)).toContain('snowy')
    expect(weatherIcon(95)).toContain('lightning')
  })

  it('coordKey agrupa a ~11 km', () => {
    expect(coordKey({ lat: 40.41, lon: -3.7 })).toBe(coordKey({ lat: 40.44, lon: -3.68 }))
  })
})
