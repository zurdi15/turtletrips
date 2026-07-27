import { describe, expect, it } from 'vitest'
import { CONTINENT_BY_CODE, continentStats } from './continents'
import { COUNTRIES } from './countries'

describe('continentes', () => {
  it('cubre TODOS los países de la app (sin huérfanos)', () => {
    const missing = COUNTRIES.filter((c) => !CONTINENT_BY_CODE.has(c.code)).map((c) => c.code)
    expect(missing).toEqual([])
  })

  it('asignaciones de referencia', () => {
    expect(CONTINENT_BY_CODE.get('ES')).toBe('europe')
    expect(CONTINENT_BY_CODE.get('JP')).toBe('asia')
    expect(CONTINENT_BY_CODE.get('MX')).toBe('northAmerica')
    expect(CONTINENT_BY_CODE.get('AR')).toBe('southAmerica')
    expect(CONTINENT_BY_CODE.get('EG')).toBe('africa')
    expect(CONTINENT_BY_CODE.get('NZ')).toBe('oceania')
  })

  it('cuenta visitados por continente (dedupe y desconocidos fuera)', () => {
    const stats = continentStats(['ES', 'ES', 'FR', 'JP', 'XX'])
    const byKey = new Map(stats.map((s) => [s.key, s]))
    expect(byKey.get('europe')!.visited).toBe(2)
    expect(byKey.get('asia')!.visited).toBe(1)
    expect(byKey.get('africa')!.visited).toBe(0)
    // los totales de los 6 continentes suman el listado completo
    expect(stats.reduce((acc, s) => acc + s.total, 0)).toBe(COUNTRIES.length)
  })
})
