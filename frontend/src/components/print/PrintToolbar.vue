<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import type { PrintOptions } from '../../utils/print'

// Barra de controles: NO se imprime (print:hidden). El interruptor de gastos
// solo aparece donde puede haberlos.
defineProps<{ backTo: string; allowExpenses: boolean }>()
const options = defineModel<PrintOptions>('options', { required: true })
defineEmits<{ print: [] }>()
</script>

<template>
  <div
    class="print:hidden sticky top-0 z-header bg-surface border-b border-line px-4 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-2"
  >
    <router-link :to="backTo">
      <Button icon="pi pi-arrow-left" severity="secondary" text size="small" :label="$t('print.back')" />
    </router-link>

    <label class="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer">
      <Checkbox v-model="options.map" binary />
      {{ $t('print.toggleMap') }}
    </label>
    <label class="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer">
      <Checkbox v-model="options.notes" binary />
      {{ $t('print.toggleNotes') }}
    </label>
    <label
      v-if="allowExpenses"
      class="flex items-center gap-2 text-sm text-ink-secondary cursor-pointer"
    >
      <Checkbox v-model="options.expenses" binary />
      {{ $t('print.toggleExpenses') }}
    </label>

    <Button
      :label="$t('print.action')"
      icon="pi pi-print"
      size="small"
      class="ml-auto"
      @click="$emit('print')"
    />
  </div>
</template>
