<script setup lang="ts">
// Nota de un gasto en la tabla: una línea recortada y, SOLO si de verdad no
// cabe, un chevron a la derecha que la despliega entera. El recorte se mide en
// el DOM (`scrollWidth` contra `clientWidth`): con el ancho de la columna
// cambiando por el zoom, el idioma o la ventana, no hay forma fiable de saber
// por el texto si va a caber.
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ text: string }>()

const open = ref(false)
const truncated = ref(false)
const textEl = ref<HTMLElement | null>(null)

function measure() {
  const el = textEl.value
  // desplegada no se mide: sin recorte `scrollWidth` iguala al ancho y el
  // chevron desaparecería justo cuando hace falta para volver a cerrarla
  if (!el || open.value) return
  truncated.value = el.scrollWidth > el.clientWidth + 1
}

let observer: ResizeObserver | null = null

onMounted(() => {
  measure()
  observer = new ResizeObserver(() => measure())
  if (textEl.value) observer.observe(textEl.value)
})
onBeforeUnmount(() => observer?.disconnect())

// nota nueva en la misma fila (paginar, reordenar): se vuelve a medir cerrada
watch(
  () => props.text,
  () => {
    open.value = false
    nextTick(measure)
  },
)

function toggle() {
  open.value = !open.value
  if (!open.value) nextTick(measure)
}
</script>

<template>
  <!-- solo es un botón cuando hay algo que desplegar: si no, el clic pasa a la
       fila (que abre el gasto) en vez de morir en un botón que no hace nada -->
  <component
    :is="truncated || open ? 'button' : 'div'"
    :type="truncated || open ? 'button' : undefined"
    class="mt-1.5 flex items-start gap-1.5 w-full max-w-note text-left text-xs text-ink-faint"
    :class="truncated || open ? 'hover:text-ink-secondary transition-colors' : undefined"
    @click.stop="(truncated || open) && toggle()"
  >
    <span
      ref="textEl"
      class="min-w-0 flex-1"
      :class="open ? 'whitespace-pre-line break-words' : 'block truncate'"
    >
      {{ text }}
    </span>
    <!-- h-4 = la altura de la primera línea (text-xs): así el chevron queda
         centrado con ella y no con el bloque entero cuando la nota se abre -->
    <span
      v-if="truncated || open"
      class="shrink-0 h-4 flex items-center"
      v-tooltip.top="open ? $t('expenses.table.hideNote') : $t('expenses.table.showNote')"
    >
      <i
        class="pi pi-chevron-down text-4xs transition-transform duration-200"
        :class="{ 'rotate-180': open }"
      />
    </span>
  </component>
</template>
