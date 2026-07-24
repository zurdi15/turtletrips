import { describe, expect, it } from 'vitest'
import type { WorldPlace } from '../api/types'
import {
  displayName,
  emptyWorldFilters,
  filterWorldPlaces,
  groupByCountry,
  inferCountryCode,
  worldStats,
} from './worldGrouping'

let nextId = 1
function makePlace(overrides: Partial<WorldPlace> = {}): WorldPlace {
  return {
    id: nextId++,
    name: 'Lugar',
    kind: 'city',
    country_code: null,
    lat: null,
    lon: null,
    note: null,
    auto: false,
    origin: null,
    ...overrides,
  }
}

describe('groupByCountry', () => {
  it('pone "Sin país" al final y ordena países alfabéticamente', () => {
    const groups = groupByCountry([
      makePlace({ country_code: null, name: 'Perdido' }),
      makePlace({ kind: 'country', country_code: 'JP', name: 'JP' }),
      makePlace({ kind: 'country', country_code: 'ES', name: 'ES' }),
    ])
    expect(groups.map((g) => g.code)).toEqual(['ES', 'JP', null])
  })

  it('ordena hijos: ciudades antes que sitios, y alfabético dentro', () => {
    const groups = groupByCountry([
      makePlace({ country_code: 'ES', kind: 'place', name: 'Alhambra' }),
      makePlace({ country_code: 'ES', kind: 'city', name: 'Sevilla' }),
      makePlace({ country_code: 'ES', kind: 'city', name: 'Granada' }),
    ])
    expect(groups[0].children.map((c) => c.name)).toEqual(['Granada', 'Sevilla', 'Alhambra'])
  })

  it('la entrada country preside el grupo sin colgar de children', () => {
    const groups = groupByCountry([
      makePlace({ kind: 'country', country_code: 'JP' }),
      makePlace({ kind: 'city', country_code: 'JP', name: 'Tokio' }),
    ])
    expect(groups[0].entry?.kind).toBe('country')
    expect(groups[0].children).toHaveLength(1)
  })
})

describe('filterWorldPlaces', () => {
  const items = [
    makePlace({ kind: 'country', country_code: 'JP', auto: true, origin: 'Japón 2026' }),
    makePlace({ kind: 'city', country_code: 'ES', name: 'Sevilla', note: 'tapas' }),
  ]

  it('filtra por tipo, origen y país', () => {
    const f = emptyWorldFilters()
    f.kind = 'city'
    expect(filterWorldPlaces(items, f)).toHaveLength(1)
    f.kind = 'all'
    f.source = 'auto'
    expect(filterWorldPlaces(items, f)[0].country_code).toBe('JP')
    f.source = 'all'
    f.country = 'ES'
    expect(filterWorldPlaces(items, f)[0].name).toBe('Sevilla')
  })

  it('busca en nombre traducido, nota y viaje de origen', () => {
    const f = emptyWorldFilters()
    f.searchText = 'japón'
    // el país auto JP se llama "JP" pero displayName lo traduce
    expect(filterWorldPlaces(items, f)).toHaveLength(1)
    f.searchText = 'tapas'
    expect(filterWorldPlaces(items, f)[0].name).toBe('Sevilla')
  })
})

describe('worldStats', () => {
  it('cuenta por tipo y calcula % del mundo', () => {
    const stats = worldStats(
      [
        makePlace({ kind: 'country', country_code: 'ES' }),
        makePlace({ kind: 'city', note: 'x' }),
        makePlace({ kind: 'place' }),
      ],
      100,
    )
    expect(stats).toEqual({ countries: 1, worldPct: 1, cities: 1, places: 1, notes: 1 })
  })
})

describe('inferCountryCode / displayName', () => {
  it('deduce el país del display_name de Nominatim', () => {
    expect(inferCountryCode('Sevilla, Andalucía, España')).toBe('ES')
    expect(inferCountryCode('Somewhere, Atlantis')).toBeNull()
  })

  it('traduce el nombre de los países auto', () => {
    expect(displayName(makePlace({ kind: 'country', country_code: 'ES', name: 'ES' }))).toBe(
      'España',
    )
    expect(displayName(makePlace({ kind: 'city', name: 'Tokio' }))).toBe('Tokio')
  })
})
