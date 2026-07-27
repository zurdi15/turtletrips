import type { ChecklistItem } from '../api/types'

/** pendientes primero (por fecha límite, sin fecha al final), hechas al fondo */
export function sortChecklist(items: ChecklistItem[]): ChecklistItem[] {
  return [...items].sort((a, b) => {
    if (a.done !== b.done) return a.done ? 1 : -1
    const dueA = a.due_date ?? '9999-12-31'
    const dueB = b.due_date ?? '9999-12-31'
    return dueA.localeCompare(dueB) || a.id - b.id
  })
}

/** pendiente con la fecha límite ya pasada (ISO yyyy-mm-dd compara bien como string) */
export function isOverdue(item: ChecklistItem, todayIso: string): boolean {
  return !item.done && item.due_date != null && item.due_date < todayIso
}
