<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Select from 'primevue/select'
import PayerTag from '../PayerTag.vue'

interface Option<T> {
  value: T
  label: string
  color?: string | null
}

const props = defineProps<{
  count: number
  working: boolean
  categoryOptions: Option<string>[]
  payerOptions: Option<number | 'none' | 'common'>[]
}>()

const emit = defineEmits<{
  'set-category': [name: string]
  'set-payer': [value: number | 'none' | 'common']
  delete: []
  clear: []
}>()

const bulkCategory = ref<string | null>(null)
const bulkPayer = ref<number | 'none' | 'common' | null>(null)

function onCategory(name: string | null) {
  if (name) emit('set-category', name)
  bulkCategory.value = null
}
function onPayer(value: number | 'none' | 'common' | null) {
  if (value != null) emit('set-payer', value)
  bulkPayer.value = null
}

function payerFor(value: number | 'none' | 'common') {
  return props.payerOptions.find((o) => o.value === value)
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 bg-info-tint border border-info-edge rounded-card p-3 mb-3">
    <span class="text-sm font-semibold text-info-strong">{{ count }} seleccionados</span>
    <span class="flex-1 sm:hidden" />
    <Select
      v-model="bulkCategory"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Cambiar categoría…"
      :disabled="working"
      class="w-full sm:w-52"
      @update:modelValue="onCategory"
    />
    <Select
      v-model="bulkPayer"
      :options="payerOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Cambiar pagador…"
      :disabled="working"
      class="w-full sm:w-48"
      @update:modelValue="onPayer"
    >
      <template #option="{ option }">
        <PayerTag :value="option.value" :label="option.label" :color="option.color" />
      </template>
      <template #value="{ value, placeholder }">
        <PayerTag
          v-if="value != null"
          :value="value"
          :label="payerFor(value)?.label ?? ''"
          :color="payerFor(value)?.color"
        />
        <template v-else>{{ placeholder }}</template>
      </template>
    </Select>
    <span class="hidden sm:block flex-1" />
    <Button
      icon="pi pi-trash"
      label="Eliminar"
      severity="danger"
      outlined
      :loading="working"
      class="max-sm:[&_.p-button-label]:hidden"
      @click="$emit('delete')"
    />
    <Button
      icon="pi pi-times"
      severity="secondary"
      text
      v-tooltip.bottom="'Quitar selección'"
      @click="$emit('clear')"
    />
  </div>
</template>
