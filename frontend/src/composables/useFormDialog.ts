import { ref, watch, type Ref } from 'vue'
import { useNotify } from './useNotify'

interface FormDialogOptions<T> {
  /** el defineModel('visible') del diálogo */
  visible: Ref<boolean>
  /** entidad en edición (p. ej. () => props.place); null/undefined = crear */
  entity: () => T | null | undefined
  /** rellena los refs del formulario desde la entidad (o defaults si null) */
  reset: (entity: T | null) => void
  /** aviso si falta algo (string o {summary, detail}), o null si se puede guardar */
  validate?: () => string | { summary: string; detail?: string } | null
  /** construye el payload y llama a store.update/create */
  submit: () => Promise<unknown>
  onSaved?: () => void
}

/**
 * Esqueleto común de los diálogos de formulario: reinicializar el estado al
 * abrirse (edición vs creación), guard de validación con toast de aviso, y
 * save con loading + toast de error + cierre.
 */
export function useFormDialog<T>(opts: FormDialogOptions<T>) {
  const notify = useNotify()
  const saving = ref(false)

  watch(opts.visible, (open) => {
    if (open) opts.reset(opts.entity() ?? null)
  })

  async function save() {
    const problem = opts.validate?.()
    if (problem) {
      if (typeof problem === 'string') notify.warn(problem)
      else notify.warn(problem.summary, problem.detail)
      return
    }
    saving.value = true
    try {
      await opts.submit()
      opts.visible.value = false
      opts.onSaved?.()
    } catch (err) {
      notify.error('Error al guardar', err)
    } finally {
      saving.value = false
    }
  }

  return { saving, save }
}
