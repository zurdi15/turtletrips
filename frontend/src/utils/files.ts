// Helpers puros para presentar ficheros adjuntos (icono por tipo y tamaño legible)

export function fileIcon(contentType: string): string {
  if (contentType === 'application/pdf') return 'pi pi-file-pdf text-red-500'
  if (contentType.startsWith('image/')) return 'pi pi-image text-sky-500'
  return 'pi pi-file text-ink-faint'
}

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
