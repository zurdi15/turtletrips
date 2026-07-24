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
/* keyframes globales de style.css; reduced-motion lo cubre el guard global */
.tt-empty {
  animation: tt-fade-in var(--tt-dur-300) ease both;
}
.tt-empty-icon {
  animation: tt-pop-in var(--tt-dur-450) var(--tt-ease-spring) 80ms both;
}
</style>
