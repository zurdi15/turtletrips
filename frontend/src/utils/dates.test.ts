import { describe, expect, it } from 'vitest'
import { addDays, daysBetween, daysUntil, eachDayInclusive } from './dates'

describe('daysBetween', () => {
  it('mismo día = 0, orden natural positivo', () => {
    expect(daysBetween('2026-07-01', '2026-07-01')).toBe(0)
    expect(daysBetween('2026-07-01', '2026-07-05')).toBe(4)
    expect(daysBetween('2026-07-05', '2026-07-01')).toBe(-4)
  })
  it('cruza cambios de mes y año', () => {
    expect(daysBetween('2026-12-30', '2027-01-02')).toBe(3)
  })
})

describe('daysUntil', () => {
  const now = new Date('2026-07-24T15:30:00')
  it('futuro: días restantes contando desde medianoche', () => {
    expect(daysUntil('2026-07-25', now)).toBe(1)
    expect(daysUntil('2026-08-01', now)).toBe(8)
  })
  it('hoy o pasado: null', () => {
    expect(daysUntil('2026-07-24', now)).toBeNull()
    expect(daysUntil('2026-07-20', now)).toBeNull()
  })
  it('sin fecha: null', () => {
    expect(daysUntil(null, now)).toBeNull()
    expect(daysUntil(undefined, now)).toBeNull()
  })
})

describe('addDays', () => {
  it('suma y resta cruzando meses', () => {
    expect(addDays('2026-07-31', 1)).toBe('2026-08-01')
    expect(addDays('2026-08-01', -1)).toBe('2026-07-31')
    expect(addDays('2026-02-28', 1)).toBe('2026-03-01')
  })
})

describe('eachDayInclusive', () => {
  it('incluye ambos extremos', () => {
    expect(eachDayInclusive('2026-07-30', '2026-08-02')).toEqual([
      '2026-07-30',
      '2026-07-31',
      '2026-08-01',
      '2026-08-02',
    ])
  })
  it('rango de un día', () => {
    expect(eachDayInclusive('2026-07-24', '2026-07-24')).toEqual(['2026-07-24'])
  })
  it('rango invertido: vacío', () => {
    expect(eachDayInclusive('2026-07-24', '2026-07-23')).toEqual([])
  })
})
