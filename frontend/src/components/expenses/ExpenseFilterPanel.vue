<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import Select from 'primevue/select'
import DateRangePicker from '../DateRangePicker.vue'
import PayerSelect from '../PayerSelect.vue'
import type { Traveler } from '../../api/types'
import type { ExpenseFilterState } from '../../utils/expenses'

interface Option<T> {
  value: T
  label: string
}

defineProps<{
  filters: ExpenseFilterState
  categoryOptions: Option<string>[]
  excludeOptions: Option<string>[]
  travelers: Traveler[]
  placeOptions: Option<number | 'all' | 'none'>[]
  activeFilterCount: number
}>()

defineEmits<{ clear: [] }>()
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-2 bg-surface-muted border border-line rounded-card p-3"
  >
    <InputText
      v-model="filters.searchText"
      :placeholder="$t('expenses.filters.searchPlaceholder')"
      class="w-full lg:w-auto lg:flex-1"
    />
    <DateRangePicker
      v-model:start="filters.dateFrom"
      v-model:end="filters.dateTo"
      :startLabel="$t('expenses.filters.from')"
      :endLabel="$t('expenses.filters.to')"
      clearable
      class="w-full sm:w-72"
    />
    <Select
      v-model="filters.category"
      :options="categoryOptions"
      optionLabel="label"
      optionValue="value"
      class="flex-1 min-w-menu sm:flex-none sm:w-48"
    />
    <MultiSelect
      v-model="filters.excludedCategories"
      :options="excludeOptions"
      optionLabel="label"
      optionValue="value"
      :placeholder="$t('expenses.filters.excludePlaceholder')"
      display="chip"
      class="flex-1 min-w-menu sm:flex-none sm:w-52"
    />
    <PayerSelect
      v-model="filters.payer"
      :travelers="travelers"
      lead="all"
      includeNone
      class="flex-1 min-w-menu sm:flex-none sm:w-44"
    />
    <Select
      v-model="filters.place"
      :options="placeOptions"
      optionLabel="label"
      optionValue="value"
      filter
      class="flex-1 min-w-menu sm:flex-none sm:w-44"
    />
    <Button
      v-if="activeFilterCount"
      :label="$t('common.actions.clear')"
      icon="pi pi-times"
      text
      severity="secondary"
      size="small"
      @click="$emit('clear')"
    />
  </div>
</template>
