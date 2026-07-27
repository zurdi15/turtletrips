import { nextTick, watch, type Ref } from 'vue'

/**
 * Resalta y centra la fila enlazada desde otra pestaña (?expense=id):
 * salta a la página donde vive y hace scrollIntoView sobre `.tt-row-flash`.
 * Las filas se recargan varias veces al montar: un solo scroll por id,
 * o el smooth-scroll se reinicia a mitad y "bota".
 */
export function useRowFlash(opts: {
  rows: () => { id: number }[]
  highlightId: () => number | null | undefined
  first: Ref<number>
  pageRows: Ref<number>
  root: () => HTMLElement | null | undefined
}) {
  let scrolledFor: number | null = null

  watch(
    [() => opts.highlightId(), opts.rows],
    async () => {
      const id = opts.highlightId()
      if (id == null) {
        scrolledFor = null
        return
      }
      if (scrolledFor === id) return
      const idx = opts.rows().findIndex((r) => r.id === id)
      if (idx < 0) return
      scrolledFor = id
      // saltar a la página donde vive el gasto y centrarlo
      opts.first.value = Math.floor(idx / opts.pageRows.value) * opts.pageRows.value
      await nextTick()
      opts
        .root()
        ?.querySelector('.tt-row-flash')
        ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    },
    { immediate: true },
  )

  function rowClass(row: { id: number }): string {
    return row.id === opts.highlightId() ? 'tt-row-flash' : ''
  }

  return { rowClass }
}
