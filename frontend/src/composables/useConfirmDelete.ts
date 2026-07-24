import { useConfirm } from 'primevue/useconfirm'

interface ConfirmActionOptions {
  message: string
  header: string
  /** por defecto 'Eliminar' con severidad danger */
  acceptLabel?: string
  acceptSeverity?: 'danger' | undefined
  icon?: string
  accept: () => void | Promise<void>
}

/**
 * Diálogo de confirmación con los botones estandarizados de la app
 * (Cancelar secundario + acción destructiva). Cubre también los casos
 * no destructivos pasando acceptLabel/acceptSeverity/icon.
 */
export function useConfirmDelete() {
  const confirm = useConfirm()
  return (opts: ConfirmActionOptions) => {
    const { acceptLabel = 'Eliminar', icon = 'pi pi-exclamation-triangle', ...rest } = opts
    const acceptSeverity = 'acceptSeverity' in opts ? opts.acceptSeverity : 'danger'
    confirm.require({
      message: rest.message,
      header: rest.header,
      icon,
      rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
      acceptProps: { label: acceptLabel, severity: acceptSeverity },
      accept: rest.accept,
    })
  }
}
