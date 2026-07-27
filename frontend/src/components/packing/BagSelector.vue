<script setup lang="ts">
import TravelerAvatar from '../ui/TravelerAvatar.vue'

export interface BagOption {
  travelerId: number | null
  label: string
  color: string | null
  avatarUrl?: string | null
  done: number
  total: number
  /** ocupa su propia fila en móvil (la común preside) */
  wide?: boolean
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
        bag.wide && 'max-sm:col-span-full',
      ]"
      @click="active = bag.travelerId"
    >
      <!-- avatar (foto o dot) del viajero; la común lleva el icono de maleta -->
      <span class="w-4 h-4 grid place-items-center overflow-hidden shrink-0">
        <TravelerAvatar
          v-if="bag.travelerId !== null"
          :name="bag.label"
          :color="bag.color"
          :avatar-url="bag.avatarUrl"
          size="xs"
        />
        <i v-else class="pi pi-briefcase text-xs text-ink-faint" />
      </span>
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
