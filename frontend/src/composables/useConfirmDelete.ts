import { useConfirm } from 'primevue/useconfirm'
import { useI18n } from 'vue-i18n'

interface ConfirmActionOptions {
  message: string
  header: string
  /** por defecto "Eliminar" con severidad danger */
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
  const { t } = useI18n()
  return (opts: ConfirmActionOptions) => {
    const { acceptLabel = t('common.actions.delete'), icon = 'pi pi-exclamation-triangle', ...rest } = opts
    const acceptSeverity = 'acceptSeverity' in opts ? opts.acceptSeverity : 'danger'
    confirm.require({
      message: rest.message,
      header: rest.header,
      icon,
      rejectProps: { label: t('common.actions.cancel'), severity: 'secondary', outlined: true },
      acceptProps: { label: acceptLabel, severity: acceptSeverity },
      accept: rest.accept,
    })
  }
}
