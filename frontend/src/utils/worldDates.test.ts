import { describe, expect, it } from 'vitest'
import { FIRST_VISIT_YEAR, visitMonths, visitYears } from './worldDates'

describe('visitYears', () => {
  it('va del año dado hacia atrás hasta 1950', () => {
    const years = visitYears(2026)
    expect(years[0]).toBe(2026)
    expect(years.at(-1)).toBe(FIRST_VISIT_YEAR)
    expect(years).toHaveLength(2026 - FIRST_VISIT_YEAR + 1)
  })

  it('no repite años ni se salta ninguno', () => {
    const years = visitYears(2000)
    expect(new Set(years).size).toBe(years.length)
    expect(years.every((y, i) => i === 0 || y === years[i - 1] - 1)).toBe(true)
  })

  it('un año anterior al primero no ofrece nada (en vez de un array al revés)', () => {
    expect(visitYears(1900)).toEqual([])
  })
})

describe('visitMonths', () => {
  it('son doce, numerados 1-12 como en la API', () => {
    const months = visitMonths('es-ES')
    expect(months).toHaveLength(12)
    expect(months.map((m) => m.value)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
  })

  it('sigue el idioma que se le pasa', () => {
    expect(visitMonths('es-ES')[0].label).toBe('enero')
    expect(visitMonths('en-GB')[0].label).toBe('January')
  })
})
