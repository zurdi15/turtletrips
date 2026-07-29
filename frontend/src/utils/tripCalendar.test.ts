import { describe, expect, it } from 'vitest'
import { dateKey, isoKey, tripSpanClass, type CalendarDay } from './tripCalendar'

const day = (y: number, m: number, d: number, otherMonth = false): CalendarDay => ({
  year: y,
  month: m,
  day: d,
  otherMonth,
})

describe('isoKey', () => {
  it('no pasa por Date: una fecha ISO no puede retroceder un día por la zona horaria', () => {
    expect(isoKey('2026-09-05')).toBe(dateKey(new Date(2026, 8, 5)))
  })

  it('acepta la parte de fecha de un datetime y descarta lo que no lo es', () => {
    expect(isoKey('2026-09-05T22:30:00')).toBe(isoKey('2026-09-05'))
    expect(isoKey('mañana')).toBeNull()
  })
})

describe('tripSpanClass', () => {
  const start = '2026-09-05'
  const end = '2026-09-16'

  it('marca los días de dentro y cierra los extremos', () => {
    // 5 y 16 de septiembre: extremos del viaje (el 5 tiene el 12 debajo)
    expect(tripSpanClass(day(2026, 8, 5), start, end)).toBe(
      'tt-trip-day tt-trip-day-first tt-trip-day-open-bottom',
    )
    expect(tripSpanClass(day(2026, 8, 16), start, end)).toBe(
      'tt-trip-day tt-trip-day-last tt-trip-day-open-top',
    )
  })

  it('funde las semanas: la casilla con viaje arriba y abajo abre por los dos lados', () => {
    // el 9 tiene el 2 fuera del viaje y el 16 dentro
    expect(tripSpanClass(day(2026, 8, 9), start, end)).toBe('tt-trip-day tt-trip-day-open-bottom')
    // el 12 tiene el 5 y el 19: el 19 se sale del viaje
    expect(tripSpanClass(day(2026, 8, 12), start, end)).toBe('tt-trip-day tt-trip-day-open-top')
    // en un viaje largo, una casilla del medio abre arriba y abajo
    expect(tripSpanClass(day(2026, 8, 12), '2026-09-01', '2026-09-30')).toBe(
      'tt-trip-day tt-trip-day-open-top tt-trip-day-open-bottom',
    )
  })

  it('no funde contra casillas de otro mes (esas no llevan marca)', () => {
    // 3 de septiembre: el 27 de agosto es del viaje pero cae en el mes vecino
    expect(tripSpanClass(day(2026, 8, 3), '2026-08-25', '2026-09-04')).toBe(
      'tt-trip-day',
    )
    // 28 de septiembre: se funde con el 21 de arriba, pero NO con el 5 de
    // octubre de abajo aunque el viaje siga (ese día ya es del mes vecino)
    expect(tripSpanClass(day(2026, 8, 28), '2026-09-20', '2026-10-06')).toBe(
      'tt-trip-day tt-trip-day-open-top',
    )
  })

  it('deja fuera la víspera y el día siguiente', () => {
    expect(tripSpanClass(day(2026, 8, 4), start, end)).toBe('')
    expect(tripSpanClass(day(2026, 8, 17), start, end)).toBe('')
  })

  it('un viaje de un solo día es principio y fin a la vez, sin fundir con nada', () => {
    expect(tripSpanClass(day(2026, 8, 5), start, start)).toBe(
      'tt-trip-day tt-trip-day-first tt-trip-day-last',
    )
  })

  it('sin las dos fechas no hay duración que pintar', () => {
    expect(tripSpanClass(day(2026, 8, 10), start, null)).toBe('')
    expect(tripSpanClass(day(2026, 8, 10), null, end)).toBe('')
    expect(tripSpanClass(day(2026, 8, 10), null, null)).toBe('')
  })

  it('fechas al revés no pintan nada (en vez de una franja imposible)', () => {
    expect(tripSpanClass(day(2026, 8, 10), end, start)).toBe('')
  })

  it('los días del mes vecino se quedan sin marcar', () => {
    expect(tripSpanClass(day(2026, 8, 5, true), start, end)).toBe('')
  })

  it('acepta Date además de ISO (los formularios manejan Date)', () => {
    expect(tripSpanClass(day(2026, 8, 6), new Date(2026, 8, 5), new Date(2026, 8, 16))).toBe(
      'tt-trip-day tt-trip-day-open-bottom',
    )
  })

  it('cruza el cambio de mes y de año', () => {
    expect(tripSpanClass(day(2026, 11, 31), '2026-12-28', '2027-01-04')).toBe('tt-trip-day')
    expect(tripSpanClass(day(2027, 0, 4), '2026-12-28', '2027-01-04')).toBe(
      'tt-trip-day tt-trip-day-last',
    )
  })
})
