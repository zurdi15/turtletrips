<script setup lang="ts">
import Chart from 'primevue/chart'
import SelectButton from 'primevue/selectbutton'
import type { Expense, Trip } from '../../api/types'
import { useExpenseCharts } from '../../composables/useExpenseCharts'
import { formatMoney } from '../../composables/useMoney'
import { useTheme } from '../../composables/useTheme'

const props = defineProps<{
  filtered: Expense[]
  trip: Trip
  catColor: (name: string) => string
  payerName: (e: Expense) => string
  placeNameOf: (e: Expense) => string
  excludedCategories: string[]
}>()

const { isDark } = useTheme()

const {
  chartDim,
  chartType,
  dimOptions,
  typeOptions,
  chartSeries,
  chartTotal,
  chartJsType,
  chartData,
  chartOptions,
} = useExpenseCharts({
  filtered: () => props.filtered,
  trip: () => props.trip,
  catColor: (name) => props.catColor(name),
  payerName: (e) => props.payerName(e),
  placeNameOf: (e) => props.placeNameOf(e),
  isDark: () => isDark.value,
})
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 p-4 sm:p-5">
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <SelectButton
        v-model="chartDim"
        :options="dimOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
        size="small"
      />
      <span class="flex-1" />
      <SelectButton
        v-model="chartType"
        :options="typeOptions"
        optionValue="value"
        :allowEmpty="false"
        size="small"
      >
        <template #option="{ option }">
          <i :class="option.icon" v-tooltip.top="option.label" />
        </template>
      </SelectButton>
    </div>
    <p v-if="!chartSeries.length" class="text-sm text-slate-400 text-center py-10">
      Sin datos con los filtros actuales
    </p>
    <div
      v-else
      class="mx-auto h-[22rem] sm:h-[26rem]"
      :class="chartJsType === 'doughnut' ? 'max-w-xl' : ''"
    >
      <Chart
        :key="`${chartDim}-${chartType}`"
        :type="chartJsType"
        :data="chartData"
        :options="chartOptions"
        class="h-full [&_canvas]:!w-full"
      />
    </div>
    <p class="text-xs text-slate-400 mt-3 text-center">
      {{ formatMoney(chartTotal, trip.base_currency) }} en total
      <template v-if="excludedCategories.length"> · sin {{ excludedCategories.join(', ') }} </template>
    </p>
  </div>
</template>
