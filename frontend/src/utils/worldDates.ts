/**
 * Opciones de "cuándo lo visité" para el diario del mapa: las comparten el
 * formulario completo y la tarjeta de alta rápida, y el año que ofrecen tiene
 * que ser el mismo en las dos.
 */

/** Primer año que se ofrece: por debajo de esto ya no es un viaje, es genealogía */
export const FIRST_VISIT_YEAR = 1950

/** Años de más reciente a más antiguo (el de arriba es el que más se usa) */
export function visitYears(currentYear = new Date().getFullYear()): number[] {
  const total = Math.max(0, currentYear - FIRST_VISIT_YEAR + 1)
  return Array.from({ length: total }, (_, i) => currentYear - i)
}

/** Meses en el idioma activo; el value es 1-12 como en la API */
export function visitMonths(locale: string): { value: number; label: string }[] {
  return Array.from({ length: 12 }, (_, i) => ({
    value: i + 1,
    label: new Date(2000, i, 1).toLocaleDateString(locale, { month: 'long' }),
  }))
}
