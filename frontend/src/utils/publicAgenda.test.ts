import { describe, expect, it, vi } from 'vitest'
import type { Booking, ItineraryItem, Place } from '../api/types'

vi.mock('../i18n', () => ({ intlLocale: () => 'es-ES' }))
import { buildPublicDay } from './publicAgenda'
import type { TranslateFn } from './itinerary'

const MESSAGES: Record<string, string> = {
  'itinerary.agenda.checkin': 'Check-in',
  'itinerary.agenda.checkout': 'Check-out',
  'itinerary.agenda.night': 'noche',
  'itinerary.agenda.arrival': 'Llegada',
  'common.bookingType.flight': 'Vuelo',
  'common.bookingType.activity': 'Actividad',
}
const t: TranslateFn = (key) => MESSAGES[key] ?? key

let nextId = 1
function booking(partial: Partial<Booking>): Booking {
  return {
    id: nextId++,
    trip_id: 1,
    type: 'other',
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
    ...partial,
  }
}

function item(partial: Partial<ItineraryItem>): ItineraryItem {
  return {
    id: nextId++,
    trip_id: 1,
    day: '2026-09-05',
    end_day: null,
    start_time: null,
    end_time: null,
    order_index: 0,
    title: 'Actividad',
    notes: null,
    place_id: null,
    booking_id: null,
    ...partial,
  }
}

const PLACE: Place = {
  id: 100,
  trip_id: 1,
  name: 'Sagrada Família',
  category: 'sight',
  notes: null,
  url: null,
  address: null,
  lat: 41.4,
  lon: 2.17,
  visited: false,
  priority: 0,
}
const places = new Map([[PLACE.id, PLACE]])

describe('buildPublicDay', () => {
  it('ordena transporte, reservas, actividades y alojamiento', () => {
    const vuelo = booking({
      type: 'flight',
      title: 'Ida',
      origin: 'MAD',
      destination: 'BCN',
      start_dt: '2026-09-05T08:30',
      provider: 'Iberia',
    })
    const tour = booking({ type: 'activity', title: 'Tour', start_dt: '2026-09-05T16:00' })
    const hotel = booking({ type: 'hotel', title: 'Casa Gràcia', start_dt: '2026-09-05T15:00' })
    const rows = buildPublicDay(
      '2026-09-05',
      [item({ title: 'Subida a las torres', place_id: PLACE.id, start_time: '12:30' })],
      [{ b: vuelo, arrival: false }],
      [tour],
      [hotel],
      places,
      t,
    )
    expect(rows.map((r) => r.tone)).toEqual(['info', 'warn', 'plain', 'lodging'])
    expect(rows[0]).toMatchObject({ head: 'Vuelo: 08:30', title: 'MAD → BCN', place: 'Iberia' })
    expect(rows[2]).toMatchObject({ head: '12:30', place: 'Sagrada Família' })
    expect(rows[3].head).toBe('Check-in: 15:00')
  })

  it('la actividad sin hora no inventa una', () => {
    const rows = buildPublicDay('2026-09-05', [item({ title: 'Paseo' })], [], [], [], places, t)
    expect(rows[0]).toMatchObject({ head: '', title: 'Paseo', place: null, note: null })
  })

  it('no repite el sitio cuando la actividad se llama igual', () => {
    const rows = buildPublicDay(
      '2026-09-05',
      [item({ title: 'Sagrada Família', place_id: PLACE.id, notes: null })],
      [],
      [],
      [],
      places,
      t,
    )
    expect(rows[0].place).toBeNull()
  })

  it('sin sitio enlazado cae la nota como detalle', () => {
    const rows = buildPublicDay(
      '2026-09-05',
      [item({ title: 'Cena', notes: 'Reservar antes' })],
      [],
      [],
      [],
      places,
      t,
    )
    expect(rows[0].note).toBe('Reservar antes')
  })

  it('un rango de horas se muestra entero', () => {
    const rows = buildPublicDay(
      '2026-09-05',
      [item({ title: 'Museo', start_time: '10:00', end_time: '12:30' })],
      [],
      [],
      [],
      places,
      t,
    )
    expect(rows[0].head).toBe('10:00–12:30')
  })

  it('día vacío, ninguna fila', () => {
    expect(buildPublicDay('2026-09-05', [], [], [], [], places, t)).toEqual([])
  })
})
