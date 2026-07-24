import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Attachment } from '../api/types'

export const useAttachmentsStore = defineStore('attachments', {
  state: () => ({
    items: [] as Attachment[],
    tripId: null as number | null,
    loading: false,
  }),
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        this.items = await api.get<Attachment[]>(`/trips/${tripId}/attachments`)
      } finally {
        this.loading = false
      }
    },
    async upload(file: File, bookingId?: number | null) {
      const form = new FormData()
      form.append('file', file)
      if (bookingId != null) form.append('booking_id', String(bookingId))
      const attachment = await api.upload<Attachment>(
        `/trips/${this.tripId}/attachments`,
        form,
      )
      this.items.unshift(attachment)
      return attachment
    },
    async remove(id: number) {
      await api.delete(`/attachments/${id}`)
      this.items = this.items.filter((a) => a.id !== id)
    },
    downloadUrl(id: number, inline = false): string {
      return `/api/v1/attachments/${id}/download${inline ? '?inline=true' : ''}`
    },
  },
})
