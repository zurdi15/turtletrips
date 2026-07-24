import { defineStore } from 'pinia'
import type { Category } from '../api/types'
import { useGlobalResource } from './globalResource'
import { FALLBACK_COLOR } from '../theme'

// alias histórico: mismo fallback para categorías y viajeros
export const FALLBACK_CATEGORY_COLOR = FALLBACK_COLOR

type Kind = 'expense' | 'packing'

interface CategoryPayload {
  name?: string
  color?: string | null
}

export const useCategoriesStore = defineStore('categories', () => {
  // dos colecciones independientes (gastos y maleta) sobre la misma base
  const kinds: Record<Kind, ReturnType<typeof makeKind>> = {
    expense: makeKind('expense'),
    packing: makeKind('packing'),
  }

  function makeKind(kind: Kind) {
    return useGlobalResource<Category, CategoryPayload & { kind: Kind }, CategoryPayload>({
      listPath: `/categories?kind=${kind}`,
      itemPath: (id) => `/categories/${id}`,
    })
  }

  function colorOf(kind: Kind, name: string): string {
    return kinds[kind].items.value.find((c) => c.name === name)?.color ?? FALLBACK_CATEGORY_COLOR
  }

  return {
    expense: kinds.expense.items,
    packing: kinds.packing.items,
    colorOf,
    load: (kind: Kind, force = false) => kinds[kind].load(force),
    create: (kind: Kind, name: string, color: string) => kinds[kind].create({ kind, name, color }),
    update: (id: number, kind: Kind, payload: CategoryPayload) => kinds[kind].update(id, payload),
    remove: (id: number, kind: Kind) => kinds[kind].remove(id),
  }
})
