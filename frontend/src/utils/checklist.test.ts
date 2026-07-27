import { describe, expect, it } from 'vitest'
import type { ChecklistItem } from '../api/types'
import { isOverdue, sortChecklist } from './checklist'

let nextId = 1
function makeItem(overrides: Partial<ChecklistItem> = {}): ChecklistItem {
  return {
    id: nextId++,
    trip_id: 1,
    title: 'Tarea',
    done: false,
    due_date: null,
    url: null,
    notes: null,
    ...overrides,
  }
}

describe('sortChecklist', () => {
  it('pendientes por fecha (sin fecha al final) y hechas al fondo', () => {
    const done = makeItem({ done: true, due_date: '2026-01-01', title: 'hecha' })
    const noDue = makeItem({ title: 'sin fecha' })
    const soon = makeItem({ due_date: '2026-02-01', title: 'pronto' })
    const later = makeItem({ due_date: '2026-03-01', title: 'después' })
    expect(sortChecklist([done, noDue, later, soon]).map((i) => i.title)).toEqual([
      'pronto',
      'después',
      'sin fecha',
      'hecha',
    ])
  })
})

describe('isOverdue', () => {
  it('solo pendientes con fecha pasada', () => {
    const today = '2026-07-27'
    expect(isOverdue(makeItem({ due_date: '2026-07-26' }), today)).toBe(true)
    expect(isOverdue(makeItem({ due_date: '2026-07-27' }), today)).toBe(false)
    expect(isOverdue(makeItem({ due_date: '2026-07-26', done: true }), today)).toBe(false)
    expect(isOverdue(makeItem(), today)).toBe(false)
  })
})
