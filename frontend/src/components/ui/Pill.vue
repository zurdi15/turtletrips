<script setup lang="ts">
export type PillColor = 'brand' | 'warn' | 'info' | 'lodging' | 'nature' | 'neutral'

withDefaults(defineProps<{ color?: PillColor; icon?: string; popIn?: boolean }>(), {
  color: 'neutral',
  popIn: false,
})

// strings literales completos: Tailwind JIT no ve clases interpoladas
const COLOR_CLASSES: Record<PillColor, string> = {
  brand: 'bg-brand-tint text-brand-strong',
  warn: 'bg-warn-tint text-warn-strong',
  info: 'bg-info-tint text-info-strong',
  lodging: 'bg-lodging-tint text-lodging-strong',
  nature: 'bg-nature-tint text-nature-strong',
  neutral: 'bg-surface-muted text-ink-muted',
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium"
    :class="[COLOR_CLASSES[color], popIn ? 'tt-pop-in' : '']"
  >
    <i v-if="icon" :class="icon" class="text-3xs" />
    <slot />
  </span>
</template>
