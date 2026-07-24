import type { SplitMode } from '../api/types'

/** Reparto a partes iguales en céntimos por mayor resto: la suma cuadra exacta. */
export function equalSplit(total: number, n: number): number[] {
  if (n <= 0) return []
  const cents = Math.round(total * 100)
  const floor = Math.floor(cents / n)
  const remainder = cents - floor * n
  return Array.from({ length: n }, (_, i) => (floor + (i < remainder ? 1 : 0)) / 100)
}

/** Suma de los valores rellenos, redondeada a céntimos. */
export function sumValues(values: (number | null)[]): number {
  return Math.round(values.reduce((acc: number, v) => acc + (v ?? 0), 0) * 100) / 100
}

/**
 * Rellena los huecos (null/0) repartiendo lo que falta hasta `total` a partes
 * iguales; los valores ya escritos no se tocan.
 */
export function splitRemaining(total: number, values: (number | null)[]): number[] {
  const missing = values
    .map((v, i) => ({ v, i }))
    .filter(({ v }) => v == null || v === 0)
    .map(({ i }) => i)
  const assigned = sumValues(values)
  const result = values.map((v) => v ?? 0)
  if (!missing.length) return result
  const parts = equalSplit(Math.max(0, total - assigned), missing.length)
  missing.forEach((idx, k) => {
    result[idx] = parts[k]
  })
  return result
}

/** Valida un reparto; devuelve un mensaje en español o null si es correcto. */
export function validateSplit(
  mode: SplitMode,
  total: number,
  values: (number | null)[],
): string | null {
  if (!values.length) return 'Selecciona al menos un participante'
  if (mode === 'equal') return null
  if (values.some((v) => v == null)) return 'Indica el valor de cada participante'
  const sum = sumValues(values)
  const expected = mode === 'amount' ? Math.round(total * 100) / 100 : 100
  if (sum !== expected) {
    return mode === 'amount'
      ? `Los importes suman ${sum} y el gasto es ${expected}`
      : `Los porcentajes suman ${sum} y deben sumar 100`
  }
  return null
}
