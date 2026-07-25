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

/** Error de validación de un reparto: clave i18n + parámetros del mensaje. */
export interface SplitError {
  key: string
  params?: Record<string, number>
}

/** Valida un reparto; devuelve el error (clave i18n) o null si es correcto. */
export function validateSplit(
  mode: SplitMode,
  total: number,
  values: (number | null)[],
): SplitError | null {
  if (!values.length) return { key: 'expenses.split.errors.noParticipants' }
  if (mode === 'equal') return null
  if (values.some((v) => v == null)) return { key: 'expenses.split.errors.missingValues' }
  const sum = sumValues(values)
  const expected = mode === 'amount' ? Math.round(total * 100) / 100 : 100
  if (sum !== expected) {
    return mode === 'amount'
      ? { key: 'expenses.split.errors.amountSum', params: { sum, expected } }
      : { key: 'expenses.split.errors.percentSum', params: { sum } }
  }
  return null
}
