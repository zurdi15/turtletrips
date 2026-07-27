<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Chart from 'primevue/chart'
import ClusterBtn from '../ui/ClusterBtn.vue'
import EmptyState from '../EmptyState.vue'
import TabSkeleton from '../TabSkeleton.vue'
import ProgressMeter from '../ui/ProgressMeter.vue'
import Pill from '../ui/Pill.vue'
import { api } from '../../api/client'
import type { YearStats } from '../../api/types'
import { CONTINENT_KEYS, continentStats } from '../../continents'
import { countryName, flagEmoji } from '../../countries'
import { formatMoney } from '../../composables/useMoney'
import { cssVar, useTheme } from '../../composables/useTheme'
import { CATEGORY_PALETTE, CHART_LINE_COLOR, FALLBACK_COLOR, STATS_NEW_COLOR } from '../../theme'

// "Tu año viajero": resumen anual de los viajes en los que participas
const props = defineProps<{
  /** códigos ISO de los países visitados del diario YA filtrado (desglose por continente) */
  countryCodes: string[]
  /** años seleccionados en los filtros (vacío = todos) */
  yearsFilter: number[]
  /** países seleccionados en los filtros (vacío = todos) */
  countriesFilter: string[]
  /** true = tarjetas de lo más reciente a lo más antiguo */
  sortDesc: boolean
}>()

const { t } = useI18n()
const { isDark } = useTheme()
const years = ref<YearStats[]>([])
const loading = ref(true)

const continents = computed(() => continentStats(props.countryCodes))

onMounted(async () => {
  try {
    years.value = await api.get<YearStats[]>('/stats/yearly')
  } finally {
    loading.value = false
  }
})

// los filtros de año y país del diario también recortan estas tarjetas
// (tipo/origen/búsqueda solo tienen sentido sobre el diario, no sobre los años)
const visibleYears = computed(() => {
  let list = years.value
  if (props.yearsFilter.length) list = list.filter((y) => props.yearsFilter.includes(y.year))
  if (props.countriesFilter.length) {
    list = list.filter((y) => y.countries.some((code) => props.countriesFilter.includes(code)))
  }
  return list
})

// tarjetas en el orden elegido; la barra de días se escala al año más viajado
const sorted = computed(() =>
  [...visibleYears.value].sort((a, b) => (props.sortDesc ? b.year - a.year : a.year - b.year)),
)
const maxDays = computed(() => Math.max(1, ...visibleYears.value.map((y) => y.days)))

// ---- gráfico por métrica (mismo esquema que el panel de gastos) ----

type Metric = 'days' | 'trips' | 'countries' | 'spent'
const metric = ref<Metric>('days')
const metricOptions = computed(
  () =>
    [
      { value: 'days', label: t('world.years.metricDays'), icon: 'pi pi-calendar' },
      { value: 'trips', label: t('world.years.metricTrips'), icon: 'pi pi-compass' },
      { value: 'countries', label: t('world.years.metricCountries'), icon: 'pi pi-globe' },
      { value: 'spent', label: t('world.years.metricSpent'), icon: 'pi pi-wallet' },
    ] as const,
)

// cronológico para el eje X (el gráfico se lee siempre de izquierda a derecha)
const chronological = computed(() => [...visibleYears.value].sort((a, b) => a.year - b.year))

const chartData = computed(() => {
  const labels = chronological.value.map((y) => String(y.year))
  if (metric.value === 'countries') {
    // apiladas: estrenados ese año vs. repetidos
    return {
      labels,
      datasets: [
        {
          label: t('world.years.newCountries'),
          data: chronological.value.map((y) => y.new_countries.length),
          backgroundColor: STATS_NEW_COLOR,
          borderRadius: 4,
        },
        {
          label: t('world.years.repeatCountries'),
          data: chronological.value.map((y) => y.countries.length - y.new_countries.length),
          backgroundColor: FALLBACK_COLOR,
          borderRadius: 4,
        },
      ],
    }
  }
  if (metric.value === 'spent') {
    // un dataset por moneda base (lo normal es una sola)
    const currencies = [...new Set(chronological.value.flatMap((y) => y.spent.map((s) => s.currency)))]
    return {
      labels,
      datasets: currencies.map((currency, idx) => ({
        label: currency,
        data: chronological.value.map(
          (y) => y.spent.find((s) => s.currency === currency)?.amount ?? 0,
        ),
        backgroundColor: idx === 0 ? CHART_LINE_COLOR : CATEGORY_PALETTE[idx % CATEGORY_PALETTE.length],
        borderRadius: 4,
      })),
    }
  }
  return {
    labels,
    datasets: [
      {
        data: chronological.value.map((y) => (metric.value === 'days' ? y.days : y.trips)),
        backgroundColor: CHART_LINE_COLOR,
        borderRadius: 4,
      },
    ],
  }
})

const chartOptions = computed(() => {
  isDark.value // dependencia reactiva: relee los tokens al cambiar de tema
  const textColor = cssVar('--tt-ink-secondary')
  const gridColor = cssVar('--tt-chart-grid')
  const stacked = metric.value === 'countries'
  const showLegend = metric.value === 'countries' || metric.value === 'spent'
  return {
    maintainAspectRatio: false,
    plugins: {
      legend: showLegend
        ? { position: 'bottom' as const, labels: { boxWidth: 12, color: textColor } }
        : { display: false },
      tooltip:
        metric.value === 'spent'
          ? {
              callbacks: {
                label: (ctx: { dataset: { label?: string }; parsed: { y: number } }) =>
                  ` ${formatMoney(ctx.parsed.y, ctx.dataset.label ?? 'EUR')}`,
              },
            }
          : {},
    },
    scales: {
      y: {
        beginAtZero: true,
        stacked,
        ticks: { color: textColor, precision: 0 },
        grid: { color: gridColor },
      },
      x: {
        stacked,
        ticks: { color: textColor },
        grid: { display: false },
      },
    },
  }
})
</script>

<template>
  <TabSkeleton v-if="loading" variant="cards" :rows="3" />

  <EmptyState
    v-else-if="!years.length && !countryCodes.length"
    icon="pi pi-chart-bar"
    :title="t('world.years.emptyTitle')"
    :subtitle="t('world.years.emptySubtitle')"
  />

  <div v-else class="flex flex-col gap-4">
    <!-- desglose por continentes (estilo scratch map) -->
    <div class="bg-surface rounded-card border border-line p-4 sm:p-5">
      <h3 class="text-sm font-semibold text-ink-secondary mb-3">
        {{ t('world.continents.title') }}
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
        <div v-for="continent in continents" :key="continent.key">
          <div class="flex items-baseline justify-between gap-2 mb-1">
            <span class="text-sm text-ink">{{ t(CONTINENT_KEYS[continent.key]) }}</span>
            <span class="text-xs text-ink-faint tabular-nums">
              {{ continent.visited }}/{{ continent.total }}
            </span>
          </div>
          <ProgressMeter :value="Math.round((continent.visited / continent.total) * 100)" size="xs" />
        </div>
      </div>
    </div>
    <!-- gráfico por métrica -->
    <div v-if="visibleYears.length" class="bg-surface rounded-card border border-line p-4 sm:p-5">
      <ClusterBtn v-model="metric" :options="metricOptions" size="small" class="mb-4" />
      <div class="h-64 sm:h-72">
        <Chart
          :key="metric"
          type="bar"
          :data="chartData"
          :options="chartOptions"
          class="h-full [&_canvas]:!w-full"
        />
      </div>
    </div>

    <!-- los filtros del diario pueden dejar la parte anual sin nada que enseñar -->
    <p v-if="years.length && !visibleYears.length" class="text-center text-sm text-ink-faint py-6">
      {{ t('world.years.noMatch') }}
    </p>

    <!-- tarjetas por año -->
    <div v-if="visibleYears.length" class="tt-stagger flex flex-col gap-3">
      <div v-for="y in sorted" :key="y.year" class="bg-surface rounded-card border border-line p-4">
        <div class="flex items-baseline gap-x-3 gap-y-1 flex-wrap">
          <span class="text-2xl font-bold text-ink-heading tabular-nums">{{ y.year }}</span>
          <span class="text-sm text-ink-muted">
            {{ t('world.years.tripsCount', { n: y.trips }, y.trips) }}
            · {{ t('world.years.daysCount', { n: y.days }, y.days) }}
          </span>
          <span v-if="y.spent.length" class="ml-auto text-sm font-semibold text-ink whitespace-nowrap">
            {{ y.spent.map((s) => formatMoney(s.amount, s.currency)).join(' + ') }}
          </span>
        </div>

        <ProgressMeter :value="Math.round((y.days / maxDays) * 100)" class="mt-2.5" />

        <div v-if="y.countries.length" class="mt-3 flex flex-wrap items-center gap-1.5">
          <span
            v-for="code in y.countries"
            :key="code"
            class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-surface-muted text-ink"
          >
            {{ flagEmoji(code) }} {{ countryName(code) }}
            <Pill v-if="y.new_countries.includes(code)" color="brand">
              {{ t('world.years.newPill') }}
            </Pill>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
