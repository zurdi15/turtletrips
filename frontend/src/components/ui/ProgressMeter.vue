<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** porcentaje 0-100 (se capa solo) */
    value: number
    color?: 'brand' | 'info' | 'warn'
    /** colorea por umbral de presupuesto: rojo ≥100, ámbar ≥80, esmeralda si no */
    thresholds?: boolean
    size?: 'xs' | 'sm' | 'md'
  }>(),
  { color: 'brand', thresholds: false, size: 'sm' },
)

const SIZE_CLASSES: Record<string, string> = {
  xs: 'h-1.5',
  sm: 'h-2',
  md: 'h-2.5',
}

const COLOR_CLASSES: Record<string, string> = {
  brand: 'bg-emerald-500',
  info: 'bg-sky-500',
  warn: 'bg-amber-500',
}

const fillClass = computed(() => {
  if (props.thresholds) {
    if (props.value >= 100) return 'bg-red-500'
    if (props.value >= 80) return 'bg-amber-500'
    return 'bg-emerald-500'
  }
  return COLOR_CLASSES[props.color]
})

const pct = computed(() => Math.min(100, Math.max(0, props.value)))
</script>

<template>
  <div class="rounded-full bg-surface-muted overflow-hidden" :class="SIZE_CLASSES[size]">
    <div class="tt-bar h-full rounded-full" :class="fillClass" :style="{ width: `${pct}%` }" />
  </div>
</template>
