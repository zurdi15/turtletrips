import { useToast } from 'primevue/usetoast'

/**
 * Detalle legible de un error para mostrar en un toast. Los ApiError llegan
 * con el detail de FastAPI ya formateado por api/client.parseError; usar
 * err.message evita el prefijo "Error: " que añadía String(err).
 */
export function errorDetail(err: unknown): string | undefined {
  if (err == null) return undefined
  if (err instanceof Error) return err.message
  return String(err)
}

/** Toasts con severidades y duraciones estandarizadas en toda la app. */
export function useNotify() {
  const toast = useToast()
  return {
    success(summary: string, detail?: string) {
      toast.add({ severity: 'success', summary, detail, life: 3000 })
    },
    info(summary: string, detail?: string) {
      toast.add({ severity: 'info', summary, detail, life: 2500 })
    },
    warn(summary: string, detail?: string) {
      toast.add({ severity: 'warn', summary, detail, life: 3000 })
    },
    error(summary: string, err?: unknown) {
      toast.add({ severity: 'error', summary, detail: errorDetail(err), life: 5000 })
    },
  }
}
