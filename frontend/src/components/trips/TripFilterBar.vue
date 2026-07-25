<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import type { TripStatus } from '../../api/types'

defineProps<{
  statusOptions: { value: string; label: string }[]
  countryOptions: { value: string; label: string }[]
  activeCount: number
}>()
defineEmits<{ clear: [] }>()

const search = defineModel<string>('search', { required: true })
const status = defineModel<TripStatus | 'all'>('status', { required: true })
const country = defineModel<string>('country', { required: true })
</script>

<template>
  <!-- controles de búsqueda y filtrado (colapsados por defecto);
       en móvil el buscador ocupa su propia línea, en desktop todo en una fila -->
  <div class="flex flex-wrap items-center gap-2 bg-surface-muted border border-line rounded-card p-3">
    <InputText
      v-model="search"
      :placeholder="$t('trips.filters.searchPlaceholder')"
      class="w-full sm:w-auto sm:flex-1"
    />
    <Select
      v-model="status"
      :options="statusOptions"
      optionLabel="label"
      optionValue="value"
      class="flex-1 min-w-[8rem] sm:flex-none sm:w-44"
    />
    <Select
      v-model="country"
      :options="countryOptions"
      optionLabel="label"
      optionValue="value"
      filter
      class="flex-1 min-w-[8rem] sm:flex-none sm:w-48"
    />
    <Button
      v-if="activeCount"
      :label="$t('common.actions.clear')"
      icon="pi pi-times"
      text
      severity="secondary"
      size="small"
      @click="$emit('clear')"
    />
  </div>
</template>
