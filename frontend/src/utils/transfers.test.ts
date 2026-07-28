import { describe, expect, it } from 'vitest'
import type { ItineraryItem, Place } from '../api/types'
import {
  buildDayTransfers,
  dayFeasibility,
  formatKm,
  formatMinutes,
  haversineKm,
  travelMinutes,
  DETOUR_FACTOR,
} from './transfers'

// coordenadas reales para que las distancias sean comprobables a mano
const MADRID = { lat: 40.4168, lon: -3.7038 }
const BARCELONA = { lat: 41.3874, lon: 2.1686 }

let nextId = 1
function place(lat: number | null, lon: number | null): Place {
  return {
    id: nextId++,
    trip_id: 1,
    name: 'Sitio',
    category: 'sight',
    notes: null,
    url: null,
    address: null,
    lat,
    lon,
    visited: false,
    priority: 0,
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

/** cadena de actividades sobre sitios dados, en orden */
function chain(coords: ({ lat: number; lon: number } | null)[], times: (string | null)[] = []) {
  const places = new Map<number, Place>()
  const items = coords.map((c, idx) => {
    const p = place(c?.lat ?? null, c?.lon ?? null)
    places.set(p.id, p)
    return item({ place_id: c ? p.id : null, order_index: idx, start_time: times[idx] ?? null })
  })
  return { items, places }
}

describe('haversineKm', () => {
  it('mide la distancia real entre dos ciudades', () => {
    // Madrid–Barcelona en línea recta son ~505 km
    expect(haversineKm(MADRID, BARCELONA)).toBeGreaterThan(500)
    expect(haversineKm(MADRID, BARCELONA)).toBeLessThan(510)
  })

  it('el mismo punto son cero km y es simétrica', () => {
    expect(haversineKm(MADRID, MADRID)).toBe(0)
    expect(haversineKm(MADRID, BARCELONA)).toBeCloseTo(haversineKm(BARCELONA, MADRID), 9)
  })
})

describe('travelMinutes', () => {
  it('convierte con la velocidad de cada modo', () => {
    expect(travelMinutes(4.5, 'walk')).toBe(60)
    expect(travelMinutes(45, 'car')).toBe(60)
    expect(travelMinutes(1, 'walk')).toBeGreaterThan(travelMinutes(1, 'transit'))
  })
})

describe('buildDayTransfers', () => {
  it('encadena las paradas y aplica el factor de rodeo', () => {
    const { items, places } = chain([MADRID, BARCELONA])
    const t = buildDayTransfers(items, places, 'car')
    expect(t.list).toHaveLength(1)
    expect(t.list[0].km).toBeCloseTo(haversineKm(MADRID, BARCELONA) * DETOUR_FACTOR, 6)
    expect(t.list[0].fromId).toBe(items[0].id)
    expect(t.byItem.get(items[1].id)).toBe(t.list[0])
    expect(t.km).toBeCloseTo(t.list[0].km, 6)
  })

  it('la primera actividad no lleva traslado', () => {
    const { items, places } = chain([MADRID, BARCELONA])
    expect(buildDayTransfers(items, places, 'walk').byItem.has(items[0].id)).toBe(false)
  })

  it('una actividad sin sitio no corta la cadena', () => {
    const { items, places } = chain([MADRID, null, BARCELONA])
    const t = buildDayTransfers(items, places, 'car')
    expect(t.list).toHaveLength(1)
    expect(t.list[0].fromId).toBe(items[0].id)
    expect(t.list[0].toId).toBe(items[2].id)
  })

  it('dos actividades en el mismo sitio no generan traslado', () => {
    const { items, places } = chain([MADRID, MADRID])
    expect(buildDayTransfers(items, places, 'walk').list).toHaveLength(0)
  })

  it('marca los saltos largos', () => {
    const { items, places } = chain([MADRID, BARCELONA])
    expect(buildDayTransfers(items, places, 'car').list[0].longHaul).toBe(true)
    const cerca = chain([MADRID, { lat: 40.42, lon: -3.69 }])
    expect(buildDayTransfers(cerca.items, cerca.places, 'walk').list[0].longHaul).toBe(false)
  })

  it('suma totales de km y minutos', () => {
    const { items, places } = chain([
      MADRID,
      { lat: 40.45, lon: -3.69 },
      { lat: 40.5, lon: -3.7 },
    ])
    const t = buildDayTransfers(items, places, 'walk')
    expect(t.list).toHaveLength(2)
    expect(t.km).toBeCloseTo(t.list[0].km + t.list[1].km, 9)
    expect(t.minutes).toBe(t.list[0].minutes + t.list[1].minutes)
  })
})

describe('tramos cubiertos por una reserva de transporte', () => {
  it('el salto largo se marca cubierto y no suma al total del día', () => {
    const { items, places } = chain([MADRID, BARCELONA, { lat: 41.39, lon: 2.19 }])
    const t = buildDayTransfers(items, places, 'car', { hasTransport: true })
    expect(t.list[0].covered).toBe(true)
    expect(t.list[1].covered).toBe(false)
    // el total es solo lo que te mueves por tu cuenta al llegar
    expect(t.km).toBeCloseTo(t.list[1].km, 9)
    expect(t.minutes).toBe(t.list[1].minutes)
  })

  it('sin reserva de transporte nada queda cubierto', () => {
    const { items, places } = chain([MADRID, BARCELONA])
    expect(buildDayTransfers(items, places, 'car').list[0].covered).toBe(false)
  })

  it('un salto corto nunca se da por cubierto, aunque haya vuelo', () => {
    const { items, places } = chain([MADRID, { lat: 40.45, lon: -3.69 }])
    const t = buildDayTransfers(items, places, 'car', { hasTransport: true })
    expect(t.list[0].covered).toBe(false)
    expect(t.km).toBeGreaterThan(0)
  })
})

describe('dayFeasibility', () => {
  it('día tranquilo: sin avisos', () => {
    const { items, places } = chain([MADRID, { lat: 40.42, lon: -3.69 }], ['10:00', '12:00'])
    const t = buildDayTransfers(items, places, 'walk')
    expect(dayFeasibility(items, t)).toEqual([])
  })

  it('overlap: no da tiempo a llegar a la hora de la siguiente', () => {
    // ~4 km a pie (con rodeo) no se hacen en 10 minutos
    const { items, places } = chain([MADRID, { lat: 40.45, lon: -3.69 }], ['10:00', '10:10'])
    const t = buildDayTransfers(items, places, 'walk')
    expect(dayFeasibility(items, t)).toContain('overlap')
  })

  it('el mismo salto en coche sí cabe', () => {
    const { items, places } = chain([MADRID, { lat: 40.45, lon: -3.69 }], ['10:00', '10:30'])
    const t = buildDayTransfers(items, places, 'car')
    expect(dayFeasibility(items, t)).toEqual([])
  })

  it('tooLong: sin horas, el día estimado no cabe en 12 h', () => {
    const { items, places } = chain([MADRID, { lat: 41.0, lon: -3.7 }])
    const t = buildDayTransfers(items, places, 'walk')
    expect(dayFeasibility(items, t)).toContain('tooLong')
  })

  it('tooFar: salto de 500 km entre dos visitas sin transporte', () => {
    const { items, places } = chain([MADRID, BARCELONA])
    const t = buildDayTransfers(items, places, 'car')
    expect(dayFeasibility(items, t)).toContain('tooFar')
  })

  it('con vuelo o tren ese día, el salto largo no genera NINGÚN aviso', () => {
    // ni tooFar, ni el overlap/tooLong que saldrían de estimarlo en coche
    const conHoras = chain([MADRID, BARCELONA], ['08:00', '14:00'])
    const t1 = buildDayTransfers(conHoras.items, conHoras.places, 'car', { hasTransport: true })
    expect(dayFeasibility(conHoras.items, t1)).toEqual([])

    const sinHoras = chain([MADRID, BARCELONA])
    const t2 = buildDayTransfers(sinHoras.items, sinHoras.places, 'car', { hasTransport: true })
    expect(dayFeasibility(sinHoras.items, t2)).toEqual([])
  })

  it('día sin traslados: nada que avisar', () => {
    const { items, places } = chain([MADRID])
    expect(dayFeasibility(items, buildDayTransfers(items, places, 'walk'))).toEqual([])
  })
})

describe('formato', () => {
  it('km: decimal por debajo de 10, entero por encima', () => {
    expect(formatKm(2.44, 'en-GB')).toBe('2.4 km')
    expect(formatKm(18.6, 'en-GB')).toBe('19 km')
    expect(formatKm(0.2, 'en-GB')).toBe('0.2 km')
  })

  it('minutos: horas y minutos, nunca cero', () => {
    expect(formatMinutes(45)).toBe('45 min')
    expect(formatMinutes(125)).toBe('2 h 5 min')
    expect(formatMinutes(120)).toBe('2 h')
    expect(formatMinutes(0.2)).toBe('1 min')
  })
})
