import { describe, expect, it, vi } from 'vitest'
import type { Booking, ItineraryItem, Place } from '../api/types'

// el módulo i18n real toca localStorage/navigator al importarse; aquí solo se
// usa intlLocale, así el test sigue siendo puro (sin DOM) y determinista
vi.mock('../i18n', () => ({ intlLocale: () => 'es-ES' }))
import {
  agendaDayLabel,
  agendaDays,
  bookingHead,
  buildContinuations,
  buildLodgingByDay,
  buildOtherBookingsByDay,
  buildRoute,
  buildTransportsByDay,
  fmtTime,
  lodgingHead,
  lodgingKind,
  rangeNights,
  transportHead,
  transportLabel,
  type TranslateFn,
} from './itinerary'

// stub de t: espejo mínimo en español de las claves que usan las etiquetas
const MESSAGES: Record<string, string> = {
  'itinerary.agenda.arrival': 'Llegada',
  'itinerary.agenda.checkin': 'Check-in',
  'itinerary.agenda.checkout': 'Check-out',
  'itinerary.agenda.night': 'noche',
  'itinerary.agenda.dayN': 'Día {n}',
  'common.bookingType.flight': 'Vuelo',
  'common.bookingType.train': 'Tren',
  'common.bookingType.activity': 'Actividad',
}
const t: TranslateFn = (key, named) => {
  let msg = MESSAGES[key] ?? key
  for (const [k, v] of Object.entries(named ?? {})) msg = msg.replace(`{${k}}`, String(v))
  return msg
}

let nextId = 1
function booking(partial: Partial<Booking>): Booking {
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
    ...partial,
  }
}

function item(partial: Partial<ItineraryItem>): ItineraryItem {
  return {
    id: nextId++,
    trip_id: 1,
    day: '2026-08-01',
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

describe('buildTransportsByDay', () => {
  it('vuelo nocturno: salida en su día y entrada de Llegada en el destino', () => {
    const flight = booking({
      type: 'flight',
      start_dt: '2026-08-01T23:50:00',
      end_dt: '2026-08-02T07:30:00',
      origin: 'MAD',
      destination: 'NRT',
    })
    const map = buildTransportsByDay([flight])
    expect(map.get('2026-08-01')).toEqual([{ b: flight, arrival: false }])
    expect(map.get('2026-08-02')).toEqual([{ b: flight, arrival: true }])
  })

  it('llegada el mismo día: una sola entrada', () => {
    const train = booking({
      type: 'train',
      start_dt: '2026-08-03T09:00:00',
      end_dt: '2026-08-03T11:30:00',
    })
    const map = buildTransportsByDay([train])
    expect(map.get('2026-08-03')).toHaveLength(1)
  })

  it('ordena por hora dentro del día e ignora no-transportes y sin fecha', () => {
    const late = booking({ type: 'bus', start_dt: '2026-08-01T18:00:00' })
    const early = booking({ type: 'ferry', start_dt: '2026-08-01T08:00:00' })
    const hotel = booking({ type: 'hotel', start_dt: '2026-08-01T15:00:00' })
    const sinFecha = booking({ type: 'flight' })
    const map = buildTransportsByDay([late, hotel, early, sinFecha])
    expect(map.get('2026-08-01')!.map((e) => e.b.id)).toEqual([early.id, late.id])
  })
})

describe('buildLodgingByDay', () => {
  it('expande del check-in al check-out inclusive', () => {
    const hotel = booking({
      type: 'hotel',
      start_dt: '2026-08-01T15:00:00',
      end_dt: '2026-08-04T11:00:00',
    })
    const map = buildLodgingByDay([hotel])
    expect([...map.keys()].sort()).toEqual(['2026-08-01', '2026-08-02', '2026-08-03', '2026-08-04'])
  })

  it('sin checkout (o mismo día): solo el día de entrada', () => {
    const map = buildLodgingByDay([booking({ type: 'hotel', start_dt: '2026-08-01T15:00:00' })])
    expect([...map.keys()]).toEqual(['2026-08-01'])
  })

  it('clasifica check-in / noche / check-out', () => {
    const hotel = booking({
      type: 'hotel',
      start_dt: '2026-08-01T15:00:00',
      end_dt: '2026-08-03T11:00:00',
    })
    expect(lodgingKind(hotel, '2026-08-01')).toBe('checkin')
    expect(lodgingKind(hotel, '2026-08-02')).toBe('noche')
    expect(lodgingKind(hotel, '2026-08-03')).toBe('checkout')
  })
})

describe('buildOtherBookingsByDay', () => {
  it('solo actividades/coche/otros con fecha, ordenados por hora', () => {
    const act = booking({ type: 'activity', start_dt: '2026-08-02T16:00:00' })
    const car = booking({ type: 'car_rental', start_dt: '2026-08-02T09:00:00' })
    const vuelo = booking({ type: 'flight', start_dt: '2026-08-02T08:00:00' })
    const map = buildOtherBookingsByDay([act, car, vuelo])
    expect(map.get('2026-08-02')!.map((b) => b.id)).toEqual([car.id, act.id])
  })
})

describe('etiquetas', () => {
  const flight = booking({
    type: 'flight',
    start_dt: '2026-08-01T23:50:00',
    end_dt: '2026-08-02T07:30:00',
    origin: 'MAD',
    destination: 'NRT',
    title: 'Iberia 6800',
  })

  it('transportHead: tipo + hora (Llegada usa la hora de fin)', () => {
    expect(transportHead({ b: flight, arrival: false }, t)).toBe('Vuelo: 23:50')
    expect(transportHead({ b: flight, arrival: true }, t)).toBe('Llegada: 07:30')
  })

  it('transportHead omite la medianoche (sin hora real)', () => {
    const sinHora = booking({ type: 'train', start_dt: '2026-08-01T00:00:00' })
    expect(transportHead({ b: sinHora, arrival: false }, t)).toBe('Tren')
  })

  it('transportLabel: ruta si hay origen/destino, título si no', () => {
    expect(transportLabel({ b: flight, arrival: false })).toBe('MAD → NRT')
    expect(transportLabel({ b: booking({ type: 'bus', title: 'Bus JR' }), arrival: false })).toBe(
      'Bus JR',
    )
  })

  it('lodgingHead: check-in/check-out con hora, noche sin ella', () => {
    const hotel = booking({
      type: 'hotel',
      start_dt: '2026-08-01T15:00:00',
      end_dt: '2026-08-03T11:00:00',
    })
    expect(lodgingHead(hotel, '2026-08-01', t)).toBe('Check-in: 15:00')
    expect(lodgingHead(hotel, '2026-08-02', t)).toBe('noche')
    expect(lodgingHead(hotel, '2026-08-03', t)).toBe('Check-out: 11:00')
  })

  it('bookingHead: tipo con hora si existe', () => {
    expect(bookingHead(booking({ type: 'activity', start_dt: '2026-08-02T16:00:00' }), t)).toBe(
      'Actividad: 16:00',
    )
    expect(bookingHead(booking({ type: 'activity' }), t)).toBe('Actividad')
  })
})

describe('agendaDays', () => {
  it('rango del viaje + items multi-día + días con reservas, ordenado', () => {
    const trip = { start_date: '2026-08-01', end_date: '2026-08-03' }
    const items = [item({ day: '2026-08-05', end_day: '2026-08-06' })]
    const transports = buildTransportsByDay([
      booking({ type: 'flight', start_dt: '2026-07-31T22:00:00' }),
    ])
    const days = agendaDays(trip, items, transports, new Map(), new Map())
    expect(days).toEqual([
      '2026-07-31',
      '2026-08-01',
      '2026-08-02',
      '2026-08-03',
      '2026-08-05',
      '2026-08-06',
    ])
  })
})

describe('buildContinuations', () => {
  it('un item multi-día continúa en cada día posterior hasta el fin', () => {
    const ruta = item({ day: '2026-08-01', end_day: '2026-08-03', title: 'Ruta' })
    const map = buildContinuations([ruta, item({ day: '2026-08-01' })])
    expect([...map.keys()].sort()).toEqual(['2026-08-02', '2026-08-03'])
    expect(map.get('2026-08-02')![0].title).toBe('Ruta')
  })
})

describe('rangeNights y dayLabel', () => {
  it('rangeNights cuenta noches del rango', () => {
    expect(rangeNights(item({ day: '2026-08-01', end_day: '2026-08-04' }))).toBe(3)
    expect(rangeNights(item({ day: '2026-08-01' }))).toBe(0)
  })

  it('dayLabel: "Día N" dentro del viaje, fecha larga fuera', () => {
    // la fecha es el título; el ordinal acompaña en el sub
    const day2 = agendaDayLabel('2026-08-02', '2026-08-01', t)
    expect(day2.sub).toBe('Día 2')
    expect(day2.title).not.toContain('Día')
    const before = agendaDayLabel('2026-07-30', '2026-08-01', t)
    expect(before.title).not.toContain('Día')
    expect(before.sub).toBe('')
  })

  it('fmtTime recorta segundos', () => {
    expect(fmtTime('16:30:00')).toBe('16:30')
    expect(fmtTime(null)).toBe('')
  })
})

describe('buildRoute', () => {
  function routeItem(
    id: number,
    day: string,
    order: number,
    placeId: number | null,
    endDay: string | null = null,
  ): ItineraryItem {
    return {
      id, trip_id: 1, day, end_day: endDay, start_time: null, end_time: null,
      order_index: order, title: 'x', notes: null, place_id: placeId, booking_id: null,
    } as ItineraryItem
  }
  function routePlace(id: number, lat: number | null, lon: number | null): [number, Place] {
    return [id, { id, name: `P${id}`, lat, lon } as Place]
  }

  it('ordena por día y posición, salta sitios sin coords y funde consecutivos acumulando días', () => {
    const placeById = new Map([
      routePlace(1, 40, -3),
      routePlace(2, null, null),
      routePlace(3, 41, 2),
    ])
    const items = [
      routeItem(4, '2026-08-03', 0, 3),
      routeItem(1, '2026-08-01', 0, 1),
      routeItem(2, '2026-08-01', 1, 2), // sin coords: fuera
      routeItem(3, '2026-08-02', 0, 1), // mismo sitio consecutivo: se funde
      routeItem(5, '2026-08-03', 1, null),
    ]
    const route = buildRoute(items, placeById)
    expect(route.map((s) => [s.lat, s.lon])).toEqual([
      [40, -3],
      [41, 2],
    ])
    expect(route[0].days).toEqual(['2026-08-01', '2026-08-02'])
    expect(route[0].name).toBe('P1')
  })

  it('las estancias multi-día aportan el rango completo de días', () => {
    const placeById = new Map([routePlace(1, 40, -3)])
    const route = buildRoute([routeItem(1, '2026-08-01', 0, 1, '2026-08-03')], placeById)
    expect(route[0].days).toEqual(['2026-08-01', '2026-08-02', '2026-08-03'])
  })
})
