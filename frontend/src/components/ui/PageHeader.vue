<script setup lang="ts">
defineProps<{
  title: string
  /** texto del tooltip informativo (icono ⓘ junto al título) */
  info?: string
}>()
</script>

<template>
  <!-- sin margen propio: el call site decide (mb-6, mb-1…) vía class -->
  <div class="flex items-center gap-2">
    <h1 class="text-2xl font-bold text-ink-heading">{{ title }}</h1>
    <button
      v-if="info"
      class="text-ink-faint hover:text-ink-secondary transition-colors"
      v-tooltip.bottom="info"
      :aria-label="`Información sobre ${title.toLowerCase()}`"
    >
      <i class="pi pi-info-circle" />
    </button>
    <span v-if="$slots.actions" class="flex-1" />
    <slot name="actions" />
  </div>
</template>
