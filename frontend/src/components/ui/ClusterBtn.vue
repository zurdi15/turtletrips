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
    <button
      v-for="o in options"
      :key="o.value"
      type="button"
      class="relative flex items-center justify-center gap-1.5 rounded-md font-medium whitespace-nowrap cursor-pointer"
      :class="[
        size === 'small' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm',
        model === o.value ? 'text-ink' : 'text-ink-muted hover:text-ink',
      ]"
      :aria-pressed="model === o.value"
      v-tooltip.top="iconOnly && o.label ? o.label : undefined"
      @click="model = o.value"
    >
      <i v-if="o.icon" :class="[o.icon, !iconOnly && 'text-xs']" />
      <template v-if="!iconOnly && o.label">{{ o.label }}</template>
    </button>
  </div>
</template>

<style scoped>
/* reduced-motion lo cubre el guard global de style.css */
.tt-cluster-pill {
  transition: transform var(--tt-dur-180) var(--tt-ease-spring);
}
</style>
