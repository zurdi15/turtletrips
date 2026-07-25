<script setup lang="ts">
import Pill from './ui/Pill.vue'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'

// Etiqueta de pagador compartida por los selects (form, filtros, edición en
// bloque): viajero → dot de su color, fondo común → cartera ámbar,
// centinelas ('all'/'none'/null) → texto plano (muted para "sin asignar").
defineProps<{
  value: number | string | null
  label: string
  color?: string | null
  muted?: boolean
}>()
</script>

<template>
  <Pill v-if="value === 'common'" color="warn" icon="pi pi-wallet">{{ label }}</Pill>
  <span v-else-if="typeof value === 'number'" class="inline-flex items-center gap-1.5">
    <span
      class="w-2 h-2 rounded-full shrink-0"
      :style="{ background: color ?? FALLBACK_CATEGORY_COLOR }"
    />
    {{ label }}
  </span>
  <span v-else :class="muted ? 'text-ink-faint' : undefined">{{ label }}</span>
</template>
