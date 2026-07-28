<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import MultiSelect from 'primevue/multiselect'
import CountrySelect from '../ui/CountrySelect.vue'
import type { WorldFilterState } from '../../utils/worldGrouping'

// Filtros del diario (mismo patrón que ExpenseFilterPanel: recibe el estado
// reactivo y lo muta; las opciones que dependen de los datos vienen dadas).
const props = defineProps<{
  filters: WorldFilterState
  /** países presentes en el diario: los únicos que filtran algo */
  journalCountryCodes: string[]
  /** años con entradas, del más reciente al más antiguo */
  yearOptions: { value: number; label: string }[]
  activeFilterCount: number
}>()

defineEmits<{ clear: [] }>()

const { t } = useI18n()

const kindFilterOptions = computed(() => [
  { value: 'country', label: t('world.filters.countries') },
  { value: 'region', label: t('world.filters.regions') },
  { value: 'city', label: t('world.filters.cities') },
  { value: 'place', label: t('world.filters.places') },
])

const sourceFilterOptions = computed(() => [
  { value: 'auto', label: t('world.filters.fromTrips') },
  { value: 'manual', label: t('world.filters.manual') },
])

const filters = computed(() => props.filters)
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 bg-surface-muted border border-line rounded-card p-3">
    <InputText
      v-model="filters.searchText"
      :placeholder="t('world.filters.searchPlaceholder')"
      class="w-full sm:w-auto sm:flex-1"
    />
    <MultiSelect
      v-model="filters.kinds"
      :options="kindFilterOptions"
      optionLabel="label"
      optionValue="value"
      :placeholder="t('world.filters.all')"
      :maxSelectedLabels="2"
      class="flex-1 min-w-menu sm:flex-none sm:w-40"
    />
    <CountrySelect
      v-model="filters.countries"
      multiple
      display="comma"
      :codes="journalCountryCodes"
      :placeholder="t('world.filters.allCountries')"
      :maxSelectedLabels="1"
      class="flex-1 min-w-menu sm:flex-none sm:w-52"
    />
    <MultiSelect
      v-model="filters.sources"
      :options="sourceFilterOptions"
      optionLabel="label"
      optionValue="value"
      :placeholder="t('world.filters.anySource')"
      :maxSelectedLabels="1"
      class="flex-1 min-w-menu sm:flex-none sm:w-48"
    />
    <MultiSelect
      v-model="filters.years"
      :options="yearOptions"
      optionLabel="label"
      optionValue="value"
      :placeholder="t('world.filters.anyYear')"
      :maxSelectedLabels="2"
      class="flex-1 min-w-menu sm:flex-none sm:w-40"
    />
    <Button
      v-if="activeFilterCount"
      :label="t('common.actions.clear')"
      icon="pi pi-times"
      text
      severity="secondary"
      size="small"
      @click="$emit('clear')"
    />
  </div>
</template>
