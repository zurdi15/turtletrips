<script setup lang="ts" generic="T extends string">
import { computed } from 'vue'

// Segmented control (cluster de botones): sustituye a los SelectButton de la
// app con una pill que se desliza hasta la opción activa. Segmentos siempre
// iguales (grid auto-cols-fr), así la pill se mueve SOLO con transform y la
// posición sale del índice sin medir nada.
const props = withDefaults(
  defineProps<{
    options: readonly { value: T; label?: string; icon?: string }[]
    size?: 'normal' | 'small'
    /** solo icono; el label pasa a tooltip */
    iconOnly?: boolean
  }>(),
  { size: 'normal', iconOnly: false },
)

const model = defineModel<T>({ required: true })

const activeIndex = computed(() => props.options.findIndex((o) => o.value === model.value))
</script>

<template>
  <div
    role="group"
    class="relative inline-grid grid-flow-col auto-cols-fr items-stretch bg-surface-muted border border-line rounded-lg p-1"
  >
    <span
      v-if="activeIndex >= 0"
      aria-hidden="true"
      class="tt-cluster-pill absolute top-1 bottom-1 left-1 rounded-md bg-surface shadow-sm"
      :style="{
        width: `calc((100% - 0.5rem) / ${options.length})`,
        transform: `translateX(${activeIndex * 100}%)`,
      }"
    />
    <!-- el color activo cambia sin transición (se congelaría con el hilo ocupado) -->
    <!-- los segmentos son minmax(0,1fr): pueden encogerse por debajo de su
         contenido, así que el label recorta con ellipsis en vez de desbordar
         y pisar al vecino -->
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      class="relative flex min-w-0 items-center justify-center gap-1.5 overflow-hidden rounded-md font-medium cursor-pointer"
      :class="[
        size === 'small' ? 'px-2 py-1 text-xs' : 'px-2 py-1.5 text-sm sm:px-3',
        model === o.value ? 'text-ink' : 'text-ink-muted hover:text-ink',
      ]"
      :aria-pressed="model === o.value"
      v-tooltip.top="iconOnly && o.label ? o.label : undefined"
      @click="model = o.value"
    >
      <i v-if="o.icon" :class="[o.icon, 'shrink-0', !iconOnly && 'text-xs']" />
      <span v-if="!iconOnly && o.label" class="truncate">{{ o.label }}</span>
    </button>
  </div>
</template>

<style scoped>
/* reduced-motion lo cubre el guard global de style.css */
.tt-cluster-pill {
  transition: transform var(--tt-dur-180) var(--tt-ease-spring);
}
</style>
