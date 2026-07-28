<script setup lang="ts">
import Pill from './ui/Pill.vue'
import TravelerAvatar from './ui/TravelerAvatar.vue'

// Etiqueta de pagador compartida por los selects (form, filtros, edición en
// bloque): viajero → su avatar (foto si tiene, si no el dot de su color),
// fondo común → cartera ámbar, centinelas ('all'/'none'/null) → texto plano
// (muted para "sin asignar").
defineProps<{
  value: number | string | null
  label: string
  color?: string | null
  avatarUrl?: string | null
  muted?: boolean
}>()
</script>

<template>
  <Pill v-if="value === 'common'" color="warn" icon="pi pi-wallet">{{ label }}</Pill>
  <span v-else-if="typeof value === 'number'" class="inline-flex items-center gap-1.5">
    <!-- caja fija: el dot (8px) y la foto (16px) ocupan lo mismo, así las
         opciones no bailan según quién tenga avatar -->
    <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
      <TravelerAvatar :name="label" :color="color" :avatar-url="avatarUrl" size="xs" />
    </span>
    {{ label }}
  </span>
  <span v-else :class="muted ? 'text-ink-faint' : undefined">{{ label }}</span>
</template>
