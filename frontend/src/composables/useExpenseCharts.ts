import { computed, ref, watch } from 'vue'
import type { Expense, Trip } from '../api/types'
import { CATEGORY_PALETTE, CHART_LINE_COLOR, WHITE } from '../theme'
import { cssVar } from './useTheme'
import { FALLBACK_CATEGORY_COLOR } from '../stores/categories'
import { aggregate, cumulative } from '../utils/expenses'
import { formatDate, formatMoney } from './useMoney'

export type ChartDim = 'category' | 'payer' | 'place' | 'day'
export type ChartKind = 'pie' | 'bar' | 'line' | 'cumulative'

/** Configuración y series del gráfico de gastos (dimensión + tipo, Chart.js). */
export function useExpenseCharts(ctx: {
  filtered: () => Expense[]
  trip: () => Trip
  catColor: (name: string) => string
  payerName: (e: Expense) => string
  placeNameOf: (e: Expense) => string
  isDark: () => boolean
}) {
  const chartDim = ref<ChartDim>('category')
  const chartType = ref<ChartKind>('pie')

  const dimOptions = [
    { value: 'category', label: 'Categoría' },
    { value: 'payer', label: 'Pagador' },
    { value: 'place', label: 'Sitio' },
    { value: 'day', label: 'Día' },
  ]

  const typeOptions = computed(() =>
    chartDim.value === 'day'
      ? [
          { value: 'bar', label: 'Barras', icon: 'pi pi-chart-bar' },
          { value: 'line', label: 'Línea', icon: 'pi pi-chart-line' },
          { value: 'cumulative', label: 'Acumulado', icon: 'pi pi-arrow-up-right' },
        ]
      : [
          { value: 'pie', label: 'Tarta', icon: 'pi pi-chart-pie' },
          { value: 'bar', label: 'Barras', icon: 'pi pi-chart-bar' },
        ],
  )

  // si cambia la dimensión y el tipo actual no aplica, elegir el primero válido
  watch(chartDim, () => {
    if (!typeOptions.value.some((o) => o.value === chartType.value)) {
      chartType.value = typeOptions.value[0].value as ChartKind
    }
  })

  const chartSeries = computed(() => {
    if (chartDim.value === 'category') {
      return aggregate(ctx.filtered(), (e) => e.category)
        .sort((a, b) => b.value - a.value)
        .map((d) => ({ ...d, color: ctx.catColor(d.label) }))
    }
    if (chartDim.value === 'payer') {
      return aggregate(ctx.filtered(), ctx.payerName)
        .sort((a, b) => b.value - a.value)
        .map((d) => {
          const traveler = ctx.trip().travelers.find((t) => t.name === d.label)
          return { ...d, color: traveler?.color ?? FALLBACK_CATEGORY_COLOR }
        })
    }
    if (chartDim.value === 'place') {
      return aggregate(ctx.filtered(), ctx.placeNameOf)
        .sort((a, b) => b.value - a.value)
        .map((d, idx) => ({
          ...d,
          color:
            d.label === 'Sin sitio'
              ? FALLBACK_CATEGORY_COLOR
              : CATEGORY_PALETTE[idx % CATEGORY_PALETTE.length],
        }))
    }
    // por día, en orden cronológico
    const series = aggregate(ctx.filtered(), (e) => e.day).sort((a, b) =>
      a.label.localeCompare(b.label),
    )
    const points = chartType.value === 'cumulative' ? cumulative(series) : series
    return points.map((d) => ({ ...d, color: CHART_LINE_COLOR }))
  })

  const chartTotal = computed(() => ctx.filtered().reduce((acc, e) => acc + e.amount_base, 0))

  const chartJsType = computed(() => {
    if (chartType.value === 'pie') return 'doughnut'
    if (chartType.value === 'bar') return 'bar'
    return 'line'
  })

  const chartData = computed(() => {
    const labels = chartSeries.value.map((d) =>
      chartDim.value === 'day' ? formatDate(d.label) : d.label,
    )
    const values = chartSeries.value.map((d) => d.value)
    const colors = chartSeries.value.map((d) => d.color)
    if (chartJsType.value === 'line') {
      return {
        labels,
        datasets: [
          {
            data: values,
            borderColor: CHART_LINE_COLOR,
            backgroundColor: `${CHART_LINE_COLOR}55`,
            fill: chartType.value === 'cumulative',
            tension: 0.25,
            pointRadius: 3,
          },
        ],
      }
    }
    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderRadius: chartJsType.value === 'bar' ? 4 : 0,
          borderWidth: chartJsType.value === 'doughnut' ? 2 : 0,
          borderColor: WHITE,
        },
      ],
    }
  })

  const chartOptions = computed(() => {
    const currency = ctx.trip().base_currency
    const money = (v: number) => formatMoney(v, currency)
    ctx.isDark() // dependencia reactiva: relee los tokens al cambiar de tema
    const textColor = cssVar('--tt-ink-secondary')
    const gridColor = cssVar('--tt-chart-grid')
    if (chartJsType.value === 'doughnut') {
      return {
        cutout: '58%',
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' as const, labels: { boxWidth: 12, color: textColor } },
          tooltip: {
            callbacks: {
              label: (ctx2: { label: string; parsed: number }) => {
                const pct = chartTotal.value
                  ? Math.round((ctx2.parsed / chartTotal.value) * 100)
                  : 0
                return ` ${money(ctx2.parsed)} · ${pct}%`
              },
            },
          },
        },
      }
    }
    return {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx2: { parsed: { y: number } }) => ` ${money(ctx2.parsed.y)}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: textColor,
            callback: (v: number | string) => money(Number(v)).replace(/,00\s/, ' '),
          },
          grid: { color: gridColor },
        },
        x: {
          ticks: { color: textColor },
          grid: { display: false },
        },
      },
    }
  })

  return {
    chartDim,
    chartType,
    dimOptions,
    typeOptions,
    chartSeries,
    chartTotal,
    chartJsType,
    chartData,
    chartOptions,
  }
}
