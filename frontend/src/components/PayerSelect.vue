<script lang="ts">
export type PayerValue = number | 'common' | null
</script>

<script setup lang="ts">
import { computed } from 'vue'
import Select from 'primevue/select'
import type { Traveler } from '../api/types'

interface PayerOption {
  value: PayerValue
  label: string
  color?: string | null
}

const props = defineProps<{ travelers: Traveler[] }>()
const model = defineModel<PayerValue>({ required: true })

const options = computed<PayerOption[]>(() => [
  { value: null, label: 'Sin asignar' },
  ...props.travelers.map((t) => ({ value: t.id, label: t.name, color: t.color })),
  { value: 'common', label: 'Fondo común' },
])

function optionFor(value: PayerValue): PayerOption | undefined {
  return options.value.find((o) => o.value === value)
}
</script>

<template>
  <Select v-model="model" :options="options" optionLabel="label" optionValue="value">
    <template #option="{ option }">
      <span
        v-if="option.value === 'common'"
        class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700"
      >
        <i class="pi pi-wallet text-[10px]" />
        {{ option.label }}
      </span>
      <span v-else-if="option.value === null" class="text-slate-400">
        {{ option.label }}
      </span>
      <span v-else class="inline-flex items-center gap-1.5">
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :style="{ background: option.color ?? '#94a3b8' }"
        />
        {{ option.label }}
      </span>
    </template>
    <template #value="{ value }">
      <span
        v-if="value === 'common'"
        class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700"
      >
        <i class="pi pi-wallet text-[10px]" />
        Fondo común
      </span>
      <span v-else-if="value == null" class="text-slate-400">Sin asignar</span>
      <span v-else class="inline-flex items-center gap-1.5">
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :style="{ background: optionFor(value)?.color ?? '#94a3b8' }"
        />
        {{ optionFor(value)?.label }}
      </span>
    </template>
  </Select>
</template>
