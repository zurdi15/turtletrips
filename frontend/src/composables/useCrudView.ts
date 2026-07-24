import { ref, type Ref } from 'vue'
import { useConfirmDelete } from './useConfirmDelete'

interface CrudViewOptions<T> {
  /** textos del diálogo de confirmación de borrado para un item */
  confirm: (item: T) => { message: string; header: string }
  remove: (item: T) => void | Promise<void>
}

/**
 * Estado CRUD estándar de una vista: diálogo de formulario (nuevo/editar)
 * + borrado con confirmación. El trío openNew/openEdit/removeItem que antes
 * se repetía en cada pestaña.
 */
export function useCrudView<T>(opts: CrudViewOptions<T>) {
  const showForm = ref(false)
  const editing = ref<T | null>(null) as Ref<T | null>
  const confirmAction = useConfirmDelete()

  function openNew() {
    editing.value = null
    showForm.value = true
  }
  function openEdit(item: T) {
    editing.value = item
    showForm.value = true
  }
  function removeItem(item: T) {
    confirmAction({ ...opts.confirm(item), accept: () => opts.remove(item) })
  }

  return { showForm, editing, openNew, openEdit, removeItem }
}
