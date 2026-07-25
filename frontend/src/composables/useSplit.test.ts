import { describe, expect, it } from 'vitest'
import { equalSplit, splitRemaining, sumValues, validateSplit } from './useSplit'

describe('equalSplit', () => {
  it('reparte exacto en céntimos con mayor resto', () => {
    expect(equalSplit(100, 3)).toEqual([33.34, 33.33, 33.33])
    expect(equalSplit(10, 4)).toEqual([2.5, 2.5, 2.5, 2.5])
    expect(equalSplit(0.05, 2)).toEqual([0.03, 0.02])
  })

  it('la suma siempre cuadra', () => {
    for (const [total, n] of [
      [99.99, 7],
      [0.01, 3],
      [123.45, 6],
    ] as const) {
      const parts = equalSplit(total, n)
      expect(Math.round(parts.reduce((a, b) => a + b, 0) * 100) / 100).toBe(total)
    }
  })

  it('casos degenerados', () => {
    expect(equalSplit(10, 0)).toEqual([])
  })
})

describe('splitRemaining', () => {
  it('rellena los huecos con lo que falta', () => {
    expect(splitRemaining(100, [40, null, null])).toEqual([40, 30, 30])
    expect(splitRemaining(100, [null, null, null])).toEqual([33.34, 33.33, 33.33])
  })

  it('no toca los valores escritos y no va a negativo', () => {
    expect(splitRemaining(50, [60, null])).toEqual([60, 0])
    expect(splitRemaining(100, [25, 75])).toEqual([25, 75])
  })
})

describe('validateSplit', () => {
  it('equal solo exige participantes', () => {
    expect(validateSplit('equal', 100, [])).toEqual({
      key: 'expenses.split.errors.noParticipants',
    })
    expect(validateSplit('equal', 100, [null, null])).toBeNull()
  })

  it('amount exige valores que sumen el total', () => {
    expect(validateSplit('amount', 100, [50, null])).toEqual({
      key: 'expenses.split.errors.missingValues',
    })
    expect(validateSplit('amount', 100, [50, 40])).toEqual({
      key: 'expenses.split.errors.amountSum',
      params: { sum: 90, expected: 100 },
    })
    expect(validateSplit('amount', 100, [50, 50])).toBeNull()
  })

  it('percent exige sumar 100', () => {
    expect(validateSplit('percent', 80, [50, 40])).toEqual({
      key: 'expenses.split.errors.percentSum',
      params: { sum: 90 },
    })
    expect(validateSplit('percent', 80, [60, 40])).toBeNull()
  })
})

describe('sumValues', () => {
  it('ignora nulls y evita errores de coma flotante', () => {
    expect(sumValues([0.1, 0.2, null])).toBe(0.3)
  })
})
