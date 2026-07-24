<script setup lang="ts">
import { FALLBACK_CATEGORY_COLOR } from '../../stores/categories'

// tarjeta de categoría con borde superior del color de la categoría;
// las filas van en el slot (difieren entre maleta y plantilla)
withDefaults(
  defineProps<{
    name: string
    color: string | null
    /** contador de la cabecera: "3/5" en maleta, "4" en plantilla */
    count: string
    size?: 'md' | 'sm'
  }>(),
  { size: 'md' },
)
</script>

<template>
  <div
    class="border border-line overflow-hidden"
    :class="size === 'md' ? 'bg-surface rounded-card' : 'rounded-lg'"
  >
    <div
      class="border-b border-line-subtle flex items-center gap-2"
      :class="size === 'md' ? 'px-4 py-2.5' : 'px-3 py-2 text-sm'"
      :style="{ borderTop: `3px solid ${color ?? FALLBACK_CATEGORY_COLOR}` }"
    >
      <span class="font-semibold text-ink">{{ name }}</span>
      <span class="text-xs text-ink-faint">{{ count }}</span>
    </div>
    <ul>
      <slot />
    </ul>
  </div>
</template>
