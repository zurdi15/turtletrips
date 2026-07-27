import { beforeAll, describe, expect, it } from 'vitest'
import type { WorldPlace } from '../api/types'
import { i18n } from '../i18n'
import {
  buildTimeline,
  buildTimelineSegments,
  countWorldFilters,
  displayName,
  sortCountryGroups,
  emptyWorldFilters,
  filterWorldPlaces,
  groupByCountry,
  inferCountryCode,
  visitedLabel,
  worldStats,
} from './worldGrouping'

// countryName (usado por displayName y groupByCountry) depende del locale activo:
// fijarlo a 'es' para que el test no dependa del idioma del entorno
beforeAll(() => {
  i18n.global.locale.value = 'es'
})

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
    visited_year: null,
    visited_month: null,
    photo_url: null,
    auto: false,
    origin: null,
    ...overrides,
  }
}

describe('groupByCountry', () => {
  it('pone "Sin país" al final (title null: lo traduce el componente) y ordena países alfabéticamente', () => {
    const groups = groupByCountry([
      makePlace({ country_code: null, name: 'Perdido' }),
      makePlace({ kind: 'country', country_code: 'JP', name: 'JP' }),
      makePlace({ kind: 'country', country_code: 'ES', name: 'ES' }),
    ])
    expect(groups.map((g) => g.code)).toEqual(['ES', 'JP', null])
    expect(groups[2].title).toBeNull()
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

  it('filtra por tipo, origen y país (multiselección; vacío = sin filtrar)', () => {
    const f = emptyWorldFilters()
    expect(filterWorldPlaces(items, f)).toHaveLength(2)
    f.kinds = ['city']
    expect(filterWorldPlaces(items, f)).toHaveLength(1)
    // varios valores a la vez: unión
    f.kinds = ['city', 'country']
    expect(filterWorldPlaces(items, f)).toHaveLength(2)
    f.kinds = []
    f.sources = ['auto']
    expect(filterWorldPlaces(items, f)[0].country_code).toBe('JP')
    f.sources = []
    f.countries = ['ES']
    expect(filterWorldPlaces(items, f)[0].name).toBe('Sevilla')
    f.countries = ['ES', 'JP']
    expect(filterWorldPlaces(items, f)).toHaveLength(2)
  })

  it('countWorldFilters cuenta un punto por grupo activo, no por valor', () => {
    const f = emptyWorldFilters()
    expect(countWorldFilters(f)).toBe(0)
    f.kinds = ['city', 'country']
    expect(countWorldFilters(f)).toBe(1)
    f.searchText = '  '
    expect(countWorldFilters(f)).toBe(1)
    f.searchText = 'kioto'
    f.years = [2020]
    expect(countWorldFilters(f)).toBe(3)
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
    expect(stats).toEqual({ countries: 1, worldPct: 1, cities: 1, places: 1 })
  })
})

describe('inferCountryCode / displayName', () => {
  it('deduce el país del display_name de Nominatim (nombre en español o en inglés)', () => {
    expect(inferCountryCode('Sevilla, Andalucía, España')).toBe('ES')
    expect(inferCountryCode('Seville, Andalusia, Spain')).toBe('ES')
    expect(inferCountryCode('Somewhere, Atlantis')).toBeNull()
  })

  it('traduce el nombre de los países auto', () => {
    expect(displayName(makePlace({ kind: 'country', country_code: 'ES', name: 'ES' }))).toBe(
      'España',
    )
    expect(displayName(makePlace({ kind: 'city', name: 'Tokio' }))).toBe('Tokio')
  })
})

describe('fecha de visita', () => {
  it('visitedLabel: año solo, mes + año, o null sin fecha', () => {
    expect(visitedLabel(makePlace())).toBeNull()
    expect(visitedLabel(makePlace({ visited_year: 2018 }))).toBe('2018')
    const withMonth = visitedLabel(makePlace({ visited_year: 2018, visited_month: 5 }))
    // el nombre del mes depende del ICU del entorno: basta con que preceda al año
    expect(withMonth).toMatch(/^\S+ 2018$/)
  })

  it('filtra por año de visita (varios años a la vez)', () => {
    const filters = emptyWorldFilters()
    filters.years = [2018]
    const items = [
      makePlace({ visited_year: 2018 }),
      makePlace({ visited_year: 2020 }),
      makePlace(),
    ]
    expect(filterWorldPlaces(items, filters)).toHaveLength(1)
    expect(filterWorldPlaces(items, filters)[0].visited_year).toBe(2018)
    filters.years = [2018, 2020]
    expect(filterWorldPlaces(items, filters)).toHaveLength(2)
    // los que no tienen año quedan fuera de cualquier filtro por año
    expect(filterWorldPlaces(items, filters).every((p) => p.visited_year != null)).toBe(true)
  })

  it('buildTimeline agrupa por año ascendente y ordena mes → tipo → nombre', () => {
    const timeline = buildTimeline([
      makePlace({ name: 'Sin fecha' }),
      makePlace({ name: 'Kioto', kind: 'city', visited_year: 2020, visited_month: 4 }),
      makePlace({ name: 'JP', kind: 'country', country_code: 'JP', visited_year: 2020, visited_month: 4 }),
      makePlace({ name: 'Anual', kind: 'place', visited_year: 2020 }),
      makePlace({ name: 'FR', kind: 'country', country_code: 'FR', visited_year: 2015 }),
    ])
    expect(timeline.map((y) => y.year)).toEqual([2015, 2020])
    // mismo mes: país antes que ciudad; sin mes al final
    expect(timeline[1].entries.map((e) => e.name)).toEqual(['JP', 'Kioto', 'Anual'])
  })

  it('sortCountryGroups ordena por fecha y deja los países sin fecha al final', () => {
    const groups = groupByCountry([
      makePlace({ kind: 'country', country_code: 'ES', name: 'ES', visited_year: 2015, visited_month: 6 }),
      makePlace({ kind: 'country', country_code: 'JP', name: 'JP', visited_year: 2020 }),
      makePlace({ kind: 'country', country_code: 'FR', name: 'FR', visited_year: 2015, visited_month: 2 }),
      makePlace({ kind: 'country', country_code: 'IT', name: 'IT' }),
    ])
    expect(sortCountryGroups(groups, true).map((g) => g.code)).toEqual(['JP', 'ES', 'FR', 'IT'])
    // el mes desempata dentro del año; los sin fecha siguen al final
    expect(sortCountryGroups(groups, false).map((g) => g.code)).toEqual(['FR', 'ES', 'JP', 'IT'])
  })

  it('buildTimelineSegments funde años ocultos en un hueco y cuenta lo filtrado', () => {
    const es = makePlace({ name: 'ES', kind: 'country', country_code: 'ES', visited_year: 2015 })
    const fr = makePlace({ name: 'FR', kind: 'country', country_code: 'FR', visited_year: 2016 })
    const it = makePlace({ name: 'IT', kind: 'country', country_code: 'IT', visited_year: 2017 })
    const jp = makePlace({ name: 'JP', kind: 'country', country_code: 'JP', visited_year: 2020 })
    const kioto = makePlace({ name: 'Kioto', kind: 'city', visited_year: 2020 })
    const all = [es, fr, it, jp, kioto]

    // el filtro deja fuera 2016 y 2017 enteros, y Kioto dentro de 2020
    const segments = buildTimelineSegments(all, [es, jp])
    expect(segments.map((s) => (s.type === 'year' ? s.year : 'gap'))).toEqual([2015, 'gap', 2020])
    // los dos años ocultos consecutivos se funden en UN hueco con su total
    const gap = segments[1]
    expect(gap.type === 'gap' && gap.hidden).toBe(2)
    // el año visible informa de lo que se quedó fuera dentro de él
    const y2020 = segments[2]
    expect(y2020.type === 'year' && y2020.hidden).toBe(1)
    expect(y2020.type === 'year' && y2020.entries.map((e) => e.name)).toEqual(['JP'])
  })
})
