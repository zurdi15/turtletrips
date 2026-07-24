import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Category } from '../api/types'

export const FALLBACK_CATEGORY_COLOR = '#94a3b8'

export const useCategoriesStore = defineStore('categories', {
  state: () => ({
    expense: [] as Category[],
    packing: [] as Category[],
    loaded: { expense: false, packing: false },
  }),
  getters: {
    colorOf() {
      return (kind: 'expense' | 'packing', name: string): string =>
        this[kind].find((c) => c.name === name)?.color ?? FALLBACK_CATEGORY_COLOR
    },
  },
  actions: {
    async load(kind: 'expense' | 'packing', force = false) {
      if (this.loaded[kind] && !force) return
      this[kind] = await api.get<Category[]>(`/categories?kind=${kind}`)
      this.loaded[kind] = true
    },
    async create(kind: 'expense' | 'packing', name: string, color: string) {
      const category = await api.post<Category>('/categories', { kind, name, color })
      this[kind].push(category)
      return category
    },
    async update(id: number, kind: 'expense' | 'packing', payload: { name?: string; color?: string | null }) {
      const category = await api.patch<Category>(`/categories/${id}`, payload)
      const idx = this[kind].findIndex((c) => c.id === id)
      if (idx >= 0) this[kind][idx] = category
      return category
    },
    async remove(id: number, kind: 'expense' | 'packing') {
      await api.delete(`/categories/${id}`)
      this[kind] = this[kind].filter((c) => c.id !== id)
    },
  },
})
