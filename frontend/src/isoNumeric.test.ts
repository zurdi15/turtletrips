import { describe, expect, it } from 'vitest'
import { ALPHA2_BY_NUMERIC, alpha2FromNumeric } from './isoNumeric'
import { COUNTRIES } from './countries'

describe('alpha2FromNumeric', () => {
  it('traduce el código numérico de un feature', () => {
    expect(alpha2FromNumeric('724')).toBe('ES')
    expect(alpha2FromNumeric(724)).toBe('ES')
    expect(alpha2FromNumeric('4')).toBe('AF') // rellena a 3 dígitos
  })

  it('devuelve null para lo que no es un país ISO', () => {
    expect(alpha2FromNumeric(undefined)).toBeNull()
    expect(alpha2FromNumeric(null)).toBeNull()
    expect(alpha2FromNumeric('-99')).toBeNull()
    expect(alpha2FromNumeric('999')).toBeNull()
  })
})

describe('tabla ISO', () => {
  it('cubre todos los países del selector', () => {
    const known = new Set(Object.values(ALPHA2_BY_NUMERIC))
    const missing = COUNTRIES.map((c) => c.code).filter((code) => !known.has(code))
    expect(missing).toEqual([])
  })

  it('no repite alpha-2', () => {
    const values = Object.values(ALPHA2_BY_NUMERIC)
    expect(new Set(values).size).toBe(values.length)
  })
})
