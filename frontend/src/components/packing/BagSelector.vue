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
  <!-- en móvil, rejilla de 2 columnas con celdas iguales (el flex-wrap dejaba
       filas irregulares); en desktop, chips a su anchura natural -->
  <div class="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center">
    <button
      v-for="bag in bags"
      :key="bag.travelerId ?? 'common'"
      class="flex items-center gap-2 px-3.5 py-2 rounded-card border transition-colors min-w-0"
      :class="[
        active === bag.travelerId
          ? 'border-primary bg-brand-tint text-ink-strong'
          : 'border-line bg-surface text-ink-secondary hover:border-line-strong',
        // la maleta común preside en su propia fila; los viajeros van de dos en dos
        bag.travelerId === null && 'max-sm:col-span-full',
      ]"
      @click="active = bag.travelerId"
    >
      <span
        v-if="bag.color"
        class="w-2.5 h-2.5 rounded-full shrink-0"
        :style="{ background: bag.color }"
      />
      <i v-else class="pi pi-briefcase text-xs text-ink-faint" />
      <span class="font-medium truncate">{{ bag.label }}</span>
      <span
        class="text-xs px-1.5 py-0.5 rounded-full shrink-0 ml-auto sm:ml-0"
        :class="
          bag.total && bag.done === bag.total
            ? 'bg-brand-tint-strong text-brand-strong'
            : 'bg-surface-muted text-ink-muted'
        "
      >
        {{ bag.done }}/{{ bag.total }}
      </span>
    </button>
    <slot />
  </div>
</template>
