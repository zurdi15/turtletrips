<script setup lang="ts">
defineProps<{ icon: string; title: string; subtitle?: string }>()
</script>

<template>
  <div class="tt-empty flex flex-col items-center justify-center py-14 text-center">
    <i :class="icon" class="tt-empty-icon text-4xl text-slate-300 mb-3" />
    <p class="font-medium text-slate-600">{{ title }}</p>
    <p v-if="subtitle" class="text-sm text-slate-400 mt-1">{{ subtitle }}</p>
    <div class="mt-4">
      <slot />
    </div>
  </div>
</template>

<style scoped>
/* keyframes globales de style.css */
.tt-empty {
  animation: tt-fade-in 0.3s ease both;
}
.tt-empty-icon {
  animation: tt-pop-in 0.45s cubic-bezier(0.22, 1, 0.36, 1) 0.08s both;
}
@media (prefers-reduced-motion: reduce) {
  .tt-empty,
  .tt-empty-icon {
    animation: none;
  }
}
</style>
