<script setup lang="ts">
import Chart from 'primevue/chart'
import ClusterBtn from '../ui/ClusterBtn.vue'
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
  <div class="bg-surface rounded-card border border-line p-4 sm:p-5">
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <ClusterBtn v-model="chartDim" :options="dimOptions" size="small" />
      <span class="flex-1" />
      <ClusterBtn v-model="chartType" :options="typeOptions" size="small" iconOnly />
    </div>
    <p v-if="!chartSeries.length" class="text-sm text-ink-faint text-center py-10">
      {{ $t('expenses.charts.empty') }}
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
    <p class="text-xs text-ink-faint mt-3 text-center">
      {{ $t('expenses.charts.total', { amount: formatMoney(chartTotal, trip.base_currency) }) }}
      <template v-if="excludedCategories.length">
        {{ $t('expenses.charts.excluding', { list: excludedCategories.join(', ') }) }}
      </template>
    </p>
  </div>
</template>
