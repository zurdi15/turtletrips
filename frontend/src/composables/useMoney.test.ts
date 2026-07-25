import { beforeAll, describe, expect, it } from 'vitest'
import { formatMoney, parseIsoDate, toIsoDate } from './useMoney'
import { i18n } from '../i18n'

// en Node el idioma detectado es en; estos asserts son de formato es-ES
beforeAll(() => {
  i18n.global.locale.value = 'es'
})

describe('toIsoDate', () => {
  it('formatea en local sin sorpresas de zona horaria', () => {
    expect(toIsoDate(new Date(2026, 6, 24))).toBe('2026-07-24')
    expect(toIsoDate(new Date(2026, 0, 1))).toBe('2026-01-01')
  })

  it('hace roundtrip con parseIsoDate', () => {
    expect(toIsoDate(parseIsoDate('2026-01-01'))).toBe('2026-01-01')
    expect(toIsoDate(parseIsoDate('2026-12-31'))).toBe('2026-12-31')
  })
})

describe('formatMoney', () => {
  it('formatea EUR en es-ES', () => {
    // NBSP entre cifra y símbolo según Intl
    expect(formatMoney(1234.5, 'EUR').replace(/ /g, ' ')).toBe('1234,50 €')
  })

  it('no revienta con una moneda desconocida', () => {
    expect(formatMoney(10, 'XXXX')).toContain('10')
  })
})
