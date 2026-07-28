<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import Select from 'primevue/select'
import PayerSelect from '../PayerSelect.vue'
import type { Traveler } from '../../api/types'

interface Option<T> {
  value: T
  label: string
}

defineProps<{
  count: number
  working: boolean
  categoryOptions: Option<string>[]
  travelers: Traveler[]
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
// el select no guarda estado: dispara el cambio y vuelve a su placeholder
function onPayer(value: number | 'none' | 'common' | null) {
  if (value != null) emit('set-payer', value)
  bulkPayer.value = null
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 bg-info-tint border border-info-edge rounded-card p-3 mb-3">
    <span class="text-sm font-semibold text-info-strong">{{ $t('expenses.bulk.selected', { n: count }) }}</span>
    <span class="flex-1 sm:hidden" />
    <Select
      v-model="bulkCategory"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      :placeholder="$t('expenses.bulk.changeCategory')"
      :disabled="working"
      class="w-full sm:w-52"
      @update:modelValue="onCategory"
    />
    <PayerSelect
      v-model="bulkPayer"
      :travelers="travelers"
      :lead="null"
      includeNone
      :placeholder="$t('expenses.bulk.changePayer')"
      :disabled="working"
      class="w-full sm:w-48"
      @update:modelValue="onPayer"
    />
    <span class="hidden sm:block flex-1" />
    <Button
      icon="pi pi-trash"
      :label="$t('common.actions.delete')"
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
      v-tooltip.bottom="$t('expenses.bulk.clearSelection')"
      @click="$emit('clear')"
    />
  </div>
</template>
