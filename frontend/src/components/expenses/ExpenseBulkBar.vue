<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Select from 'primevue/select'

interface Option<T> {
  value: T
  label: string
}

defineProps<{
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
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 bg-sky-50 border border-sky-200 rounded-xl p-3 mb-3">
    <span class="text-sm font-semibold text-sky-700">{{ count }} seleccionados</span>
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
    />
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
