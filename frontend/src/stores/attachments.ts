import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Attachment } from '../api/types'
import { useTripResource } from './tripResource'

export const useAttachmentsStore = defineStore('attachments', () => {
  const base = useTripResource<Attachment, never>({
    listPath: (tripId) => `/trips/${tripId}/attachments`,
    itemPath: (id) => `/attachments/${id}`,
  })

  async function upload(file: File, bookingId?: number | null, expenseId?: number | null) {
    const form = new FormData()
    form.append('file', file)
    if (bookingId != null) form.append('booking_id', String(bookingId))
    if (expenseId != null) form.append('expense_id', String(expenseId))
    const attachment = await api.upload<Attachment>(
      `/trips/${base.tripId.value}/attachments`,
      form,
    )
    base.items.value.unshift(attachment)
    return attachment
  }

  function downloadUrl(id: number, inline = false): string {
    return `/api/v1/attachments/${id}/download${inline ? '?inline=true' : ''}`
  }

  return { ...base, upload, downloadUrl }
})
