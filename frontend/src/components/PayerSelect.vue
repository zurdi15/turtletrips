<script lang="ts">
export type PayerValue = number | 'common' | null
</script>

<script setup lang="ts">
import { computed } from 'vue'
import Select from 'primevue/select'
import Pill from './ui/Pill.vue'
import type { Traveler } from '../api/types'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'

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
      <Pill v-if="option.value === 'common'" color="warn" icon="pi pi-wallet">
        {{ option.label }}
      </Pill>
      <span v-else-if="option.value === null" class="text-ink-faint">
        {{ option.label }}
      </span>
      <span v-else class="inline-flex items-center gap-1.5">
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :style="{ background: option.color ?? FALLBACK_CATEGORY_COLOR }"
        />
        {{ option.label }}
      </span>
    </template>
    <template #value="{ value }">
      <Pill v-if="value === 'common'" color="warn" icon="pi pi-wallet">Fondo común</Pill>
      <span v-else-if="value == null" class="text-ink-faint">Sin asignar</span>
      <span v-else class="inline-flex items-center gap-1.5">
        <span
          class="w-2 h-2 rounded-full shrink-0"
          :style="{ background: optionFor(value)?.color ?? FALLBACK_CATEGORY_COLOR }"
        />
        {{ optionFor(value)?.label }}
      </span>
    </template>
  </Select>
</template>
