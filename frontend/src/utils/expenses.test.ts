import { describe, expect, it } from 'vitest'
import type { Expense } from '../api/types'
import {
  aggregate,
  buildRows,
  computeStats,
  countActiveFilters,
  cumulative,
  currencyBreakdown,
  emptyFilters,
  filterExpenses,
  groupTotals,
  sortRows,
  tripDayCount,
} from './expenses'

let nextId = 1
function makeExpense(overrides: Partial<Expense> = {}): Expense {
  return {
    id: nextId++,
    trip_id: 1,
    booking_id: null,
    place_id: null,
    day: '2026-02-10',
    category: 'Comida',
    description: 'Gasto',
    amount: 10,
    currency: 'EUR',
    exchange_rate: 1,
    amount_base: 10,
    paid_by_id: null,
    paid_by_common: false,
    split_mode: 'equal',
    shares: [],
    notes: null,
    ...overrides,
  }
}

const noPlace = () => 'Sin sitio'

describe('filterExpenses', () => {
  it('combina búsqueda, exclusiones y rango de fechas', () => {
    const items = [
      makeExpense({ description: 'Sushi', day: '2026-02-10', category: 'Comida' }),
      makeExpense({ description: 'Hotel', day: '2026-02-11', category: 'Alojamiento' }),
      makeExpense({ description: 'Sushi premium', day: '2026-02-15', category: 'Comida' }),
    ]
    const f = emptyFilters()
    f.searchText = 'sushi'
    f.excludedCategories = ['Alojamiento']
    f.dateTo = new Date(2026, 1, 12)
    const result = filterExpenses(items, f, noPlace)
    expect(result.map((e) => e.description)).toEqual(['Sushi'])
  })

  it('filtra por pagador y sitio con los valores especiales none/all/common', () => {
    const items = [
      makeExpense({ paid_by_id: 1, place_id: 5 }),
      makeExpense({ paid_by_id: null, place_id: null }),
      makeExpense({ paid_by_common: true }),
    ]
    const f = emptyFilters()
    f.payer = 'none'
    // "sin asignar" no incluye los del fondo común
    expect(filterExpenses(items, f, noPlace)).toHaveLength(1)
    f.payer = 'common'
    expect(filterExpenses(items, f, noPlace)).toHaveLength(1)
    expect(filterExpenses(items, f, noPlace)[0].paid_by_common).toBe(true)
    f.payer = 1
    expect(filterExpenses(items, f, noPlace)).toHaveLength(1)
    f.payer = 'all'
    f.place = 'none'
    expect(filterExpenses(items, f, noPlace)).toHaveLength(2)
  })

  it('busca también en el nombre del sitio', () => {
    const items = [makeExpense({ place_id: 7, description: 'Entrada' })]
    const f = emptyFilters()
    f.searchText = 'louvre'
    expect(filterExpenses(items, f, () => 'Museo del Louvre')).toHaveLength(1)
    expect(filterExpenses(items, f, noPlace)).toHaveLength(0)
  })
})

describe('countActiveFilters', () => {
  it('cuenta cada filtro activo', () => {
    const f = emptyFilters()
    expect(countActiveFilters(f)).toBe(0)
    f.searchText = 'x'
    f.category = 'Comida'
    f.dateFrom = new Date(2026, 0, 1)
    expect(countActiveFilters(f)).toBe(3)
  })
})

describe('computeStats / tripDayCount', () => {
  it('usa las fechas del viaje cuando existen', () => {
    const days = tripDayCount('2026-02-10', '2026-02-14', [])
    expect(days).toBe(5)
    const stats = computeStats([makeExpense({ amount_base: 100 })], 2, days)
    expect(stats.total).toBe(100)
    expect(stats.perPerson).toBe(50)
    expect(stats.perDay).toBe(20)
    expect(stats.perDayPerson).toBe(10)
  })

  it('sin fechas cuenta días distintos con gasto', () => {
    const items = [
      makeExpense({ day: '2026-02-10' }),
      makeExpense({ day: '2026-02-10' }),
      makeExpense({ day: '2026-02-11' }),
    ]
    expect(tripDayCount(null, null, items)).toBe(2)
    expect(tripDayCount(null, null, [])).toBeNull()
  })

  it('sin viajeros ni días devuelve nulls', () => {
    const stats = computeStats([], 0, null)
    expect(stats.perPerson).toBeNull()
    expect(stats.perDay).toBeNull()
    expect(stats.perDayPerson).toBeNull()
  })
})

describe('currencyBreakdown', () => {
  it('agrupa solo monedas distintas de la base', () => {
    const items = [
      makeExpense({ currency: 'EUR', amount: 10 }),
      makeExpense({ currency: 'JPY', amount: 1000 }),
      makeExpense({ currency: 'JPY', amount: 500 }),
    ]
    expect(currencyBreakdown(items, 'EUR')).toEqual([['JPY', 1500]])
  })
})

describe('aggregate / cumulative', () => {
  it('suma amount_base por clave', () => {
    const items = [
      makeExpense({ category: 'Comida', amount_base: 10 }),
      makeExpense({ category: 'Comida', amount_base: 5 }),
      makeExpense({ category: 'Tours', amount_base: 20 }),
    ]
    const series = aggregate(items, (e) => e.category)
    expect(series).toEqual([
      { label: 'Comida', value: 15 },
      { label: 'Tours', value: 20 },
    ])
  })

  it('acumula preservando labels', () => {
    expect(
      cumulative([
        { label: 'a', value: 1 },
        { label: 'b', value: 2 },
        { label: 'c', value: 3 },
      ]),
    ).toEqual([
      { label: 'a', value: 1 },
      { label: 'b', value: 3 },
      { label: 'c', value: 6 },
    ])
  })
})

describe('sortRows / groupTotals', () => {
  const rows = buildRows(
    [
      makeExpense({ day: '2026-02-10', category: 'B', amount_base: 10 }),
      makeExpense({ day: '2026-02-12', category: 'A', amount_base: 20 }),
      makeExpense({ day: '2026-02-11', category: 'A', amount_base: 5 }),
    ],
    () => 'Ana',
    noPlace,
  )

  it('sin agrupar ordena por día descendente', () => {
    expect(sortRows(rows, 'none').map((r) => r.day)).toEqual([
      '2026-02-12',
      '2026-02-11',
      '2026-02-10',
    ])
  })

  it('agrupado por categoría ordena por categoría y luego día desc', () => {
    const sorted = sortRows(rows, 'category')
    expect(sorted.map((r) => `${r.category}:${r.day}`)).toEqual([
      'A:2026-02-12',
      'A:2026-02-11',
      'B:2026-02-10',
    ])
  })

  it('por pagador: fondo común primero, viajeros alfabéticos, sin asignar al final', () => {
    const mixed = [
      makeExpense({ paid_by_id: null }),
      makeExpense({ paid_by_id: 2 }),
      makeExpense({ paid_by_common: true }),
      makeExpense({ paid_by_id: 1 }),
    ]
    const rows2 = buildRows(
      mixed,
      (e) => (e.paid_by_common ? 'Fondo común' : e.paid_by_id === 1 ? 'Ana' : e.paid_by_id === 2 ? 'Luis' : 'Sin asignar'),
      noPlace,
    )
    expect(sortRows(rows2, 'payer_name').map((r) => r.payer_name)).toEqual([
      'Fondo común',
      'Ana',
      'Luis',
      'Sin asignar',
    ])
  })

  it('groupTotals suma y cuenta por grupo', () => {
    const totals = groupTotals(sortRows(rows, 'category'), 'category')
    expect(totals.get('A')).toEqual({ total: 25, count: 2 })
    expect(totals.get('B')).toEqual({ total: 10, count: 1 })
    expect(groupTotals(rows, 'none').size).toBe(0)
  })
})
