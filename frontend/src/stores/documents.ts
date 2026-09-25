import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Document } from '../api/types'
import { useGlobalResource } from './globalResource'

/**
 * Documentos personales de la familia (DNI, pasaporte, carnet…). Globales, no
 * de un viaje: se cargan una vez y se comparten entre pantallas.
 */
export const useDocumentsStore = defineStore('documents', () => {
  const base = useGlobalResource<Document, never, { original_name?: string; traveler_id?: number }>(
    {
      listPath: '/documents',
      itemPath: (id) => `/documents/${id}`,
    },
  )

  async function upload(file: File, travelerId: number) {
    const form = new FormData()
    form.append('file', file)
    form.append('traveler_id', String(travelerId))
    const document = await api.upload<Document>('/documents', form)
    base.items.value.unshift(document)
    return document
  }

  function downloadUrl(id: number, inline = false): string {
    return `/api/v1/documents/${id}/download${inline ? '?inline=true' : ''}`
  }

  return { ...base, upload, downloadUrl }
})
