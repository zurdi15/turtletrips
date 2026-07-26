import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { PackingTemplate, PackingTemplateDetail, PackingTemplateItem } from '../api/types'

export const usePackingTemplatesStore = defineStore('packingTemplates', {
  state: () => ({
    templates: [] as PackingTemplate[],
    detail: null as PackingTemplateDetail | null,
    loading: false,
  }),
  actions: {
    async load() {
      this.loading = true
      try {
        this.templates = await api.get<PackingTemplate[]>('/packing-templates')
      } finally {
        this.loading = false
      }
    },
    async select(id: number) {
      this.detail = await api.get<PackingTemplateDetail>(`/packing-templates/${id}`)
    },
    _syncCount() {
      if (!this.detail) return
      const template = this.templates.find((t) => t.id === this.detail!.id)
      if (template) template.item_count = this.detail.items.length
    },
    /** travelerId = dueño de la plantilla (null = el propio usuario) */
    async create(name: string, travelerId: number | null = null) {
      const template = await api.post<PackingTemplate>('/packing-templates', {
        name,
        traveler_id: travelerId,
      })
      this.templates.push(template)
      this.templates.sort((a, b) => a.name.localeCompare(b.name, 'es'))
      return template
    },
    async rename(id: number, name: string) {
      const template = await api.patch<PackingTemplate>(`/packing-templates/${id}`, { name })
      const idx = this.templates.findIndex((t) => t.id === id)
      if (idx >= 0) this.templates[idx] = template
      if (this.detail?.id === id) this.detail.name = template.name
    },
    /** reasigna la plantilla a otro viajero (solo admin) */
    async reassign(id: number, travelerId: number) {
      const template = await api.patch<PackingTemplate>(`/packing-templates/${id}`, {
        traveler_id: travelerId,
      })
      const idx = this.templates.findIndex((t) => t.id === id)
      if (idx >= 0) this.templates[idx] = template
      if (this.detail?.id === id) this.detail.traveler_id = template.traveler_id
    },
    async remove(id: number) {
      await api.delete(`/packing-templates/${id}`)
      this.templates = this.templates.filter((t) => t.id !== id)
      if (this.detail?.id === id) this.detail = null
    },
    async addItem(payload: { name: string; category: string; url?: string | null }) {
      if (!this.detail) return
      const item = await api.post<PackingTemplateItem>(
        `/packing-templates/${this.detail.id}/items`,
        payload,
      )
      this.detail.items.push(item)
      this._syncCount()
      return item
    },
    async updateItem(
      id: number,
      payload: { name?: string; category?: string; url?: string | null },
    ) {
      const item = await api.patch<PackingTemplateItem>(`/packing-template-items/${id}`, payload)
      if (this.detail) {
        const idx = this.detail.items.findIndex((i) => i.id === id)
        if (idx >= 0) this.detail.items[idx] = item
      }
      return item
    },
    async removeItem(id: number) {
      await api.delete(`/packing-template-items/${id}`)
      if (this.detail) {
        this.detail.items = this.detail.items.filter((i) => i.id !== id)
        this._syncCount()
      }
    },
  },
})
