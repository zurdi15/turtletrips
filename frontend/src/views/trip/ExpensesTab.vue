<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import SelectButton from 'primevue/selectbutton'
import InputText from 'primevue/inputtext'
import DateRangePicker from '../../components/DateRangePicker.vue'
import Chart from 'primevue/chart'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import ExpenseFormDialog from '../../components/ExpenseFormDialog.vue'
import ExpenseImportDialog from '../../components/ExpenseImportDialog.vue'
import MemberChip from '../../components/MemberChip.vue'
import EmptyState from '../../components/EmptyState.vue'
import type { Expense, Trip } from '../../api/types'
import { CATEGORY_PALETTE } from '../../constants'
import { useExpensesStore } from '../../stores/expenses'
import { useCategoriesStore, FALLBACK_CATEGORY_COLOR } from '../../stores/categories'
import { usePlacesStore } from '../../stores/places'
import { useTheme } from '../../composables/useTheme'
import { formatDate, formatMoney, parseIsoDate, toIsoDate } from '../../composables/useMoney'

const props = defineProps<{ trip: Trip }>()
const store = useExpensesStore()
const categoriesStore = useCategoriesStore()
const places = usePlacesStore()
const confirm = useConfirm()
const toast = useToast()
const { isDark } = useTheme()

function catColor(name: string): string {
  return categoriesStore.colorOf('expense', name)
}

const showForm = ref(false)
const showImport = ref(false)
const editing = ref<Expense | null>(null)

// ---- filtros ----
const showFilters = ref(false)
const searchText = ref('')
const filterCategory = ref<string>('all')
const excludedCategories = ref<string[]>([])
const filterPayer = ref<number | 'all' | 'none'>('all')
const filterPlace = ref<number | 'all' | 'none'>('all')
const dateFrom = ref<Date | null>(null)
const dateTo = ref<Date | null>(null)

// ---- gráfico ----
const chartDim = ref<'category' | 'payer' | 'place' | 'day'>('category')
const chartType = ref<'pie' | 'bar' | 'line' | 'cumulative'>('pie')

// ---- agrupación de la tabla ----
const tableGroup = ref<'none' | 'day' | 'category' | 'payer_name' | 'place_name'>('none')

// ---- vista: tabla o gráficos ----
const viewMode = ref<'table' | 'charts'>('table')
const viewOptions = [
  { value: 'table', label: 'Tabla', icon: 'pi pi-table' },
  { value: 'charts', label: 'Gráficos', icon: 'pi pi-chart-pie' },
]

onMounted(() => {
  store.load(props.trip.id)
  categoriesStore.load('expense')
  places.load(props.trip.id)
})
watch(() => props.trip.id, (id) => {
  store.load(id)
  places.load(id)
})

const memberById = computed(() => new Map(props.trip.travelers.map((t) => [t.id, t])))
const placeById = computed(() => new Map(places.items.map((p) => [p.id, p])))

function placeNameOf(e: Expense): string {
  return e.place_id != null ? (placeById.value.get(e.place_id)?.name ?? 'Sin sitio') : 'Sin sitio'
}

const allCategoryNames = computed(() => {
  const names = new Set(categoriesStore.expense.map((c) => c.name))
  for (const e of store.items) names.add(e.category)
  return [...names]
})

const categoryFilterOptions = computed(() => [
  { value: 'all', label: 'Todas las categorías' },
  ...allCategoryNames.value.map((name) => ({ value: name, label: name })),
])
const excludeOptions = computed(() =>
  allCategoryNames.value.map((name) => ({ value: name, label: name })),
)
const payerFilterOptions = computed(() => [
  { value: 'all' as const, label: 'Todos los pagadores' },
  ...props.trip.travelers.map((t) => ({ value: t.id, label: t.name })),
  { value: 'none' as const, label: 'Sin asignar' },
])

const placeFilterOptions = computed(() => {
  const usedIds = new Set(
    store.items.map((e) => e.place_id).filter((id): id is number => id != null),
  )
  return [
    { value: 'all' as const, label: 'Todos los sitios' },
    ...[...usedIds]
      .map((id) => ({ value: id, label: placeById.value.get(id)?.name ?? `#${id}` }))
      .sort((a, b) => a.label.localeCompare(b.label, 'es')),
    { value: 'none' as const, label: 'Sin sitio' },
  ]
})

const activeFilterCount = computed(
  () =>
    (searchText.value.trim() ? 1 : 0) +
    (filterCategory.value !== 'all' ? 1 : 0) +
    (excludedCategories.value.length ? 1 : 0) +
    (filterPayer.value !== 'all' ? 1 : 0) +
    (filterPlace.value !== 'all' ? 1 : 0) +
    (dateFrom.value ? 1 : 0) +
    (dateTo.value ? 1 : 0),
)

function clearFilters() {
  searchText.value = ''
  filterCategory.value = 'all'
  excludedCategories.value = []
  filterPayer.value = 'all'
  filterPlace.value = 'all'
  dateFrom.value = null
  dateTo.value = null
}

const filtered = computed(() =>
  store.items.filter((e) => {
    if (filterCategory.value !== 'all' && e.category !== filterCategory.value) return false
    if (excludedCategories.value.includes(e.category)) return false
    if (filterPayer.value === 'none' && e.paid_by_id != null) return false
    if (filterPayer.value !== 'all' && filterPayer.value !== 'none' && e.paid_by_id !== filterPayer.value)
      return false
    if (filterPlace.value === 'none' && e.place_id != null) return false
    if (filterPlace.value !== 'all' && filterPlace.value !== 'none' && e.place_id !== filterPlace.value)
      return false
    if (dateFrom.value && e.day < toIsoDate(dateFrom.value)) return false
    if (dateTo.value && e.day > toIsoDate(dateTo.value)) return false
    if (searchText.value) {
      const q = searchText.value.toLowerCase()
      if (
        !e.description.toLowerCase().includes(q) &&
        !(e.notes ?? '').toLowerCase().includes(q) &&
        !e.category.toLowerCase().includes(q) &&
        !placeNameOf(e).toLowerCase().includes(q)
      )
        return false
    }
    return true
  }),
)

// ---- métricas (sobre los datos filtrados) ----

const tripDayCount = computed<number | null>(() => {
  if (props.trip.start_date && props.trip.end_date) {
    return (
      Math.round(
        (parseIsoDate(props.trip.end_date).getTime() -
          parseIsoDate(props.trip.start_date).getTime()) /
          86400000,
      ) + 1
    )
  }
  const days = new Set(filtered.value.map((e) => e.day))
  return days.size || null
})

const stats = computed(() => {
  const total = filtered.value.reduce((acc, e) => acc + e.amount_base, 0)
  const travelers = props.trip.travelers.length
  const days = tripDayCount.value
  return {
    total,
    count: filtered.value.length,
    travelers,
    days,
    perPerson: travelers ? total / travelers : null,
    perDay: days ? total / days : null,
    perDayPerson: travelers && days ? total / days / travelers : null,
  }
})

const currencyBreakdown = computed(() => {
  const map = new Map<string, number>()
  for (const e of filtered.value) {
    if (e.currency !== props.trip.base_currency) {
      map.set(e.currency, (map.get(e.currency) ?? 0) + e.amount)
    }
  }
  return [...map.entries()]
})

const budgetPct = computed(() => {
  const s = store.summary
  if (!s?.budget_amount) return null
  return Math.min(100, Math.round((s.total_base / s.budget_amount) * 100))
})

// ---- agregaciones para el gráfico ----

function aggregate(keyOf: (e: Expense) => string): { label: string; value: number }[] {
  const map = new Map<string, number>()
  for (const e of filtered.value) {
    const key = keyOf(e)
    map.set(key, (map.get(key) ?? 0) + e.amount_base)
  }
  return [...map.entries()].map(([label, value]) => ({ label, value }))
}

const payerName = (e: Expense) =>
  e.paid_by_id != null ? (memberById.value.get(e.paid_by_id)?.name ?? 'Sin asignar') : 'Sin asignar'

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
    chartType.value = typeOptions.value[0].value as typeof chartType.value
  }
})

const chartSeries = computed(() => {
  if (chartDim.value === 'category') {
    return aggregate((e) => e.category)
      .sort((a, b) => b.value - a.value)
      .map((d) => ({ ...d, color: catColor(d.label) }))
  }
  if (chartDim.value === 'payer') {
    return aggregate(payerName)
      .sort((a, b) => b.value - a.value)
      .map((d) => {
        const traveler = props.trip.travelers.find((t) => t.name === d.label)
        return { ...d, color: traveler?.color ?? FALLBACK_CATEGORY_COLOR }
      })
  }
  if (chartDim.value === 'place') {
    return aggregate(placeNameOf)
      .sort((a, b) => b.value - a.value)
      .map((d, idx) => ({
        ...d,
        color: d.label === 'Sin sitio' ? FALLBACK_CATEGORY_COLOR : CATEGORY_PALETTE[idx % CATEGORY_PALETTE.length],
      }))
  }
  // por día, en orden cronológico
  const series = aggregate((e) => e.day).sort((a, b) => a.label.localeCompare(b.label))
  if (chartType.value === 'cumulative') {
    let acc = 0
    return series.map((d) => ({ label: d.label, value: (acc += d.value), color: '#0ea5e9' }))
  }
  return series.map((d) => ({ ...d, color: '#0ea5e9' }))
})

const chartTotal = computed(() => filtered.value.reduce((acc, e) => acc + e.amount_base, 0))

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
          borderColor: '#0ea5e9',
          backgroundColor: '#0ea5e955',
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
        borderColor: '#ffffff',
      },
    ],
  }
})

const chartOptions = computed(() => {
  const currency = props.trip.base_currency
  const money = (v: number) => formatMoney(v, currency)
  const textColor = isDark.value ? '#cbd5e1' : '#475569'
  const gridColor = isDark.value ? 'rgba(51, 65, 85, 0.6)' : 'rgba(226, 232, 240, 0.8)'
  if (chartJsType.value === 'doughnut') {
    return {
      cutout: '58%',
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' as const, labels: { boxWidth: 12, color: textColor } },
        tooltip: {
          callbacks: {
            label: (ctx: { label: string; parsed: number }) => {
              const pct = chartTotal.value ? Math.round((ctx.parsed / chartTotal.value) * 100) : 0
              return ` ${money(ctx.parsed)} · ${pct}%`
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
          label: (ctx: { parsed: { y: number } }) => ` ${money(ctx.parsed.y)}`,
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

// ---- tabla (con agrupación opcional) ----

const tableGroupOptions = [
  { value: 'none', label: 'Sin agrupar' },
  { value: 'day', label: 'Agrupar por día' },
  { value: 'category', label: 'Agrupar por categoría' },
  { value: 'payer_name', label: 'Agrupar por pagador' },
  { value: 'place_name', label: 'Agrupar por sitio' },
]

interface Row extends Expense {
  payer_name: string
  place_name: string
}

const rows = computed<Row[]>(() => {
  const enriched = filtered.value.map((e) => ({
    ...e,
    payer_name: payerName(e),
    place_name: placeNameOf(e),
  }))
  const byDayDesc = (a: Row, b: Row) => b.day.localeCompare(a.day) || b.id - a.id
  if (tableGroup.value === 'day') return enriched.sort(byDayDesc)
  if (tableGroup.value === 'category')
    return enriched.sort((a, b) => a.category.localeCompare(b.category, 'es') || byDayDesc(a, b))
  if (tableGroup.value === 'payer_name')
    return enriched.sort((a, b) => a.payer_name.localeCompare(b.payer_name, 'es') || byDayDesc(a, b))
  if (tableGroup.value === 'place_name')
    return enriched.sort((a, b) => a.place_name.localeCompare(b.place_name, 'es') || byDayDesc(a, b))
  return enriched.sort(byDayDesc)
})

const groupTotals = computed(() => {
  const map = new Map<string, { total: number; count: number }>()
  if (tableGroup.value === 'none') return map
  for (const row of rows.value) {
    const key = String(row[tableGroup.value as keyof Row])
    const entry = map.get(key) ?? { total: 0, count: 0 }
    entry.total += row.amount_base
    entry.count += 1
    map.set(key, entry)
  }
  return map
})

function groupLabel(row: Row): string {
  if (tableGroup.value === 'day') return formatDate(row.day)
  if (tableGroup.value === 'category') return row.category
  if (tableGroup.value === 'place_name') return row.place_name
  return row.payer_name
}
function groupKey(row: Row): string {
  return String(row[tableGroup.value as keyof Row])
}

// ---- selección múltiple y acciones en bloque ----

const selected = ref<Row[]>([])
const bulkCategory = ref<string | null>(null)
const bulkPayer = ref<number | 'none' | null>(null)
const bulkWorking = ref(false)

const bulkCategoryOptions = computed(() =>
  allCategoryNames.value.map((name) => ({ value: name, label: name })),
)
const bulkPayerOptions = computed(() => [
  ...props.trip.travelers.map((t) => ({ value: t.id as number | 'none', label: t.name })),
  { value: 'none' as const, label: 'Sin asignar' },
])

async function applyBulk(payload: { category?: string; paid_by_id?: number | null }) {
  bulkWorking.value = true
  try {
    const count = selected.value.length
    await store.bulkUpdate(selected.value.map((e) => e.id), payload)
    toast.add({ severity: 'success', summary: `${count} gastos actualizados`, life: 3000 })
    selected.value = []
  } finally {
    bulkWorking.value = false
    bulkCategory.value = null
    bulkPayer.value = null
  }
}

function onBulkCategory(name: string | null) {
  if (name) applyBulk({ category: name })
}
function onBulkPayer(value: number | 'none' | null) {
  if (value != null) applyBulk({ paid_by_id: value === 'none' ? null : value })
}

function bulkDelete() {
  const count = selected.value.length
  confirm.require({
    message: `¿Eliminar los ${count} gastos seleccionados?`,
    header: 'Eliminar gastos',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: `Eliminar ${count}`, severity: 'danger' },
    accept: async () => {
      bulkWorking.value = true
      try {
        await store.bulkRemove(selected.value.map((e) => e.id))
        toast.add({ severity: 'success', summary: `${count} gastos eliminados`, life: 3000 })
        selected.value = []
      } finally {
        bulkWorking.value = false
      }
    },
  })
}

function openNew() {
  editing.value = null
  showForm.value = true
}
function openEdit(expense: Expense) {
  editing.value = expense
  showForm.value = true
}
function removeExpense(expense: Expense) {
  confirm.require({
    message: `¿Eliminar el gasto "${expense.description}"?`,
    header: 'Eliminar gasto',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Eliminar', severity: 'danger' },
    accept: () => store.remove(expense.id),
  })
}
</script>

<template>
  <div>
    <!-- métricas -->
    <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 mb-5">
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">
          Total gastado
        </p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{ formatMoney(stats.total, trip.base_currency) }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">{{ stats.count }} gastos</p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Presupuesto</p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{
            store.summary?.budget_amount != null
              ? formatMoney(store.summary.budget_amount, trip.base_currency)
              : '—'
          }}
        </p>
        <div v-if="budgetPct != null" class="mt-1.5">
          <div class="h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div
              class="h-full rounded-full"
              :class="budgetPct >= 100 ? 'bg-red-500' : budgetPct >= 80 ? 'bg-amber-500' : 'bg-emerald-500'"
              :style="{ width: `${budgetPct}%` }"
            />
          </div>
          <p class="text-xs text-slate-400 mt-0.5">{{ budgetPct }}% usado</p>
        </div>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Restante</p>
        <p
          class="text-xl font-bold mt-1"
          :class="(store.summary?.remaining ?? 0) < 0 ? 'text-red-600' : 'text-emerald-600'"
        >
          {{
            store.summary?.remaining != null
              ? formatMoney(store.summary.remaining, trip.base_currency)
              : '—'
          }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">del presupuesto del viaje</p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Por persona</p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{ stats.perPerson != null ? formatMoney(stats.perPerson, trip.base_currency) : '—' }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">
          {{ stats.travelers ? `entre ${stats.travelers} viajeros` : 'añade viajeros al viaje' }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Por día</p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{ stats.perDay != null ? formatMoney(stats.perDay, trip.base_currency) : '—' }}
        </p>
        <p class="text-xs text-slate-400 mt-0.5">
          {{ stats.days ? `${stats.days} días` : 'sin fechas' }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-slate-200 p-3.5">
        <p class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">
          Por día y persona
        </p>
        <p class="text-xl font-bold text-slate-800 mt-1">
          {{
            stats.perDayPerson != null ? formatMoney(stats.perDayPerson, trip.base_currency) : '—'
          }}
        </p>
        <p v-if="activeFilterCount" class="text-xs text-sky-600 mt-0.5">con filtros aplicados</p>
      </div>
    </div>

    <p
      v-if="currencyBreakdown.length"
      class="text-xs text-slate-400 -mt-3 mb-4 flex flex-wrap gap-x-3"
    >
      <span>En moneda original:</span>
      <span v-for="[currency, amount] in currencyBreakdown" :key="currency">
        {{ formatMoney(amount, currency) }}
      </span>
    </p>

    <!-- barra de acciones -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <Button label="Nuevo gasto" icon="pi pi-plus" @click="openNew" />
      <Button
        label="Filtros"
        :icon="showFilters ? 'pi pi-chevron-up' : 'pi pi-sliders-h'"
        severity="secondary"
        :outlined="!showFilters && !activeFilterCount"
        :badge="activeFilterCount ? String(activeFilterCount) : undefined"
        @click="showFilters = !showFilters"
      />
      <Select
        v-if="viewMode === 'table'"
        v-model="tableGroup"
        :options="tableGroupOptions"
        optionLabel="label"
        optionValue="value"
        class="w-52"
      />
      <span class="flex-1" />
      <SelectButton
        v-model="viewMode"
        :options="viewOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
      />
      <Button
        icon="pi pi-file-import"
        severity="secondary"
        outlined
        v-tooltip.bottom="'Importar CSV'"
        @click="showImport = true"
      />
      <a :href="store.exportUrl()" download>
        <Button
          icon="pi pi-file-export"
          severity="secondary"
          outlined
          v-tooltip.bottom="'Exportar CSV'"
        />
      </a>
    </div>

    <!-- panel de filtros -->
    <div
      v-if="showFilters"
      class="flex flex-wrap items-center gap-2 bg-white border border-slate-200 rounded-xl p-3 mb-4"
    >
      <InputText
        v-model="searchText"
        placeholder="Buscar en descripción, notas o categoría…"
        class="w-full lg:w-auto lg:flex-1"
      />
      <DateRangePicker
        v-model:start="dateFrom"
        v-model:end="dateTo"
        startLabel="Desde"
        endLabel="Hasta"
        clearable
        class="w-full sm:w-72"
      />
      <Select
        v-model="filterCategory"
        :options="categoryFilterOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-48"
      />
      <MultiSelect
        v-model="excludedCategories"
        :options="excludeOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="Excluir categorías…"
        display="chip"
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-52"
      />
      <Select
        v-model="filterPayer"
        :options="payerFilterOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-44"
      />
      <Select
        v-model="filterPlace"
        :options="placeFilterOptions"
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
        @click="clearFilters"
      />
    </div>

    <EmptyState
      v-if="!store.loading && !store.items.length"
      icon="pi pi-wallet"
      title="Sin gastos todavía"
      subtitle="Añade el primero o importa tu Excel como CSV"
    />

    <div v-else>
      <p v-if="!filtered.length" class="text-center text-sm text-slate-400 py-10">
        Ningún gasto coincide con los filtros
      </p>
      <div v-else-if="viewMode === 'table'">
        <!-- acciones en bloque sobre la selección -->
        <div
          v-if="selected.length"
          class="flex flex-wrap items-center gap-2 bg-sky-50 border border-sky-200 rounded-xl p-3 mb-3"
        >
          <span class="text-sm font-semibold text-sky-700">
            {{ selected.length }} seleccionados
          </span>
          <span class="flex-1 sm:hidden" />
          <Select
            v-model="bulkCategory"
            :options="bulkCategoryOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Cambiar categoría…"
            :disabled="bulkWorking"
            class="w-full sm:w-52"
            @update:modelValue="onBulkCategory"
          />
          <Select
            v-model="bulkPayer"
            :options="bulkPayerOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="Cambiar pagador…"
            :disabled="bulkWorking"
            class="w-full sm:w-48"
            @update:modelValue="onBulkPayer"
          />
          <span class="hidden sm:block flex-1" />
          <Button
            icon="pi pi-trash"
            label="Eliminar"
            severity="danger"
            outlined
            :loading="bulkWorking"
            class="max-sm:[&_.p-button-label]:hidden"
            @click="bulkDelete"
          />
          <Button
            icon="pi pi-times"
            severity="secondary"
            text
            v-tooltip.bottom="'Quitar selección'"
            @click="selected = []"
          />
        </div>

        <DataTable
          v-model:selection="selected"
          :value="rows"
          dataKey="id"
          size="small"
          stripedRows
          :loading="store.loading"
          :tableStyle="{ minWidth: '640px' }"
          :rowGroupMode="tableGroup !== 'none' ? 'subheader' : undefined"
          :groupRowsBy="tableGroup !== 'none' ? tableGroup : undefined"
          class="bg-white rounded-xl overflow-hidden border border-slate-200"
        >
          <Column selectionMode="multiple" headerStyle="width: 2.5rem" />
          <template v-if="tableGroup !== 'none'" #groupheader="{ data }">
            <div class="flex items-center gap-3 py-0.5">
              <span class="font-semibold text-slate-700">{{ groupLabel(data) }}</span>
              <span class="text-xs text-slate-400">
                {{ groupTotals.get(groupKey(data))?.count }} gastos
              </span>
              <span class="ml-auto font-semibold text-slate-700">
                {{ formatMoney(groupTotals.get(groupKey(data))?.total ?? 0, trip.base_currency) }}
              </span>
            </div>
          </template>
          <Column header="Fecha" field="day" style="width: 7rem">
            <template #body="{ data }">{{ formatDate(data.day) }}</template>
          </Column>
          <Column header="Categoría" field="category" style="width: 9rem">
            <template #body="{ data }">
              <Tag
                :value="data.category"
                :style="{
                  background: `${catColor(data.category)}20`,
                  color: catColor(data.category),
                }"
              />
            </template>
          </Column>
          <Column header="Descripción" field="description">
            <template #body="{ data }">
              <span>{{ data.description }}</span>
              <i
                v-if="data.booking_id"
                class="pi pi-ticket text-xs text-slate-400 ml-1"
                v-tooltip.top="'Creado desde una reserva'"
              />
              <router-link
                v-if="data.place_id && placeById.get(data.place_id)"
                :to="{ name: 'trip-places', params: { id: trip.id }, query: { place: data.place_id } }"
                class="mt-1.5 flex items-center gap-0.5 w-fit whitespace-nowrap text-xs text-emerald-600 hover:underline no-underline"
                v-tooltip.top="'Ver en Sitios'"
              >
                <i class="pi pi-map-marker text-[10px]" />
                <span>{{ placeById.get(data.place_id)!.name }}</span>
              </router-link>
              <p v-if="data.notes" class="mt-1.5 text-xs text-slate-400 truncate max-w-[16rem]">
                {{ data.notes }}
              </p>
            </template>
          </Column>
          <Column header="Importe" style="width: 8rem">
            <template #body="{ data }">
              <div class="text-right">
                <div class="font-medium">{{ formatMoney(data.amount_base, trip.base_currency) }}</div>
                <div v-if="data.currency !== trip.base_currency" class="text-xs text-slate-400">
                  {{ formatMoney(data.amount, data.currency) }}
                </div>
              </div>
            </template>
          </Column>
          <Column header="Pagó" field="payer_name" style="width: 7rem">
            <template #body="{ data }">
              <MemberChip
                v-if="data.paid_by_id != null && memberById.get(data.paid_by_id)"
                :member="memberById.get(data.paid_by_id)!"
              />
              <span v-else class="text-slate-300 text-xs">—</span>
            </template>
          </Column>
          <Column style="width: 5.5rem">
            <template #body="{ data }">
              <div class="flex gap-1 justify-end">
                <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(data)" />
                <Button icon="pi pi-trash" text size="small" severity="danger" @click="removeExpense(data)" />
              </div>
            </template>
          </Column>
        </DataTable>
      </div>

      <!-- gráfico configurable, a ancho completo -->
      <div v-else class="bg-white rounded-xl border border-slate-200 p-4 sm:p-5">
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
          <template v-if="excludedCategories.length">
            · sin {{ excludedCategories.join(', ') }}
          </template>
        </p>
      </div>
    </div>

    <ExpenseFormDialog v-model:visible="showForm" :trip="trip" :expense="editing" />
    <ExpenseImportDialog v-model:visible="showImport" :trip="trip" />
  </div>
</template>
