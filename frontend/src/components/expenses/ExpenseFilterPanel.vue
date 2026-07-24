<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Select from 'primevue/select'
import DateRangePicker from '../DateRangePicker.vue'
import type { ExpenseFilterState } from '../../utils/expenses'

interface Option<T> {
  value: T
  label: string
}

defineProps<{
  filters: ExpenseFilterState
  categoryOptions: Option<string>[]
  excludeOptions: Option<string>[]
  payerOptions: Option<number | 'all' | 'none' | 'common'>[]
  placeOptions: Option<number | 'all' | 'none'>[]
  activeFilterCount: number
}>()

defineEmits<{ clear: [] }>()
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-2 bg-slate-100 border border-slate-200 rounded-xl p-3 mb-4"
  >
    <InputText
      v-model="filters.searchText"
      placeholder="Buscar en descripción, notas o categoría…"
      class="w-full lg:w-auto lg:flex-1"
    />
    <DateRangePicker
      v-model:start="filters.dateFrom"
      v-model:end="filters.dateTo"
      startLabel="Desde"
      endLabel="Hasta"
      clearable
      class="w-full sm:w-72"
    />
    <Select
      v-model="filters.category"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      class="flex-1 min-w-[9rem] sm:flex-none sm:w-48"
    />
    <MultiSelect
      v-model="filters.excludedCategories"
      :options="excludeOptions"
      optionLabel="label"
      optionValue="value"
      placeholder="Excluir categorías…"
      display="chip"
      class="flex-1 min-w-[9rem] sm:flex-none sm:w-52"
    />
    <Select
      v-model="filters.payer"
      :options="payerOptions"
      optionLabel="label"
      optionValue="value"
      class="flex-1 min-w-[9rem] sm:flex-none sm:w-44"
    />
    <Select
      v-model="filters.place"
      :options="placeOptions"
      optionLabel="label"
      optionValue="value"
      filter
      class="flex-1 min-w-[9rem] sm:flex-none sm:w-44"
    />
    <Button
      v-if="activeFilterCount"
      label="Limpiar"
      icon="pi pi-times"
      text
      severity="secondary"
      size="small"
      @click="$emit('clear')"
    />
  </div>
</template>
