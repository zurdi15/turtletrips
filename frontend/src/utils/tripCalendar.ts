/**
 * Marcar los días del viaje dentro de un calendario.
 *
 * Cuando apuntas una reserva, una actividad o un gasto, lo que quieres ver de
 * un vistazo es DÓNDE cae dentro del viaje: la franja pintada es el viaje
 * entero, y encima de ella el DatePicker sigue pintando lo que selecciones.
 */

/** el día tal y como lo describe el DatePicker de PrimeVue (mes 0-11) */
export interface CalendarDay {
  day: number
  month: number
  year: number
  otherMonth?: boolean
}

/** clave comparable YYYYMMDD; evita comparar Date con horas de por medio */
export function dayKey(year: number, month: number, day: number): number {
  return year * 10000 + month * 100 + day
}

export function dateKey(d: Date): number {
  return dayKey(d.getFullYear(), d.getMonth(), d.getDate())
}

/**
 * Una fecha ISO ("2026-09-05") a clave, SIN pasar por Date: `new Date('...')`
 * la interpreta en UTC y en zonas al oeste retrocede un día — el viaje
 * empezaría a pintarse la víspera.
 */
export function isoKey(iso: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso)
  return m ? dayKey(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : null
}

export function keyOf(value: Date | string | null | undefined): number | null {
  if (!value) return null
  return typeof value === 'string' ? isoKey(value) : dateKey(value)
}

/** días que tiene un mes (mes 0-11), para saber si hay semana debajo */
function daysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

/**
 * Clases de la franja del viaje para un día del calendario: vacío fuera del
 * viaje, y dentro los extremos cierran su lado. Los días de los meses vecinos
 * se quedan sin marcar (el DatePicker los pinta apagados y la franja los haría
 * parecer parte del viaje en un mes que no toca).
 *
 * `open-top`/`open-bottom` marcan que la casilla de la MISMA columna en la
 * semana de arriba o de abajo también es del viaje: ahí se quita la línea
 * horizontal y las semanas se funden en un área en vez de quedar en franjas
 * sueltas. Se exige que esa casilla caiga dentro del mes, porque los días del
 * mes vecino no llevan marca y abrir contra ellos dejaría el área descosida.
 */
export function tripSpanClass(
  meta: CalendarDay,
  start: Date | string | null | undefined,
  end: Date | string | null | undefined,
): string {
  return spanClasses(meta, keyOf(start), keyOf(end), 'tt-trip-day')
}

/**
 * La misma geometría de área, con el prefijo que se le pida: la usan la franja
 * del viaje y el relleno de la selección (y del hover), para que los dos se
 * dibujen con la misma forma y encajen uno dentro del otro.
 */
export function spanClasses(
  meta: CalendarDay,
  from: number | null,
  to: number | null,
  prefix: string,
): string {
  if (meta.otherMonth) return ''
  // sin los dos extremos no hay área que pintar
  if (from == null || to == null || to < from) return ''
  const inside = (day: number) => {
    const k = dayKey(meta.year, meta.month, day)
    return k >= from && k <= to
  }
  if (!inside(meta.day)) return ''

  // la casilla de arriba/abajo es el MISMO día de semana: siete días
  const fuseTop = meta.day > 7 && inside(meta.day - 7)
  const fuseBottom =
    meta.day + 7 <= daysInMonth(meta.year, meta.month) && inside(meta.day + 7)

  const classes = [prefix]
  const k = dayKey(meta.year, meta.month, meta.day)
  if (k === from) classes.push(`${prefix}-first`)
  if (k === to) classes.push(`${prefix}-last`)
  if (fuseTop) classes.push(`${prefix}-open-top`)
  if (fuseBottom) classes.push(`${prefix}-open-bottom`)
  return classes.join(' ')
}
