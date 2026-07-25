<script lang="ts">
export type PayerValue = number | 'common' | null
</script>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Select from 'primevue/select'
import PayerTag from './PayerTag.vue'
import type { Traveler } from '../api/types'

interface PayerOption {
  value: PayerValue
  label: string
  color?: string | null
}

const props = defineProps<{ travelers: Traveler[] }>()
const model = defineModel<PayerValue>({ required: true })
const { t } = useI18n()

const options = computed<PayerOption[]>(() => [
  { value: null, label: t('common.payer.unassigned') },
  ...props.travelers.map((tr) => ({ value: tr.id, label: tr.name, color: tr.color })),
  { value: 'common', label: t('common.payer.commonFund') },
])

function optionFor(value: PayerValue): PayerOption | undefined {
  return options.value.find((o) => o.value === value)
}
</script>

<template>
  <Select v-model="model" :options="options" optionLabel="label" optionValue="value">
    <template #option="{ option }">
      <PayerTag
        :value="option.value"
        :label="option.label"
        :color="option.color"
        :muted="option.value === null"
      />
    </template>
    <template #value="{ value }">
      <PayerTag
        :value="value ?? null"
        :label="optionFor(value ?? null)?.label ?? ''"
        :color="optionFor(value ?? null)?.color"
        :muted="value == null"
      />
    </template>
  </Select>
</template>
