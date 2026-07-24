import { parseIsoDate, toIsoDate } from '../composables/useMoney'

export const DAY_MS = 86_400_000

/** Días de diferencia entre dos fechas ISO (redondeado; mismo día = 0). */
export function daysBetween(fromIso: string, toIso: string): number {
  return Math.round((parseIsoDate(toIso).getTime() - parseIsoDate(fromIso).getTime()) / DAY_MS)
}

/**
 * Días que faltan desde hoy (medianoche local) hasta la fecha.
 * null si no hay fecha o ya ha llegado — los consumidores muestran "—" o nada.
 */
export function daysUntil(iso: string | null | undefined, now: Date = new Date()): number | null {
  if (!iso) return null
  const today = new Date(now).setHours(0, 0, 0, 0)
  const diff = Math.ceil((parseIsoDate(iso).getTime() - today) / DAY_MS)
  return diff > 0 ? diff : null
}

/** Fecha ISO desplazada n días (n puede ser negativo). */
export function addDays(iso: string, n: number): string {
  const d = parseIsoDate(iso)
  d.setDate(d.getDate() + n)
  return toIsoDate(d)
}

/** Todas las fechas ISO del rango, ambos extremos incluidos. */
export function eachDayInclusive(fromIso: string, toIso: string): string[] {
  const days: string[] = []
  const end = parseIsoDate(toIso).getTime()
  for (const d = parseIsoDate(fromIso); d.getTime() <= end; d.setDate(d.getDate() + 1)) {
    days.push(toIsoDate(d))
  }
  return days
}
