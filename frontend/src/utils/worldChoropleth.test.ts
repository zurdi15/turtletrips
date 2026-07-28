import { describe, expect, it } from 'vitest'
import type { WorldPlace } from '../api/types'
import { buildCountryStates, fillOpacityFor, visitedCodes } from './worldChoropleth'

function place(over: Partial<WorldPlace>): WorldPlace {
  return {
    id: 1,
    name: 'X',
    kind: 'place',
    country_code: 'ES',
    lat: null,
    lon: null,
    note: null,
    visited_year: null,
    visited_month: null,
    photo_url: null,
    auto: false,
    origin: null,
    ...over,
  } as WorldPlace
}

describe('buildCountryStates', () => {
  it('marca el país y guarda su id y su año', () => {
    const states = buildCountryStates([
      place({ id: 7, kind: 'country', country_code: 'JP', visited_year: 2024 }),
    ])
    expect(states.get('JP')).toEqual({
      status: 'visited', placeId: 7, year: 2024, cities: 0, regions: 0,
    })
  })

  it('cuenta ciudades y sitios del país', () => {
    const states = buildCountryStates([
      place({ id: 1, kind: 'country', country_code: 'ES' }),
      place({ id: 2, kind: 'city', country_code: 'ES' }),
      place({ id: 3, kind: 'place', country_code: 'ES' }),
    ])
    expect(states.get('ES')?.cities).toBe(2)
  })

  it('una ciudad sin entrada de país ya pinta el país', () => {
    const states = buildCountryStates([place({ id: 2, kind: 'city', country_code: 'PT' })])
    expect(states.get('PT')?.status).toBe('visited')
    expect(states.get('PT')?.placeId).toBeNull()
  })

  it('ignora las entradas sin país', () => {
    expect(buildCountryStates([place({ country_code: null })]).size).toBe(0)
  })
})

describe('fillOpacityFor', () => {
  it('no pinta lo no visitado', () => {
    expect(fillOpacityFor(undefined)).toBe(0)
    expect(
      fillOpacityFor({ status: 'none', placeId: null, year: null, cities: 0, regions: 0 }),
    ).toBe(0)
  })

  it('sube con las ciudades y se estanca en el tope', () => {
    const base = { status: 'visited' as const, placeId: 1, year: null, regions: 0 }
    const none = fillOpacityFor({ ...base, cities: 0 })
    const some = fillOpacityFor({ ...base, cities: 3 })
    const many = fillOpacityFor({ ...base, cities: 40 })
    expect(some).toBeGreaterThan(none)
    expect(many).toBeGreaterThan(some)
    expect(many).toBe(fillOpacityFor({ ...base, cities: 4 }))
    expect(many).toBeLessThanOrEqual(0.4)
  })
})

describe('regiones', () => {
  it('las cuenta aparte de las ciudades y también pintan el país', () => {
    const states = buildCountryStates([
      place({ id: 1, kind: 'region', country_code: 'ES', region_code: 'ES-CT' }),
      place({ id: 2, kind: 'region', country_code: 'ES', region_code: 'ES-AR' }),
      place({ id: 3, kind: 'city', country_code: 'ES' }),
    ])
    expect(states.get('ES')).toMatchObject({ status: 'visited', regions: 2, cities: 1 })
  })

  it('suman a la intensidad del relleno igual que las ciudades', () => {
    const withRegions = { status: 'visited' as const, placeId: 1, year: null, cities: 0, regions: 2 }
    const withCities = { status: 'visited' as const, placeId: 1, year: null, cities: 2, regions: 0 }
    expect(fillOpacityFor(withRegions)).toBe(fillOpacityFor(withCities))
  })
})

describe('visitedCodes', () => {
  it('devuelve solo los marcados', () => {
    const states = buildCountryStates([
      place({ id: 1, kind: 'country', country_code: 'ES' }),
      place({ id: 2, kind: 'country', country_code: 'FR' }),
    ])
    expect(visitedCodes(states).sort()).toEqual(['ES', 'FR'])
  })
})
