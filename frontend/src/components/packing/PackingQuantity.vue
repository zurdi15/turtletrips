<script setup lang="ts">
// "×3" junto al nombre del elemento; con una sola unidad no se pinta nada
defineProps<{ quantity: number }>()
</script>

<template>
  <span
    v-if="quantity > 1"
    class="ml-1 inline-flex items-center px-1.5 rounded-md bg-surface-muted text-xs font-semibold tabular-nums text-ink-secondary"
  >
    ×{{ quantity }}
  </span>
</template>
