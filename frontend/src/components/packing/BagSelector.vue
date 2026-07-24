<script setup lang="ts">
export interface BagOption {
  travelerId: number | null
  label: string
  color: string | null
  done: number
  total: number
}

defineProps<{ bags: BagOption[] }>()
const active = defineModel<number | null>('active', { required: true })
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <button
      v-for="bag in bags"
      :key="bag.travelerId ?? 'common'"
      class="flex items-center gap-2 px-3.5 py-2 rounded-xl border transition-colors"
      :class="
        active === bag.travelerId
          ? 'border-[var(--p-primary-color)] bg-brand-tint text-slate-900'
          : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300'
      "
      @click="active = bag.travelerId"
    >
      <span v-if="bag.color" class="w-2.5 h-2.5 rounded-full" :style="{ background: bag.color }" />
      <i v-else class="pi pi-briefcase text-xs text-slate-400" />
      <span class="font-medium">{{ bag.label }}</span>
      <span
        class="text-xs px-1.5 py-0.5 rounded-full"
        :class="
          bag.total && bag.done === bag.total
            ? 'bg-brand-tint-strong text-brand-strong'
            : 'bg-slate-100 text-slate-500'
        "
      >
        {{ bag.done }}/{{ bag.total }}
      </span>
    </button>
    <slot />
  </div>
</template>
