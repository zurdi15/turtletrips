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

/** Extensión de un fichero (".pdf"), vacía si no la tiene */
export function fileExtension(name: string): string {
  const dot = name.lastIndexOf('.')
  return dot > 0 && dot < name.length - 1 ? name.slice(dot) : ''
}
