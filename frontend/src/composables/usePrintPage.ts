import { nextTick, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { resolvePrintOptions, type PrintOptions } from '../utils/print'

/**
 * Estado común de las dos vistas imprimibles. Las opciones nacen de la query
 * (`?map=0&notes=0`) para que un enlace ya lleve elegido qué se imprime, y
 * `allowExpenses` es el candado: en la versión pública no hay dinero, se pida
 * como se pida.
 */
export function usePrintPage(allowExpenses: boolean) {
  const route = useRoute()
  const options = ref<PrintOptions>(resolvePrintOptions(route.query, { allowExpenses }))
  const previousTitle = document.title

  /** el navegador usa el <title> como nombre del PDF */
  function setTitle(title: string) {
    document.title = title
  }
  onBeforeUnmount(() => {
    document.title = previousTitle
  })

  async function print() {
    await nextTick()
    // dos frames para que el layout esté pintado; con mapa, un respiro extra
    // porque sus tiles llegan por red y el diálogo captura lo que haya
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
    if (options.value.map) await new Promise((resolve) => setTimeout(resolve, 700))
    window.print()
  }

  return { options, print, setTitle }
}
