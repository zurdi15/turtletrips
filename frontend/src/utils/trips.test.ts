import { describe, expect, it } from 'vitest'
import { byDateDesc, groupTrips, pickHeroTrip, tripDateRange } from './trips'
import type { Trip } from '../api/types'

function trip(partial: Partial<Trip> & { id: number }): Trip {
  return {
    name: `Viaje ${partial.id}`,
    start_date: null,
    end_date: null,
    countries: [],
    status: 'planning',
    status_override: null,
    notes: null,
    base_currency: 'EUR',
    budget_amount: null,
    album_url: null,
    cover_url: null,
    travelers: [],
    debts_settled: false,
    ics_token: null,
    created_at: '2026-01-01T00:00:00',
    updated_at: '2026-01-01T00:00:00',
    ...partial,
  } as Trip
}

describe('byDateDesc', () => {
  it('recientes primero; sin fecha al final (por id desc)', () => {
    const sorted = byDateDesc([
      trip({ id: 1, start_date: '2025-01-10' }),
      trip({ id: 2 }),
      trip({ id: 3, start_date: '2026-03-01' }),
      trip({ id: 4 }),
    ])
    expect(sorted.map((t) => t.id)).toEqual([3, 1, 4, 2])
  })
})

describe('groupTrips por año', () => {
  it('agrupa por año descendente con "Sin fecha" al final', () => {
    const groups = groupTrips(
      [
        trip({ id: 1, start_date: '2025-05-01' }),
        trip({ id: 2, start_date: '2026-02-01' }),
        trip({ id: 3 }),
        trip({ id: 4, start_date: '2026-08-01' }),
      ],
      'year',
    )
    expect(groups.map((g) => g.key)).toEqual(['2026', '2025', 'Sin fecha'])
    expect(groups[0].trips.map((t) => t.id)).toEqual([4, 2])
  })
})

describe('groupTrips por estado', () => {
  it('sigue el orden en-curso/próximo/planificando/terminado y omite vacíos', () => {
    const groups = groupTrips(
      [
        trip({ id: 1, status: 'done', start_date: '2024-01-01' }),
        trip({ id: 2, status: 'ongoing', start_date: '2026-07-20' }),
        trip({ id: 3, status: 'planning' }),
      ],
      'status',
    )
    expect(groups.map((g) => g.key)).toEqual(['ongoing', 'planning', 'done'])
    expect(groups[0].title).toBe('En curso')
  })
})

describe('pickHeroTrip', () => {
  it('prefiere el viaje en curso', () => {
    const hero = pickHeroTrip([
      trip({ id: 1, status: 'upcoming', start_date: '2026-08-01' }),
      trip({ id: 2, status: 'ongoing', start_date: '2026-07-20' }),
    ])
    expect(hero?.id).toBe(2)
  })
  it('si no hay en curso: el próximo más cercano en fecha', () => {
    const hero = pickHeroTrip([
      trip({ id: 1, status: 'upcoming', start_date: '2026-12-01' }),
      trip({ id: 2, status: 'upcoming', start_date: '2026-08-01' }),
      trip({ id: 3, status: 'done', start_date: '2025-01-01' }),
    ])
    expect(hero?.id).toBe(2)
  })
  it('sin candidatos: null', () => {
    expect(pickHeroTrip([trip({ id: 1, status: 'done' })])).toBeNull()
  })
})

describe('tripDateRange', () => {
  it('sin fechas', () => {
    expect(tripDateRange({ start_date: null, end_date: null })).toBe('Sin fechas')
  })
  it('solo inicio', () => {
    expect(tripDateRange({ start_date: '2026-08-01', end_date: null })).not.toContain('→')
  })
  it('rango completo', () => {
    expect(tripDateRange({ start_date: '2026-08-01', end_date: '2026-08-10' })).toContain('→')
  })
})
